// -----------------------------
// Payment Terms + Grace Days
// -----------------------------
// Always set payment terms from first item (unless manual override is checked)
function force_set_payment_terms_template(frm) {
    if (frm.doc.docstatus !== 0) {
        console.log("Document is submitted. Skipping payment terms/grace-days auto-set.");
        return;
    }

    const firstItem = frm.doc.items && frm.doc.items[0];
    if (!(firstItem && firstItem.item_code)) return;

    frappe.db.get_doc('Item', firstItem.item_code).then(itemDoc => {
        if (!itemDoc.item_group) return;

        frappe.db.get_doc('Item Group', itemDoc.item_group).then(groupDoc => {
            const template  = groupDoc.custom_payment_terms_template;
            const graceDays = groupDoc.custom_grace_days;

            // Set Payment Terms Template (respect manual override & returns)
            if (template) {
                if (!frm.doc.custom_manual_payment_terms && !frm.doc.is_return) {
                    console.log("Auto-setting Payment Terms Template:", template);
                    frm.set_value('payment_terms_template', template);
                } else {
                    console.log("Manual override enabled or is_return — not setting template.");
                }
            }

            // Set Grace Days (independent of manual_payment_terms)
            if (graceDays !== undefined && graceDays !== null) {
                console.log("Auto-setting custom_grace_days:", graceDays);
                frm.set_value('custom_grace_days', graceDays); // will trigger overdue check via handler
            } else {
                // If Item Group has no value, clear on SI
                frm.set_value('custom_grace_days', null);
            }
        });
    });
}

// ----------------------------------
// Overdue Check (with Grace Days)
// ----------------------------------

// Robust readiness & visibility check for dashboard
function waitForDashboardVisible(frm, cb, tries = 0) {
    const MAX_TRIES = 20; // ~1s max (20 * 50ms)
    const next = () => waitForDashboardVisible(frm, cb, tries + 1);

    if (!frm.dashboard || !frm.dashboard.wrapper) {
        return setTimeout(next, 50);
    }

    try {
        // Make sure the dashboard is not hidden
        frm.dashboard.show && frm.dashboard.show();
        // Remove common hidden classes if present
        const $w = $(frm.dashboard.wrapper);
        $w.removeClass('hidden d-none').css('display', ''); // clear inline display:none
        $w.closest('.form-dashboard').removeClass('hidden d-none');
    } catch (e) { /* noop */ }

    // Ensure wrapper is in DOM and visible
    const el = frm.dashboard.wrapper && frm.dashboard.wrapper[0];
    const isVisible = el && document.body.contains(el) && el.offsetParent !== null;

    if (!isVisible && tries < MAX_TRIES) {
        return setTimeout(next, 50);
    }

    // After AJAX (render cycle) then run callback
    frappe.after_ajax(() => cb());
}

function setHeadlineOnce(frm, text, color) {
    // Cache to avoid repainting same headline
    if (frm._overdue_headline_text === text && frm._overdue_headline_color === color) {
        return;
    }
    waitForDashboardVisible(frm, () => {
        frm.dashboard.set_headline_alert(text, color);
        frm._overdue_headline_text  = text;
        frm._overdue_headline_color = color;
    });
}

function getGraceDays(frm) {
    const n = parseInt(frm.doc.custom_grace_days, 10);
    return Number.isFinite(n) && n > 0 ? n : 0;
}

function parseGrace(n) {
    const v = parseInt(n, 10);
    return Number.isFinite(v) && v > 0 ? v : 0;
}

// --- msgprint dedupe: avoid duplicate popups on new form load ---
function shouldShowOverduePopup(frm, customer, invoiceNames) {
    const key = `${customer}|${invoiceNames.sort().join(',')}`;
    if (frm._overdue_last_popup_key === key) return false;
    frm._overdue_last_popup_key = key;
    return true;
}

function fetchOverdue(frm, source) {
    const customer = frm.doc.customer;
    if (!customer) {
        setHeadlineOnce(frm, "No customer selected.", "orange");
        return;
    }

    const defaultGrace = getGraceDays(frm); // fallback if an older invoice has no custom_grace_days
    const today = frappe.datetime.get_today();

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Sales Invoice",
            filters: [
                ["customer", "=", customer],
                ["docstatus", "=", 1],
                ["outstanding_amount", ">", 0],
                ["due_date", "<", today]
            ],
            fields: ["name", "due_date", "outstanding_amount", "custom_grace_days"] // per-invoice grace
        },
        callback: function(r) {
            const rows = Array.isArray(r.message) ? r.message : [];

            const beyondGrace = [];
            const withinGrace = [];

            rows.forEach(inv => {
                const invGrace  = parseGrace(inv.custom_grace_days) || defaultGrace; // prefer the invoice's own grace
                const deadline  = frappe.datetime.add_days(inv.due_date, invGrace);
                const isBeyond  = frappe.datetime.get_diff(today, deadline) > 0; // today > (due + grace)
                const enriched  = Object.assign({}, inv, { invGrace, deadline });
                (isBeyond ? beyondGrace : withinGrace).push(enriched);
            });

            // --- Msgprint (only when customer changes), de-duplicated & per-invoice grace ---
            if (source === "customer" && rows.length) {
                const names = rows.map(x => x.name);
                if (shouldShowOverduePopup(frm, customer, names)) {
                    const html = rows.map(row => {
                        const invGrace  = parseGrace(row.custom_grace_days) || defaultGrace;
                        const deadline  = frappe.datetime.add_days(row.due_date, invGrace);
                        const dueStr    = frappe.datetime.str_to_user(row.due_date);
                        const graceStr  = invGrace ? `; Grace ${invGrace}d until ${frappe.datetime.str_to_user(deadline)}` : "";
                        return `<b>${row.name}</b>: ₹${row.outstanding_amount} (Due ${dueStr}${graceStr})`;
                    }).join("<br>");
                    frappe.msgprint(__("Customer has overdue invoices:") + "<br>" + html);
                }
            }

            // --- Dashboard headline + save gating ---
            const allowBlock = !frm.doc.custom_disable_overdue_check && !frm.doc.is_return;

            if (beyondGrace.length) {
                setHeadlineOnce(frm, `This Customer Has Overdue Invoices Beyond Grace (${beyondGrace.length})`, "red");
                if (allowBlock) frm.disable_save(); else frm.enable_save && frm.enable_save();
            } else if (withinGrace.length) {
                setHeadlineOnce(frm, `This Customer Has Overdue Invoices (Within Grace: ${withinGrace.length})`, "orange");
                frm.enable_save && frm.enable_save();
            } else {
                setHeadlineOnce(frm, "No overdue invoices for this customer.", "green");
                frm.enable_save && frm.enable_save();
            }
        }
    });
}

// Debounce ONLY for 'refresh' to avoid duplicate paints; call immediate for other triggers.
const fetchOverdueDebounced = frappe.utils.debounce(fetchOverdue, 400);

// -----------------------------
// Event Handlers
// -----------------------------
// Sales Invoice Item row events
frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const firstItem = frm.doc.items && frm.doc.items[0];

        if (firstItem && row.name === firstItem.name) {
            console.log("First item selected or changed.");
            force_set_payment_terms_template(frm);
        }
    },

    items_remove: function(frm) {
        // Delay ensures frm.doc.items is updated
        setTimeout(() => {
            const newFirst = frm.doc.items[0];
            if (!newFirst || !newFirst.item_code) {
                console.log("First item removed. Clearing Payment Terms Template and Grace Days.");
                frm.set_value('payment_terms_template', null);
                frm.set_value('custom_grace_days', null);
            } else {
                console.log("First item changed after delete. Updating Payment Terms Template and Grace Days.");
                force_set_payment_terms_template(frm);
            }
        }, 200);
    }
});

// Consolidated Sales Invoice events (single block to avoid duplicate triggers)
frappe.ui.form.on('Sales Invoice', {
    // Runs after the form is painted; good place to show headline on brand-new docs
    onload_post_render: function(frm) {
        fetchOverdue(frm, "onload_post_render"); // immediate
    },

    refresh: function(frm) {
        // Initial auto-set from first item (small delay lets child table render)
        setTimeout(() => {
            force_set_payment_terms_template(frm);
        }, 500);

        // Overdue check (debounced only on refresh)
        fetchOverdueDebounced(frm, "refresh");
    },

    customer: function(frm) {
        // Reset popup dedupe key when customer changes
        frm._overdue_last_popup_key = null;
        // Run immediately so the headline appears right after choosing the customer
        fetchOverdue(frm, "customer");
    },

    is_return: function(frm) {
        fetchOverdue(frm, "is_return"); // immediate
    },

    custom_disable_overdue_check: function(frm) {
        fetchOverdue(frm, "custom_disable_overdue_check"); // immediate
    },

    custom_grace_days: function(frm) {
        // Re-evaluate when grace days change (either manually or via Item Group auto-set)
        fetchOverdue(frm, "grace_change"); // immediate
    },

    manual_payment_terms: function(frm) {
        // Optional UX: enable/disable the field based on checkbox
        frm.toggle_enable('payment_terms_template', frm.doc.custom_manual_payment_terms);
    }
});

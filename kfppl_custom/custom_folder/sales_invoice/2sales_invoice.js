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
                frm.set_value('custom_grace_days', graceDays); // triggers our overdue check via field handler below
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
function setHeadlineOnce(frm, text, color) {
    if (frm._overdue_headline_text !== text || frm._overdue_headline_color !== color) {
        frm.dashboard.set_headline_alert(text, color);
        frm._overdue_headline_text  = text;
        frm._overdue_headline_color = color;
    }
}

function getGraceDays(frm) {
    const n = parseInt(frm.doc.custom_grace_days, 10);
    return Number.isFinite(n) && n > 0 ? n : 0;
}

function fetchOverdue(frm, source) {
    const customer = frm.doc.customer;
    if (!customer) {
        setHeadlineOnce(frm, "No customer selected.", "orange");
        return;
    }

    const grace = getGraceDays(frm);
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
            fields: ["name", "due_date", "outstanding_amount"]
        },
        callback: function(r) {
            const rows = Array.isArray(r.message) ? r.message : [];

            const beyondGrace = [];
            const withinGrace = [];

            rows.forEach(inv => {
                const deadline = frappe.datetime.add_days(inv.due_date, grace);
                const beyond = frappe.datetime.get_diff(today, deadline) > 0; // today > (due + grace)
                (beyond ? beyondGrace : withinGrace).push(inv);
            });

            // --- Msgprint behavior (only when customer changes), now showing grace info ---
            if (source === "customer" && rows.length) {
                const fmt = inv => {
                    const deadline = frappe.datetime.add_days(inv.due_date, grace);
                    return `<b>${inv.name}</b>: ₹${inv.outstanding_amount} (Due ${frappe.datetime.str_to_user(inv.due_date)}; Grace until ${frappe.datetime.str_to_user(deadline)})`;
                };
                let msg = __("Customer has overdue invoices:") + "<br>" + rows.map(fmt).join("<br>");
                frappe.msgprint(msg);
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

// Debounce to avoid repeated refresh calls painting multiple times
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
    refresh: function(frm) {
        // Initial auto-set from first item (small delay lets child table render)
        setTimeout(() => {
            force_set_payment_terms_template(frm);
        }, 500);

        // Overdue check
        fetchOverdueDebounced(frm, "refresh");
    },

    customer: function(frm) {
        fetchOverdueDebounced(frm, "customer");
    },

    is_return: function(frm) {
        fetchOverdueDebounced(frm, "is_return");
    },

    custom_disable_overdue_check: function(frm) {
        fetchOverdueDebounced(frm, "custom_disable_overdue_check");
    },

    custom_grace_days: function(frm) {
        // Re-evaluate when grace days change (either manually or via Item Group auto-set)
        fetchOverdueDebounced(frm, "grace_change");
    },

    manual_payment_terms: function(frm) {
        // Optional UX: enable/disable the field based on checkbox
        frm.toggle_enable('payment_terms_template', frm.doc.custom_manual_payment_terms);
    }
});

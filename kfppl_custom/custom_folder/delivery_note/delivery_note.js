frappe.ui.form.on("Delivery Note", {
    refresh: function(frm) {
        fetchOverdue(frm, "refresh");
    },
    customer: function(frm) {
        fetchOverdue(frm, "customer");
    }
});

function parseGrace(val) {
    const n = parseInt(val, 10);
    return Number.isFinite(n) && n > 0 ? n : 0;
}

function fetchOverdue(frm, source) {
    const customer = frm.doc.customer;
    if (!customer) return;

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Sales Invoice",
            filters: [
                ["customer", "=", customer],
                ["docstatus", "=", 1],
                ["outstanding_amount", ">", 0],
                ["due_date", "<", frappe.datetime.get_today()]
            ],
            // include per-invoice grace
            fields: ["name", "due_date", "outstanding_amount", "custom_grace_days"]
        },
        callback: function(r) {
            const rows = Array.isArray(r.message) ? r.message : [];

            if (rows.length) {
                // --- keep your existing popup unchanged (no grace shown there) ---
                if (source === "customer") {
                    frappe.msgprint(
                        __("Customer has overdue invoices:") + "<br>" +
                        rows.map(inv =>
                            `<b>${inv.name}</b>: ₹${inv.outstanding_amount} (Due on ${frappe.datetime.str_to_user(inv.due_date)})`
                        ).join("<br>")
                    );
                }

                // --- compute beyond-grace for gating only ---
                const today = frappe.datetime.get_today();
                const beyondGraceCount = rows.reduce((cnt, inv) => {
                    const g = parseGrace(inv.custom_grace_days); // per-invoice grace (fallback 0)
                    const deadline = frappe.datetime.add_days(inv.due_date, g);
                    // today > (due + grace) ?
                    return cnt + (frappe.datetime.get_diff(today, deadline) > 0 ? 1 : 0);
                }, 0);

                if (source === "refresh") {
                    frm.dashboard.set_headline_alert("This Customer Has Overdue Invoices", "red");
                    // Block save ONLY if any invoice is beyond its grace
                    if (beyondGraceCount > 0 && !frm.doc.custom_disable_overdue_check) {
                        frm.disable_save();
                    } else {
                        frm.enable_save && frm.enable_save();
                    }
                }
            } else {
                // no overdue invoices
                // optional: you can clear headline or enable save here if you want
                frm.enable_save && frm.enable_save();
            }
        }
    });
}

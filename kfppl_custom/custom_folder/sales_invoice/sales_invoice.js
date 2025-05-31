// Always set payment terms from first item (unless manual override is checked)
function force_set_payment_terms_template(frm) {

    if (frm.doc.docstatus !== 0) {
        console.log("Document is submitted. Skipping payment terms auto-set.");
        return;
    }
    const firstItem = frm.doc.items && frm.doc.items[0];

    if (firstItem && firstItem.item_code) {
        frappe.db.get_doc('Item', firstItem.item_code).then(itemDoc => {
            if (itemDoc.item_group) {
                frappe.db.get_doc('Item Group', itemDoc.item_group).then(groupDoc => {
                    const template = groupDoc.custom_payment_terms_template;
                    if (template) {
                        if (!frm.doc.custom_manual_payment_terms) {
                            console.log("Auto-setting Payment Terms Template:", template);
                            frm.set_value('payment_terms_template', template);
                        } else {
                            console.log("Manual override enabled — not setting template.");
                        }
                    }
                });
            }
        });
    }
}

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
                console.log("First item removed. Clearing Payment Terms Template.");
                frm.set_value('payment_terms_template', null);
            } else {
                console.log("First item changed after delete. Updating Payment Terms Template.");
                force_set_payment_terms_template(frm);
            }
        }, 200);
    }
});

frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        setTimeout(() => {
            force_set_payment_terms_template(frm);
        }, 500);
    },

    manual_payment_terms: function(frm) {
        // Optional UX: enable/disable the field based on checkbox
        frm.toggle_enable('payment_terms_template', frm.doc.custom_manual_payment_terms);
    }
});


frappe.ui.form.on("Sales Invoice", {
    customer: function(frm) {
        fetchOverdue(frm, "customer");
    }
});

frappe.ui.form.on("Sales Invoice", {
    refresh: function(frm) {
        fetchOverdue(frm, "refresh");
    }
});



function fetchOverdue(frm, source) {
    let customer = frm.doc.customer;
    if (!customer) return;

    console.log("The customer name is:");
    console.log(customer);

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
            fields: ["name", "due_date", "outstanding_amount"]
        },
        callback: function(r) {
            if (r.message?.length) {
                if ( source === "customer") {
                    frappe.msgprint(__("Customer has overdue invoices:") + "<br>" +
                        r.message.map(inv =>
                            `<b>${inv.name}</b>: ₹${inv.outstanding_amount} (Due on ${frappe.datetime.str_to_user(inv.due_date)})`
                        ).join("<br>")
                    );
                    
                }
                if ( source === "refresh") {
                    frm.dashboard.set_headline_alert("This Customer Has Overdue Invoices", "red")
                     if (!frm.doc.custom_disable_overdue_check && !frm.doc.is_return) {
                    frm.disable_save();
                     }
                }
            } else {
                console.log("No overdue invoices for this customer.");
            }
        }
    });
}

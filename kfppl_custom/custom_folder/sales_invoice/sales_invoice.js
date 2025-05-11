// Forcefully set payment terms (used on item_code change)
function force_set_payment_terms_template(frm) {
    const firstItem = frm.doc.items && frm.doc.items[0];

    if (firstItem && firstItem.item_code) {
        frappe.db.get_doc('Item', firstItem.item_code).then(itemDoc => {
            if (itemDoc.item_group) {
                frappe.db.get_doc('Item Group', itemDoc.item_group).then(groupDoc => {
                    const template = groupDoc.custom_payment_terms_template;

                    if (template) {
                        console.log("Force setting Payment Terms Template to:", template);
                        frm.set_value('payment_terms_template', template);
                    }
                });
            }
        });
    }
}

// Set only if not already set (used on form refresh)
function safe_set_payment_terms_template(frm) {
    if (!frm.doc.payment_terms_template && frm.doc.items && frm.doc.items.length) {
        const firstItem = frm.doc.items[0];

        if (firstItem.item_code) {
            frappe.db.get_doc('Item', firstItem.item_code).then(itemDoc => {
                if (itemDoc.item_group) {
                    frappe.db.get_doc('Item Group', itemDoc.item_group).then(groupDoc => {
                        const template = groupDoc.custom_payment_terms_template;

                        if (template) {
                            console.log("Safely setting Payment Terms Template to:", template);
                            frm.set_value('payment_terms_template', template);
                        }
                    });
                }
            });
        }
    }
}









frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const firstItem = frm.doc.items && frm.doc.items[0];

        if (firstItem && row.name === firstItem.name) {
            console.log("First item changed:", row.item_code);
            force_set_payment_terms_template(frm);
        }
    }
});

frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        setTimeout(() => {
            safe_set_payment_terms_template(frm);
        }, 500);
    },

    items_remove: function(frm, cdt, cdn) {
        const removed_row = locals[cdt][cdn];
        const was_first_row = removed_row.name === frm.doc.items[0]?.name;

        if (was_first_row || frm.doc.items.length === 0) {
            console.log("First item removed. Clearing Payment Terms Template.");
            frm.set_value('payment_terms_template', null);
        }
    }
});

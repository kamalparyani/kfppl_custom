frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Always run logic if this is the first item
        if (row.idx === 1 && row.item_code) {
            frappe.db.get_doc('Item', row.item_code).then(itemDoc => {
                if (itemDoc.item_group) {
                    frappe.db.get_doc('Item Group', itemDoc.item_group).then(groupDoc => {
                        if (groupDoc.payment_terms_template) {
                            frm.set_value('payment_terms_template', groupDoc.payment_terms_template);
                        }
                    });
                }
            });
        }
    }
});

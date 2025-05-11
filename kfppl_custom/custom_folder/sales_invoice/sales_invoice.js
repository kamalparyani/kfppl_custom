function set_payment_terms_from_first_item(frm) {
    const firstItem = frm.doc.items && frm.doc.items[0];

    if (firstItem && firstItem.item_code) {
        frappe.db.get_doc('Item', firstItem.item_code).then(itemDoc => {
            if (itemDoc.item_group) {
                frappe.db.get_doc('Item Group', itemDoc.item_group).then(groupDoc => {
                    const template = groupDoc.custom_payment_terms_template;
                    console.log("Item Group:", itemDoc.item_group);
                    console.log("Payment Terms Template:", template);

                    if (template) {
                        frm.set_value('payment_terms_template', template);
                    }
                }).catch(err => {
                    console.error("Error fetching Item Group:", err);
                });
            }
        }).catch(err => {
            console.error("Error fetching Item:", err);
        });
    }
}

// Trigger when item_code is manually changed in the first row
frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const firstItem = frm.doc.items && frm.doc.items[0];

        if (firstItem && row.name === firstItem.name) {
            console.log("First item changed:", row.item_code);
            set_payment_terms_from_first_item(frm);
        } else {
            console.log("Not the first item, skipping");
        }
    }
});

// Trigger after pulling items from Sales Order / Delivery Note
frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        setTimeout(() => {
            set_payment_terms_from_first_item(frm);
        }, 500);
    }
});


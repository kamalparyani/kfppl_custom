frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const firstItem = frm.doc.items && frm.doc.items[0];

        if (firstItem && row.name === firstItem.name && row.item_code) {
            console.log("First item changed:", row.item_code);

            frappe.db.get_doc('Item', row.item_code).then(itemDoc => {
                console.log("Item Group:", itemDoc.item_group);

                if (itemDoc.item_group) {
                    frappe.db.get_doc('Item Group', itemDoc.item_group).then(groupDoc => {
                        console.log("Payment Terms Template:", groupDoc.custom_payment_terms_template);
                    }).catch(err => {
                        console.error("Error fetching Item Group:", err);
                    });
                }
            }).catch(err => {
                console.error("Error fetching Item:", err);
            });
        } else {
            console.log("Not the first item, skipping");
        }
    }
});


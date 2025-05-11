function log_payment_terms_from_first_item(frm) {
    const firstItem = frm.doc.items && frm.doc.items[0];

    if (firstItem && firstItem.item_code) {
        frappe.db.get_doc('Item', firstItem.item_code).then(itemDoc => {
            if (itemDoc.item_group) {
                frappe.db.get_doc('Item Group', itemDoc.item_group).then(groupDoc => {
                    console.log("Item Group:", itemDoc.item_group);
                    console.log("Payment Terms Template:", groupDoc.custom_payment_terms_template);
                }).catch(err => {
                    console.error("Error fetching Item Group:", err);
                });
            }
        }).catch(err => {
            console.error("Error fetching Item:", err);
        });
    }
}

frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const firstItem = frm.doc.items && frm.doc.items[0];

        if (firstItem && row.name === firstItem.name) {
            console.log("First item changed:", row.item_code);
            log_payment_terms_from_first_item(frm);
        } else {
            console.log("Not the first item, skipping");
        }
    }
});

// Trigger after Delivery Note pull
frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        setTimeout(() => {
            log_payment_terms_from_first_item(frm);
        }, 500);
    }
});

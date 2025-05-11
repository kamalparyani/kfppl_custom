frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const firstItem = frm.doc.items && frm.doc.items[0];

        if (firstItem && row.name === firstItem.name && row.item_code) {
            console.log("First item changed:", row.item_code);

            frappe.db.get_doc('Item', row.item_code).then(itemDoc => {
                console.log("Item Group:", itemDoc.item_group);
            }).catch(err => {
                console.error("Failed to fetch Item doc:", err);
            });
        } else {
            console.log("Not the first item, skipping");
        }
    }
});

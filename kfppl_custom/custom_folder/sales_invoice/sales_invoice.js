frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        // frm: the parent form (Sales Invoice)
        // cdt: child DocType ("Sales Invoice Item")
        // cdn: child document name (like "b28f23e37a")
        
        let row = locals[cdt][cdn]; // access the current child row
        console.log(row.item_code); // this is the changed value
    }
});
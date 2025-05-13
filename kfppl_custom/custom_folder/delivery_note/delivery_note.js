frappe.ui.form.on("Delivery Note", {
    refresh: function(frm) {
        fetchOverdue(frm, "refresh");
    }
});

frappe.ui.form.on("Delivery Note", {
    customer: function(frm) {
        fetchOverdue(frm, "customer");
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
                 if (source === "customer") {
                    frappe.msgprint(__("Customer has overdue invoices:") + "<br>" +
                        r.message.map(inv =>
                            `<b>${inv.name}</b>: ₹${inv.outstanding_amount} (Due on ${frappe.datetime.str_to_user(inv.due_date)})`
                        ).join("<br>")
                    );
                    
                }
                if ( source === "refresh") {
                    frm.dashboard.set_headline_alert("This Customer Has Overdue Invoices", "red");
                    frm.disable_save();
                }
            } else {
                console.log("No overdue invoices for this customer.");
            }
        }
    });
}

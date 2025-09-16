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
                    const graceDays = groupDoc.custom_grace_days;
                    if (template) {
                       
                        if (!frm.doc.custom_manual_payment_terms && !frm.doc.is_return) {
                            console.log("Auto-setting Payment Terms Template:", template);
                            frm.set_value('payment_terms_template', template);
                        } else {
                            console.log("Manual override enabled or is_return — not setting template.");
                        }
                        
                    }
                    if (graceDays !== undefined && graceDays !== null) {
                        console.log("Auto-setting custom_grace_days:", graceDays);
                        frm.set_value('custom_grace_days', graceDays);
                    } else {
                        // Optional: clear if Item Group has no value
                        frm.set_value('custom_grace_days', null);
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
                frm.set_value('custom_grace_days', null);
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

frappe.ui.form.on("Sales Invoice", {
    is_return: function(frm) {
        fetchOverdue(frm, "refresh");
    }
});

frappe.ui.form.on("Sales Invoice", {
    custom_disable_overdue_check: function(frm) {
        fetchOverdue(frm, "refresh");
    }
});

// function fetchOverdue(frm, source) {
//     let customer = frm.doc.customer;
//     if (!customer) return;

//     console.log("The customer name is:");
//     console.log(customer);

//     frappe.call({
//         method: "frappe.client.get_list",
//         args: {
//             doctype: "Sales Invoice",
//             filters: [
//                 ["customer", "=", customer],
//                 ["docstatus", "=", 1],
//                 ["outstanding_amount", ">", 0],
//                 ["due_date", "<", frappe.datetime.get_today()]
//             ],
//             fields: ["name", "due_date", "outstanding_amount"]
//         },
//         callback: function(r) {
//             if (r.message?.length) {
//                 if ( source === "customer") {
//                     frappe.msgprint(__("Customer has overdue invoices:") + "<br>" +
//                         r.message.map(inv =>
//                             `<b>${inv.name}</b>: ₹${inv.outstanding_amount} (Due on ${frappe.datetime.str_to_user(inv.due_date)})`
//                         ).join("<br>")
//                     );
                    
//                 }
//                 if ( source === "refresh") {
//                     frm.dashboard.set_headline_alert("This Customer Has Overdue Invoices", "red")
//                      if (!frm.doc.custom_disable_overdue_check && !frm.doc.is_return) {
//                     frm.disable_save();
//                      }
//                 }
//                 if ( source === "is_return" ) {
//                     frm.dashboard.set_headline_alert("This Customer Has Overdue Invoices", "red")
//                     if (!frm.doc.custom_disable_overdue_check && !frm.doc.is_return) {
//                    frm.disable_save();
//                    }
//                 }
//                 if ( source === "custom_disable_overdue_check" ) {
//                     frm.dashboard.set_headline_alert("This Customer Has Overdue Invoices", "red")
//                     if (!frm.doc.custom_disable_overdue_check && !frm.doc.is_return) {
//                    frm.disable_save();
//                    }
//                 }


//             } else {
//                 console.log("No overdue invoices for this customer.");
//             }
//         }
//     });
// }

function getGraceDays(frm) {
    const n = parseInt(frm.doc.custom_grace_days, 10);
    return Number.isFinite(n) && n > 0 ? n : 0;
}

function fetchOverdue(frm, source) {
    const customer = frm.doc.customer;
    if (!customer) return;

    const grace = getGraceDays(frm);
    const today = frappe.datetime.get_today();

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Sales Invoice",
            filters: [
                ["customer", "=", customer],
                ["docstatus", "=", 1],
                ["outstanding_amount", ">", 0],
                ["due_date", "<", today]
            ],
            fields: ["name", "due_date", "outstanding_amount"]
        },
        callback: function(r) {
            const rows = Array.isArray(r.message) ? r.message : [];

            const beyondGrace = [];
            const withinGrace = [];

            rows.forEach(inv => {
                const deadline = frappe.datetime.add_days(inv.due_date, grace);
                if (frappe.datetime.get_diff(today, deadline) > 0) {
                    beyondGrace.push(inv);
                } else {
                    withinGrace.push(inv);
                }
            });

            // --- Msgprint behavior (only on customer change, like before) ---
            if (source === "customer" && rows.length) {
                const fmt = inv => {
                    const deadline = frappe.datetime.add_days(inv.due_date, grace);
                    return `<b>${inv.name}</b>: ₹${inv.outstanding_amount} 
                            (Due ${frappe.datetime.str_to_user(inv.due_date)}; 
                            Grace until ${frappe.datetime.str_to_user(deadline)})`;
                };

                let msg = __("Customer has overdue invoices:") + "<br>";
                msg += rows.map(fmt).join("<br>");
                frappe.msgprint(msg);
            }

            // --- Dashboard headline + save gating ---
            if (beyondGrace.length) {
                frm.dashboard.set_headline_alert(
                    `This Customer Has Overdue Invoices Beyond Grace (${beyondGrace.length})`,
                    "red"
                );
                if (!frm.doc.custom_disable_overdue_check && !frm.doc.is_return) {
                    frm.disable_save();
                } else {
                    frm.enable_save && frm.enable_save();
                }
            } else if (withinGrace.length) {
                frm.dashboard.set_headline_alert(
                    `This Customer Has Overdue Invoices (Within Grace: ${withinGrace.length})`,
                    "orange"
                );
                frm.enable_save && frm.enable_save();
            } else {
                frm.dashboard.set_headline_alert("No overdue invoices for this customer.", "green");
                frm.enable_save && frm.enable_save();
            }
        }
    });
}

// Re-check on grace_days change
frappe.ui.form.on("Sales Invoice", {
    custom_grace_days: function(frm) {
        fetchOverdue(frm, "grace_change");
    },
    customer: function(frm) {
        fetchOverdue(frm, "customer");
    },
    refresh: function(frm) {
        fetchOverdue(frm, "refresh");
    },
    is_return: function(frm) {
        fetchOverdue(frm, "is_return");
    },
    custom_disable_overdue_check: function(frm) {
        fetchOverdue(frm, "custom_disable_overdue_check");
    }
});

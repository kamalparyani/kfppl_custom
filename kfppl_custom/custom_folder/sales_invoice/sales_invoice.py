import frappe

def set_payment_terms_template(doc, method):
    # Only set if the field is currently empty and items exist
    if not doc.payment_terms_template and doc.items and doc.items[0].item_code:
        first_item = doc.items[0]
        item = frappe.get_doc("Item", first_item.item_code)

        if item.item_group:
            item_group = frappe.get_doc("Item Group", item.item_group)
            template = item_group.get("custom_payment_terms_template")
            if template:
                doc.payment_terms_template = template

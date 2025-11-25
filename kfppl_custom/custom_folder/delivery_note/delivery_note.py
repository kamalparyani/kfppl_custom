import frappe
from frappe.utils import flt

def before_submit(doc, method):
    """
    Enforce customer credit limit at Delivery Note submit.

    Uses the standard ERPNext credit limit logic (check_credit_limit),
    and adds this DN's amount as `extra_amount` so that creating this
    DN cannot push the customer over limit.
    """

    # Allow returns to go through (optional – remove if you want to block returns too)
    if getattr(doc, "is_return", 0):
        return

    # Import the standard credit limit checker from ERPNext
    from erpnext.selling.doctype.customer.customer import check_credit_limit

    customer = doc.customer
    company = doc.company

    # If no customer (edge case), do nothing
    if not customer or not company:
        return

    # Same flag that Sales Invoice uses: "Bypass credit limit check at Sales Order"
    bypass_credit_limit_check_at_sales_order = frappe.db.get_value(
        "Customer Credit Limit",
        filters={
            "parent": customer,
            "parenttype": "Customer",
            "company": company,
        },
        fieldname="bypass_credit_limit_check",
    )

    # In check_credit_limit signature this is called ignore_outstanding_sales_order
    ignore_outstanding_sales_order = bool(bypass_credit_limit_check_at_sales_order)

    # Amount of this Delivery Note (base currency)
    extra_amount = flt(doc.base_grand_total) or 0

    # This will raise an exception if credit limit is breached
    check_credit_limit(
        customer,
        company,
        ignore_outstanding_sales_order=ignore_outstanding_sales_order,
        extra_amount=extra_amount,
    )

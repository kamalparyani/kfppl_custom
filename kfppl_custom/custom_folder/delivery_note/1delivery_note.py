import frappe
from frappe import _
from erpnext.accounts.party import get_party_outstanding

def before_submit(doc, method):
    validate_credit_limit_on_delivery_note(doc)

def validate_credit_limit_on_delivery_note(doc):
    customer = doc.customer
    company = doc.company

    # get credit limit
    credit_limit = get_credit_limit(customer, company)
    if not credit_limit:
        return

    outstanding = get_party_outstanding(
        party_type="Customer",
        party=customer,
        company=company,
        ignore_outstanding_sales_order=1,
        ignore_outstanding_purchase_invoice=1,
    )

    dn_amount = doc.base_grand_total or 0
    projected = outstanding + dn_amount

    if projected > credit_limit:
        frappe.throw(
            _(
                "Credit Limit Exceeded.<br>"
                "Credit Limit: {0}<br>"
                "Outstanding: {1}<br>"
                "DN Amount: {2}<br>"
                "Projected Outstanding: {3}"
            ).format(
                credit_limit, outstanding, dn_amount, projected
            )
        )

def get_credit_limit(customer, company):
    cust = frappe.get_doc("Customer", customer)

    # Company-wise
    for row in cust.credit_limits:
        if row.company == company and row.credit_limit:
            return row.credit_limit

    # Global credit limit
    return cust.credit_limit or 0

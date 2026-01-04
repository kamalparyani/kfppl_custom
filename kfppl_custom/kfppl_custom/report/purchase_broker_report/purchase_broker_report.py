# Copyright (c) 2026, V12 Infotech and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe import _

def execute(filters=None):
    filters = filters or {}
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
        {
            "label": _("Purchase Partner"),
            "fieldname": "custom_purchase_partner",
            "fieldtype": "Link",
            "options": "Purchase Partner",
            "width": 180
        },
        {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 180},
        {"label": _("Purchase Invoice"), "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 170},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 110},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
    ]


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("pi.posting_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("pi.posting_date <= %(to_date)s")

    if filters.get("supplier"):
        conditions.append("pi.supplier = %(supplier)s")

    if filters.get("item_code"):
        conditions.append("pii.item_code = %(item_code)s")

    if filters.get("custom_purchase_partner"):
        conditions.append("pi.custom_purchase_partner = %(custom_purchase_partner)s")

    return (" AND " + " AND ".join(conditions)) if conditions else ""


def get_data(filters):
    conditions = get_conditions(filters)

    return frappe.db.sql(f"""
        SELECT
            pi.posting_date,
            pi.custom_purchase_partner,
            pi.supplier,
            pi.name AS purchase_invoice,
            pii.item_code,
            pii.item_name,
            pii.qty,
            pii.rate,
            pii.amount
        FROM `tabPurchase Invoice` pi
        INNER JOIN `tabPurchase Invoice Item` pii
            ON pii.parent = pi.name
        WHERE
            pi.docstatus = 1
            {conditions}
        ORDER BY pi.posting_date DESC, pi.name DESC
    """, filters, as_dict=True)

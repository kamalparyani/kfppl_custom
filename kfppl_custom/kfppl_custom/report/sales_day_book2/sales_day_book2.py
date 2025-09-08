# # Copyright (c) 2025, V12 Infotech and contributors
# # For license information, please see license.txt

# # import frappe

def execute(filters=None):
    pass

# import frappe
# from collections import defaultdict

# def execute(filters=None):
#     filters = frappe._dict(filters or {})
#     f_from_date = filters.get("from_date")
#     f_to_date = filters.get("to_date")

#     # -------- columns (query report format)
#     columns = [
#         {"label": "Voucher Date",  "fieldname": "voucher_date", "fieldtype": "Date",   "width": 110},
#         {"label": "Voucher No",    "fieldname": "voucher_no",   "fieldtype": "Link",   "options": "Sales Invoice", "width": 160},
#         {"label": "Particular",    "fieldname": "particular",   "fieldtype": "Data",   "width": 260},
#         {"label": "Qty",           "fieldname": "qty",          "fieldtype": "Float",  "width": 90},
#         {"label": "UOM",           "fieldname": "uom",          "fieldtype": "Link",   "options": "UOM", "width": 90},
#         {"label": "Rate",          "fieldname": "rate",         "fieldtype": "Currency", "width": 110},
#         {"label": "Amount",        "fieldname": "amount",       "fieldtype": "Currency", "width": 120},
#         {"label": "Debit Amount",  "fieldname": "debit",        "fieldtype": "Currency", "width": 120},
#         {"label": "Credit Amount", "fieldname": "credit",       "fieldtype": "Currency", "width": 120},
#     ]

#     # -------- WHERE + params
#     where = [
#         "gle.is_cancelled = 0",
#         "gle.voucher_type = 'Sales Invoice'",
#         "IFNULL(si.is_opening, 'No') = 'No'"  # exclude opening SI
#     ]
#     params = {}
#     if f_from_date:
#         where.append("gle.posting_date >= %(from_date)s")
#         params["from_date"] = f_from_date
#     if f_to_date:
#         where.append("gle.posting_date <= %(to_date)s")
#         params["to_date"] = f_to_date

#     # -------- Base GL query (order using SI's date+time; GL has no posting_time)
#     base_sql = f"""
#         SELECT
#             gle.posting_date AS voucher_date,
#             CASE WHEN IFNULL(gle.party, '') = '' THEN gle.account ELSE gle.party END AS particular,
#             gle.voucher_no,
#             gle.debit,
#             gle.credit
#         FROM `tabGL Entry` gle
#         INNER JOIN `tabSales Invoice` si ON si.name = gle.voucher_no
#         WHERE {" AND ".join(where)}
#         ORDER BY
#             si.posting_date,
#             COALESCE(si.posting_time, TIME(si.creation)),
#             gle.voucher_no,
#             gle.name
#     """
#     gl_rows = frappe.db.sql(base_sql, params, as_dict=True)

#     if not gl_rows:
#         return columns, []

#     # -------- keep voucher order as produced by SQL
#     voucher_order = []
#     seen_v = set()
#     for r in gl_rows:
#         v = r["voucher_no"]
#         if v and v not in seen_v:
#             seen_v.add(v)
#             voucher_order.append(v)

#     # -------- group GL rows by voucher
#     gl_by_voucher = defaultdict(list)
#     for r in gl_rows:
#         gl_by_voucher[r["voucher_no"]].append(r)

#     # -------- bulk fetch SI Items (also exclude opening)
#     items_by_parent = defaultdict(list)
#     if voucher_order:
#         item_sql = """
#             SELECT
#                 sii.parent,
#                 sii.item_code,
#                 sii.item_name,
#                 sii.qty,
#                 sii.uom,
#                 sii.rate,
#                 sii.amount
#             FROM `tabSales Invoice Item` sii
#             INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
#             WHERE sii.parent IN %(parents)s
#               AND IFNULL(si.is_opening, 'No') = 'No'
#             ORDER BY sii.parent, sii.idx
#         """
#         item_rows = frappe.db.sql(item_sql, {"parents": tuple(voucher_order)}, as_dict=True)
#         for it in item_rows:
#             items_by_parent[it["parent"]].append(it)

#     # -------- build data with required intra-voucher ordering:
#     # debit GL lines -> credit GL lines -> items
#     data = []

#     for vno in voucher_order:
#         rows = gl_by_voucher[vno]

#         debit_rows  = [r for r in rows if (r.get("debit") or 0) > 0]
#         credit_rows = [r for r in rows if (r.get("debit") or 0) <= 0]  # includes pure credit or zero
#         ordered_gl  = debit_rows + credit_rows

#         # emit GL lines (date & voucher shown only on first row of the voucher)
#         for idx_in_v, r in enumerate(ordered_gl):
#             first = (idx_in_v == 0)
#             data.append({
#                 "voucher_date": r["voucher_date"] if first else None,
#                 "voucher_no":   vno if first else None,
#                 "particular":   r["particular"],
#                 "qty":          None,
#                 "uom":          None,
#                 "rate":         None,
#                 "amount":       None,
#                 "debit":        r.get("debit") or 0,
#                 "credit":       r.get("credit") or 0,
#             })

#         # items LAST
#         for it in items_by_parent.get(vno, []):
#             data.append({
#                 "voucher_date": None,
#                 "voucher_no":   None,
#                 "particular":   it.get("item_code") or it.get("item_name") or "",
#                 "qty":          it.get("qty"),
#                 "uom":          it.get("uom"),
#                 "rate":         it.get("rate"),
#                 "amount":       it.get("amount"),
#                 "debit":        0,
#                 "credit":       0,
#             })

#     return columns, data , None , None , None

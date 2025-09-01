# Copyright (c) 2025, V12 Infotech and contributors
# For license information, please see license.txt

# import frappe


# reports/sales_day_book/sales_day_book.py
import frappe
from frappe import _
from collections import defaultdict

def execute(filters=None):
    filters = filters or {}
    f_from_date = filters.get("from_date")
    f_to_date = filters.get("to_date")

    # ---- CSS (print & page breaks)
    margin_css = """
    <style>
    @page {
        size: A4;
        margin: 10mm; /* adjust as needed */
    }
    .page-break { page-break-after: always; }
    table { border-collapse: collapse; width: 100%; font-size: 11px; }
    th, td { border: 1px solid #ddd; padding: 6px; }
    th { text-align: center; }
    td.num { text-align: right; }
    </style>
    """

    # ---- Build base query safely (GL for Sales Invoice)
    where = ["gle.is_cancelled = 0", "gle.voucher_type = 'Sales Invoice'"]
    params = {}

    if f_from_date:
        where.append("gle.posting_date >= %(from_date)s")
        params["from_date"] = f_from_date
    if f_to_date:
        where.append("gle.posting_date <= %(to_date)s")
        params["to_date"] = f_to_date

    base_sql = f"""
        SELECT
            gle.posting_date AS voucher_date,
            CASE WHEN IFNULL(gle.party, '') = '' THEN gle.account ELSE gle.party END AS particular,
            gle.voucher_type,
            gle.voucher_no,
            gle.debit,
            gle.credit
        FROM `tabGL Entry` gle
        WHERE {" AND ".join(where)}
        ORDER BY gle.posting_date, gle.voucher_no
    """

    gl_rows = frappe.db.sql(base_sql, params, as_dict=True)

    if not gl_rows:
        html = margin_css + "<p><b>No data for the selected period.</b></p>"
        return None, None, html, None, None

    # ---- Collect distinct voucher_nos and bulk-fetch items
    voucher_nos = tuple(sorted({r["voucher_no"] for r in gl_rows if r.get("voucher_no")}))
    items_by_parent = defaultdict(list)

    if voucher_nos:
        # Single bulk query for all items
        item_sql = """
            SELECT parent, item_code, item_name, qty, uom, rate, amount
            FROM `tabSales Invoice Item`
            WHERE parent IN %(parents)s
            ORDER BY parent, idx
        """
        item_rows = frappe.db.sql(item_sql, {"parents": voucher_nos}, as_dict=True)
        for it in item_rows:
            items_by_parent[it["parent"]].append(it)

    # ---- Build display rows (first occurrence shows header cells; repeats blank voucher/ date)
    display_rows = []
    seen = set()
    total_debit = 0.0
    total_credit = 0.0

    for r in gl_rows:
        vno = r["voucher_no"]
        first = vno not in seen
        seen.add(vno)

        display_rows.append({
            "voucher_date": r["voucher_date"] if first else "",
            "voucher_no": vno if first else "",
            "particular": r["particular"],
            "qty": None,
            "uom": None,
            "rate": None,
            "amount": None,
            "debit": r["debit"] or 0,
            "credit": r["credit"] or 0,
        })
        total_debit += (r["debit"] or 0)
        total_credit += (r["credit"] or 0)

        # After last GL line for a voucher? We don't know that cheaply here,
        # so simply append the SI items right after the *first* line for that voucher.
        if first:
            for it in items_by_parent.get(vno, []):
                display_rows.append({
                    "voucher_date": "",
                    "voucher_no": "",
                    "particular": it.get("item_code") or it.get("item_name") or "",
                    "qty": it.get("qty"),
                    "uom": it.get("uom"),
                    "rate": it.get("rate"),
                    "amount": it.get("amount"),
                    "debit": 0,
                    "credit": 0,
                })

    # ---- Pagination for print: break every N lines
    ROWS_PER_PAGE = 40
    def render_table_head():
        return """
        <table>
            <tr>
                <th>Voucher Date</th>
                <th>Voucher No</th>
                <th>Particular</th>
                <th>Qty</th>
                <th>UOM</th>
                <th>Rate</th>
                <th>Amount</th>
                <th>Debit Amount</th>
                <th>Credit Amount</th>
            </tr>
        """

    html_parts = [margin_css, render_table_head()]
    for idx, r in enumerate(display_rows, start=1):
        html_parts.append("<tr>")
        html_parts.append(f"<td>{frappe.format_value(r['voucher_date'], {'fieldtype':'Date'}) if r['voucher_date'] else ''}</td>")
        html_parts.append(f"<td>{frappe.utils.escape_html(r['voucher_no']) if r['voucher_no'] else ''}</td>")
        html_parts.append(f"<td>{frappe.utils.escape_html(r['particular'] or '')}</td>")
        html_parts.append(f"<td class='num'>{frappe.format_value(r['qty'], {'fieldtype':'Float'}) if r['qty'] is not None else ''}</td>")
        html_parts.append(f"<td>{frappe.utils.escape_html(r['uom']) if r['uom'] else ''}</td>")
        html_parts.append(f"<td class='num'>{frappe.format_value(r['rate'], {'fieldtype':'Currency'}) if r['rate'] is not None else ''}</td>")
        html_parts.append(f"<td class='num'>{frappe.format_value(r['amount'], {'fieldtype':'Currency'}) if r['amount'] is not None else ''}</td>")
        html_parts.append(f"<td class='num'>{frappe.format_value(r['debit'], {'fieldtype':'Currency'})}</td>")
        html_parts.append(f"<td class='num'>{frappe.format_value(r['credit'], {'fieldtype':'Currency'})}</td>")
        html_parts.append("</tr>")

        if idx % ROWS_PER_PAGE == 0:
            html_parts.append("</table>")
            html_parts.append("<div class='page-break'></div>")
            html_parts.append(render_table_head())

    # Totals row
    html_parts.append("<tr>")
    html_parts += ["<td></td>"] * 6
    html_parts.append(f"<td class='num'><b></b></td>")
    html_parts.append(f"<td class='num'><b>{frappe.format_value(total_debit, {'fieldtype':'Currency'})}</b></td>")
    html_parts.append(f"<td class='num'><b>{frappe.format_value(total_credit, {'fieldtype':'Currency'})}</b></td>")
    html_parts.append("</tr>")
    html_parts.append("</table>")

    html = "".join(html_parts)
    # Return HTML as the report body; other return slots left None
    return None, None, html, None, None

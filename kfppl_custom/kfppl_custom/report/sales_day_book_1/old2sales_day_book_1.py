# reports/sales_day_book/sales_day_book.py
import frappe
from frappe import _
from collections import defaultdict

def execute(filters=None):
    filters = filters or {}
    f_from_date = filters.get("from_date")
    f_to_date = filters.get("to_date")

    # ---- Print CSS + table styles
    margin_css = """
    <style>
      @page { size: A4; margin: 10mm; }
      .page-break { page-break-after: always; }
      table { border-collapse: collapse; width: 100%; font-size: 11px; }
      th, td { border: 1px solid #ddd; padding: 6px; }
      th { text-align: center; }
      td.num { text-align: right; }
    </style>
    """

    # ---- WHERE and params
    where = [
        "gle.is_cancelled = 0",
        "gle.voucher_type = 'Sales Invoice'",
        "IFNULL(si.is_opening, 'No') = 'No'"  # <-- exclude opening SIs
    ]
    params = {}
    if f_from_date:
        where.append("gle.posting_date >= %(from_date)s")
        params["from_date"] = f_from_date
    if f_to_date:
        where.append("gle.posting_date <= %(to_date)s")
        params["to_date"] = f_to_date

    # ---- Base GL query (joined with Sales Invoice to filter is_opening)
    base_sql = f"""
        SELECT
            gle.posting_date AS voucher_date,
            CASE WHEN IFNULL(gle.party, '') = '' THEN gle.account ELSE gle.party END AS particular,
            gle.voucher_type,
            gle.voucher_no,
            gle.debit,
            gle.credit
        FROM `tabGL Entry` gle
        INNER JOIN `tabSales Invoice` si ON si.name = gle.voucher_no
        WHERE {" AND ".join(where)}
        ORDER BY gle.posting_date, gle.voucher_no
    """

    gl_rows = frappe.db.sql(base_sql, params, as_dict=True)

    if not gl_rows:
        html = margin_css + "<p><b>No data for the selected period.</b></p>"
        return None, None, html, None, None

    # ---- Distinct vouchers from already-filtered GL rows
    voucher_nos = tuple(sorted({r["voucher_no"] for r in gl_rows if r.get("voucher_no")}))

    # ---- Bulk fetch SI Items, also excluding opening invoices (explicit join)
    items_by_parent = defaultdict(list)
    if voucher_nos:
        item_sql = """
            SELECT
                sii.parent,
                sii.item_code,
                sii.item_name,
                sii.qty,
                sii.uom,
                sii.rate,
                sii.amount
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.parent IN %(parents)s
              AND IFNULL(si.is_opening, 'No') = 'No'
            ORDER BY sii.parent, sii.idx
        """
        item_rows = frappe.db.sql(item_sql, {"parents": voucher_nos}, as_dict=True)
        for it in item_rows:
            items_by_parent[it["parent"]].append(it)

    # ---- Build final display rows
    display_rows = []
    seen = set()
    total_debit = 0.0
    total_credit = 0.0

    for r in gl_rows:
        vno = r["voucher_no"]
        first = vno not in seen
        if first:
            seen.add(vno)

        display_rows.append({
            "voucher_date": r["voucher_date"] if first else "",
            "voucher_no": vno if first else "",
            "particular": r["particular"],
            "qty": None,
            "uom": None,
            "rate": None,
            "amount": None,
            "debit": r.get("debit") or 0,
            "credit": r.get("credit") or 0,
        })
        total_debit += r.get("debit") or 0
        total_credit += r.get("credit") or 0

        # Append items immediately after the first GL line of that voucher
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

    # ---- Render HTML with simple pagination
    ROWS_PER_PAGE = 40

    def head():
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

    parts = [margin_css, head()]
    for idx, r in enumerate(display_rows, start=1):
        parts.append("<tr>")
        parts.append(f"<td>{frappe.format_value(r['voucher_date'], {{'fieldtype':'Date'}}) if r['voucher_date'] else ''}</td>")
        parts.append(f"<td>{frappe.utils.escape_html(r['voucher_no']) if r['voucher_no'] else ''}</td>")
        parts.append(f"<td>{frappe.utils.escape_html(r['particular'] or '')}</td>")
        parts.append(f"<td class='num'>{frappe.format_value(r['qty'], {{'fieldtype':'Float'}}) if r['qty'] is not None else ''}</td>")
        parts.append(f"<td>{frappe.utils.escape_html(r['uom']) if r['uom'] else ''}</td>")
        parts.append(f"<td class='num'>{frappe.format_value(r['rate'], {{'fieldtype':'Currency'}}) if r['rate'] is not None else ''}</td>")
        parts.append(f"<td class='num'>{frappe.format_value(r['amount'], {{'fieldtype':'Currency'}}) if r['amount'] is not None else ''}</td>")
        parts.append(f"<td class='num'>{frappe.format_value(r['debit'], {{'fieldtype':'Currency'}})}</td>")
        parts.append(f"<td class='num'>{frappe.format_value(r['credit'], {{'fieldtype':'Currency'}})}</td>")
        parts.append("</tr>")

        if idx % ROWS_PER_PAGE == 0:
            parts.append("</table>")
            parts.append("<div class='page-break'></div>")
            parts.append(head())

    # ---- Totals row
    parts.append("<tr>")
    parts += ["<td></td>"] * 6  # blank cols up to Amount
    parts.append("<td class='num'><b></b></td>")
    parts.append(f"<td class='num'><b>{frappe.format_value(total_debit, {{'fieldtype':'Currency'}})}</b></td>")
    parts.append(f"<td class='num'><b>{frappe.format_value(total_credit, {{'fieldtype':'Currency'}})}</b></td>")
    parts.append("</tr>")
    parts.append("</table>")

    html = "".join(parts)
    return None, None, html, None, None

# apps/kfppl_custom/kfppl_custom/kfppl_custom/report/sales_day_book_1/sales_day_book_1.py

import frappe
from collections import defaultdict, OrderedDict

def execute(filters=None):
    filters = frappe._dict(filters or {})
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
        "IFNULL(si.is_opening, 'No') = 'No'"  # exclude opening SIs
    ]
    params = {}
    if f_from_date:
        where.append("gle.posting_date >= %(from_date)s")
        params["from_date"] = f_from_date
    if f_to_date:
        where.append("gle.posting_date <= %(to_date)s")
        params["to_date"] = f_to_date

    # ---- Base GL query (use SI for time ordering; GL has no posting_time)
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
        ORDER BY
            si.posting_date,
            COALESCE(si.posting_time, TIME(si.creation)),
            gle.voucher_no,
            gle.name
    """
    gl_rows = frappe.db.sql(base_sql, params, as_dict=True)
    if not gl_rows:
        html = margin_css + "<p><b>No data for the selected period.</b></p>"
        return None, None, html, None, None

    # ---- Maintain overall voucher order as they appear in gl_rows
    voucher_order = []
    seen_v = set()
    for r in gl_rows:
        v = r["voucher_no"]
        if v and v not in seen_v:
            seen_v.add(v)
            voucher_order.append(v)

    # ---- Group GL rows per voucher (preserving within-voucher original order)
    gl_by_voucher = defaultdict(list)
    for r in gl_rows:
        gl_by_voucher[r["voucher_no"]].append(r)

    # ---- Bulk fetch SI Items (also excluding opening invoices)
    items_by_parent = defaultdict(list)
    if voucher_order:
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
        item_rows = frappe.db.sql(item_sql, {"parents": tuple(voucher_order)}, as_dict=True)
        for it in item_rows:
            items_by_parent[it["parent"]].append(it)

    # ---- Helpers (v15-safe)
    fmt_html = frappe.utils.escape_html
    fmt_date = frappe.utils.formatdate
    fmt_curr = frappe.utils.fmt_money

    def _float_precision():
        try:
            p = int(frappe.db.get_default("float_precision") or 3)
        except Exception:
            p = 3
        return max(0, p)

    _PREC = _float_precision()

    def fmt_float_local(val):
        if val is None:
            return ""
        try:
            return f"{float(val):.{_PREC}f}"
        except Exception:
            return str(val)

    # ---- Build final display rows with required intra-voucher ordering
    display_rows = []
    total_debit = 0.0
    total_credit = 0.0

    for vno in voucher_order:
        rows = gl_by_voucher[vno]

        # Split into debit-first then credit (preserve original relative order)
        debit_rows = [r for r in rows if (r.get("debit") or 0) > 0]
        credit_rows = [r for r in rows if (r.get("debit") or 0) <= 0]  # includes pure credit/zero

        ordered_gl = debit_rows + credit_rows

        # Emit GL lines for this voucher
        for idx_in_v, r in enumerate(ordered_gl):
            first = (idx_in_v == 0)
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

        # Then items LAST (for this voucher)
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
        parts.append(f"<td>{fmt_date(r['voucher_date']) if r['voucher_date'] else ''}</td>")
        parts.append(f"<td>{fmt_html(r['voucher_no']) if r['voucher_no'] else ''}</td>")
        parts.append(f"<td>{fmt_html(r['particular'] or '')}</td>")
        parts.append(f"<td class='num'>{fmt_float_local(r['qty']) if r['qty'] is not None else ''}</td>")
        parts.append(f"<td>{fmt_html(r['uom']) if r['uom'] else ''}</td>")
        parts.append(f"<td class='num'>{fmt_curr(r['rate']) if r['rate'] is not None else ''}</td>")
        parts.append(f"<td class='num'>{fmt_curr(r['amount']) if r['amount'] is not None else ''}</td>")
        parts.append(f"<td class='num'>{fmt_curr(r['debit'])}</td>")
        parts.append(f"<td class='num'>{fmt_curr(r['credit'])}</td>")
        parts.append("</tr>")

        if idx % ROWS_PER_PAGE == 0:
            parts.append("</table>")
            parts.append("<div class='page-break'></div>")
            parts.append(head())

    # ---- Totals row
    parts.append("<tr>")
    parts += ["<td></td>"] * 6
    parts.append("<td class='num'><b></b></td>")
    parts.append(f"<td class='num'><b>{fmt_curr(total_debit)}</b></td>")
    parts.append(f"<td class='num'><b>{fmt_curr(total_credit)}</b></td>")
    parts.append("</tr>")
    parts.append("</table>")

    html = "".join(parts)
    return None, None, html, None, None

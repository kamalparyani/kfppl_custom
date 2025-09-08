# Copyright (c) 2025, V12 Infotech and contributors
# For license information, please see license.txt

# apps/<your_app>/<your_app>/<your_app>/report/day_book/day_book.py
import frappe

def execute(filters=None):
    filters = frappe._dict(filters or {})
    f_from_date = filters.get("from_date")
    f_to_date = filters.get("to_date")

    # -------- Print CSS + table styles (like Sales/Purchase Day Book 1)
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

    # -------- WHERE + params (preserve logic)
    where = [
        "gle.is_cancelled = 0",
        "gle.voucher_type IN ('Journal Entry','Payment Entry')"
    ]
    params = {}
    # Preserve your “if not passed, default to today” behavior here in SQL
    if f_from_date:
        where.append("gle.posting_date >= %(from_date)s")
        params["from_date"] = f_from_date
    else:
        where.append("gle.posting_date >= %(today)s")
        params["today"] = frappe.utils.nowdate()

    if f_to_date:
        where.append("gle.posting_date <= %(to_date)s")
        params["to_date"] = f_to_date
    else:
        if "today" not in params:
            params["today"] = frappe.utils.nowdate()
        where.append("gle.posting_date <= %(today)s")

    # -------- Base query (LEFT JOIN Journal Entry for user_remark), same ORDER BY
    base_sql = f"""
        SELECT
            gle.posting_date AS voucher_date,
            CASE WHEN IFNULL(gle.party, '') = '' THEN gle.account ELSE gle.party END AS particular,
            gle.voucher_type,
            gle.voucher_no,
            gle.debit AS debit_in_account,
            gle.credit AS credit_in_account,
            je.user_remark
        FROM `tabGL Entry` gle
        LEFT OUTER JOIN `tabJournal Entry` je ON je.name = gle.voucher_no
        WHERE {" AND ".join(where)}
        ORDER BY gle.posting_date, gle.voucher_no DESC
    """
    rows = frappe.db.sql(base_sql, params, as_dict=True)

    # If no data, return empty HTML body (same contract as your current report)
    if not rows:
        html = margin_css + "<p><b>No data for the selected period.</b></p>"
        return None, None, html, None, None

    # -------- Helpers (v15-safe; keep INR formatting to match your code)
    fmt_html = frappe.utils.escape_html
    fmt_date = frappe.utils.formatdate
    fmt_curr = lambda x: frappe.utils.fmt_money(x, currency="INR")

    # -------- Build display rows with duplicate-voucher suppression (same logic)
    display_rows = []
    seen_vouchers = set()
    total_dr = 0.0
    total_cr = 0.0

    # pagination: keep your 30 rows per page
    ROWS_PER_PAGE = 30

    # table head (same widths as your template)
    def head():
        return """
        <table width="100%">
          <tr>
            <th style="text-align:center;width:10%;">Voucher Date</th>
            <th style="text-align:center;width:15%;">Voucher No</th>
            <th style="text-align:center;width:10%;">Voucher Type</th>
            <th style="text-align:center;width:35%;">Particular</th>
            <th style="text-align:center;width:15%;">Debit Amount</th>
            <th style="text-align:center;width:15%;">Credit Amount</th>
          </tr>
        """

    parts = [margin_css, head()]

    # We’ll render directly while iterating to preserve your exact “remarks” logic
    itemcount = 1

    for idx, r in enumerate(rows):
        vno = r.get("voucher_no")
        first_occurrence = vno not in seen_vouchers
        if first_occurrence:
            seen_vouchers.add(vno)

        # Compute printable cells (preserve “blank on repeats” behavior)
        printable_date  = r["voucher_date"] if first_occurrence else ""
        printable_vno   = vno if first_occurrence else ""
        printable_vtype = r.get("voucher_type") if first_occurrence else ""
        printable_part  = r.get("particular") or ""
        debit_val       = r.get("debit_in_account") or 0
        credit_val      = r.get("credit_in_account") or 0

        # Page break handling (same logic)
        if itemcount % ROWS_PER_PAGE == 0:
            parts.append("</table>")
            parts.append("<div class='page-break'></div>")
            parts.append(head())
        # Row
        parts.append("<tr>")
        parts.append(f"<td>{fmt_date(printable_date) if printable_date else ''}</td>")
        parts.append(f"<td>{fmt_html(printable_vno) if printable_vno else ''}</td>")
        parts.append(f"<td>{fmt_html(printable_vtype) if printable_vtype else ''}</td>")
        parts.append(f"<td>{fmt_html(printable_part)}</td>")
        parts.append(f"<td class='num'>{fmt_curr(debit_val)}</td>")
        parts.append(f"<td class='num'>{fmt_curr(credit_val)}</td>")
        parts.append("</tr>")

        total_dr += debit_val
        total_cr += credit_val
        itemcount += 1

        # ---- Remarks logic (preserved):
        # Your code checks:
        #   remarks != "" and remarks != "None" and next_remarks != "" and next_remarks != "None" and remarks != next_remarks
        # We normalize to the SAME condition below.
        remarks = str(r.get("user_remark"))  # str(None) -> "None" (same as your code path)
        next_remarks = ""
        if idx < len(rows) - 1:
            nr = rows[idx + 1].get("user_remark")
            if nr is not None:
                next_remarks = nr  # keep as original (empty if None)

        if (remarks != "" and remarks != "None"
                and next_remarks != "" and next_remarks != "None"
                and remarks != next_remarks):
            # Page break handling for the remarks row
            if itemcount % ROWS_PER_PAGE == 0:
                parts.append("</table>")
                parts.append("<div class='page-break'></div>")
                parts.append(head())

            parts.append("<tr>")
            parts.append("<td></td>")
            parts.append("<td></td>")
            parts.append("<td></td>")
            parts.append(f"<td>{fmt_html(remarks)}</td>")
            parts.append("<td></td>")
            parts.append("<td></td>")
            parts.append("</tr>")
            itemcount += 1

    # -------- Totals row (same as your code)
    parts.append("<tr>")
    parts += ["<td></td>"] * 4
    parts.append(f"<td class='num'><b>{fmt_curr(total_dr)}</b></td>")
    parts.append(f"<td class='num'><b>{fmt_curr(total_cr)}</b></td>")
    parts.append("</tr>")
    parts.append("</table>")

    html = "".join(parts)
    return None, None, html, None, None

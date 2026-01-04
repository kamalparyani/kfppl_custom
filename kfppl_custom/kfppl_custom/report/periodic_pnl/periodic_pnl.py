# Copyright (c) 2026, V12 Infotech and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe import _


def _as_list(v):
    """MultiSelectList can come as list or JSON string."""
    if not v:
        return []
    if isinstance(v, str):
        try:
            v = frappe.parse_json(v)
        except Exception:
            # if some caller sends comma separated string
            v = [x.strip() for x in v.split(",") if x.strip()]
    return v if isinstance(v, list) else [v]



def get_parent_accounts(account):
    parent_accounts = []
    while True:
        parent_account = frappe.db.get_value("Account", account, "parent_account")
        if not parent_account:
            break
        parent_accounts.insert(0, parent_account)
        if parent_account in ["Income - KFPPL", "Expenses - KFPPL"]:
            break
        account = parent_account
    return parent_accounts

def get_columns():
    return [
        {"fieldname": "account", "label": _("Account"), "fieldtype": "Data", "hidden": 1},
        {"fieldname": "parent_account", "label": _("Account"), "fieldtype": "Data", "width": 700},
        {"fieldname": "debit", "label": _("Debit"), "fieldtype": "Currency", "hidden": 1},
        {"fieldname": "credit", "label": _("Credit"), "fieldtype": "Currency", "hidden": 1},
        {"fieldname": "balance", "label": _("Balance"), "fieldtype": "Currency", "width": 150},
    ]


def execute(filters=None):
    filters = filters or {}
    f_from_date = filters.get("from_date")
    f_to_date = filters.get("to_date")
    f_cost_centers = _as_list(filters.get("cost_center"))

    # -------------------------
    # 1) GL Entry (Income/Expense)
    # -------------------------
    gl_conditions = ["`tabGL Entry`.is_cancelled = 0"]
    gl_values = {}

    if f_from_date:
        gl_conditions.append("`tabGL Entry`.posting_date >= %(from_date)s")
        gl_values["from_date"] = f_from_date

    if f_to_date:
        gl_conditions.append("`tabGL Entry`.posting_date <= %(to_date)s")
        gl_values["to_date"] = f_to_date

    if f_cost_centers:
        gl_conditions.append("`tabGL Entry`.cost_center IN %(cost_centers)s")
        gl_values["cost_centers"] = tuple(f_cost_centers)

    gl_query = f"""
        SELECT
            account,
            SUM(debit) AS debit,
            SUM(credit) AS credit
        FROM `tabGL Entry`
        WHERE {" AND ".join(gl_conditions)}
        GROUP BY `tabGL Entry`.account
    """

    data = frappe.db.sql(gl_query, gl_values, as_dict=True)

    # -------------------------
    # 2) Sales Pending Amount (DN not invoiced)
    # -------------------------
    sales_conditions = [
        "dn.posting_date BETWEEN %(from_date)s AND %(to_date)s",
        "dni.qty > 0",
        "dn.docstatus = 1",
        "(sii.name IS NULL OR sii.docstatus = 0)",
    ]
    sales_values = {"from_date": f_from_date, "to_date": f_to_date}

    if f_cost_centers:
        sales_conditions.append("ID.selling_cost_center IN %(cost_centers)s")
        sales_values["cost_centers"] = tuple(f_cost_centers)

    sales_order_query = f"""
        SELECT
            SUM(dni.amount) AS `Total Delivery Amount`
        FROM `tabDelivery Note Item` dni
        LEFT JOIN `tabDelivery Note` dn ON dn.name = dni.parent
        LEFT JOIN `tabSales Invoice Item` sii ON sii.dn_detail = dni.name
        JOIN `tabItem Default` AS ID ON dni.item_code = ID.parent
        WHERE {" AND ".join(sales_conditions)}
    """

    sales_order = frappe.db.sql(sales_order_query, sales_values, as_dict=True)

    # -------------------------
    # 3) Purchase Pending Amount (PR not invoiced)
    # -------------------------
    purchase_conditions = [
        "gr.posting_date BETWEEN %(from_date)s AND %(to_date)s",
        "pri.qty > 0",
        "gr.docstatus = 1",
        "(pii.name IS NULL OR pii.docstatus = 0)",
    ]
    purchase_values = {"from_date": f_from_date, "to_date": f_to_date}

    if f_cost_centers:
        purchase_conditions.append("ID.buying_cost_center IN %(cost_centers)s")
        purchase_values["cost_centers"] = tuple(f_cost_centers)

    purchase_order_query = f"""
        SELECT
            SUM(pri.amount) AS `Total Receipt Amount`
        FROM `tabPurchase Receipt Item` pri
        LEFT JOIN `tabPurchase Receipt` gr ON gr.name = pri.parent
        LEFT JOIN `tabPurchase Invoice Item` pii
            ON pii.item_code = pri.item_code
            AND pii.purchase_receipt = pri.parent
        JOIN `tabItem Default` AS ID ON pri.item_code = ID.parent
        WHERE {" AND ".join(purchase_conditions)}
    """

    purchase_order = frappe.db.sql(purchase_order_query, purchase_values, as_dict=True)

    # -------------------------
    # 4) Stock Opening Balance (SLE Opening + before from_date)
    # -------------------------
    stock_cc_cond = ""
    stock_open_vals = {"from_date": f_from_date}

    if f_cost_centers:
        stock_cc_cond = """
            AND (
                `tabItem Default`.buying_cost_center IN %(cost_centers)s
                OR `tabItem Default`.selling_cost_center IN %(cost_centers)s
            )
        """
        stock_open_vals["cost_centers"] = tuple(f_cost_centers)

    stock_opening_balance_query = f"""
        SELECT SUM(stock_value_difference) AS total_balance
        FROM (
            SELECT stock_value_difference
            FROM `tabStock Ledger Entry`
            LEFT JOIN `tabItem Default`
                ON `tabStock Ledger Entry`.item_code = `tabItem Default`.parent
            WHERE voucher_no LIKE '%%Opening%%'
            {stock_cc_cond}

            UNION ALL

            SELECT stock_value_difference
            FROM `tabStock Ledger Entry`
            LEFT JOIN `tabItem Default`
                ON `tabStock Ledger Entry`.item_code = `tabItem Default`.parent
            WHERE posting_date < %(from_date)s
              AND voucher_no NOT LIKE '%%Opening%%'
              AND is_cancelled = 0
            {stock_cc_cond}
        ) AS combined_totals
    """

    stock_opening_balance = frappe.db.sql(stock_opening_balance_query, stock_open_vals, as_dict=True)

    # -------------------------
    # 5) Stock Closing Balance (your CTE, but with CC filter as IN)
    # -------------------------
    stock_closing_vals = {"from_date": f_from_date, "to_date": f_to_date}
    cc_where = ""
    if f_cost_centers:
        cc_where = """
            WHERE (
                id.buying_cost_center IN %(cost_centers)s
                OR id.selling_cost_center IN %(cost_centers)s
            )
        """
        stock_closing_vals["cost_centers"] = tuple(f_cost_centers)

    stock_closing_balance_query = f"""
        WITH opening_balance AS (
            SELECT
                item_code,
                SUM(stock_value_difference) AS total_balance
            FROM `tabStock Ledger Entry`
            WHERE (voucher_no LIKE '%%Opening%%' OR posting_date < %(from_date)s)
              AND is_cancelled = 0
            GROUP BY item_code
        ),
        total_value_change AS (
            SELECT
                item_code,
                SUM(stock_value_difference) AS total_change
            FROM `tabStock Ledger Entry`
            WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
              AND voucher_no NOT LIKE '%%Opening%%'
              AND is_cancelled = 0
            GROUP BY item_code
        )
        SELECT
            i.item_code,
            id.buying_cost_center,
            id.selling_cost_center,
            IFNULL(ob.total_balance, 0) AS opening_balance,
            IFNULL(tvc.total_change, 0) AS total_change,
            (IFNULL(ob.total_balance, 0) + IFNULL(tvc.total_change, 0)) AS closing_value
        FROM `tabItem` i
        LEFT JOIN `tabItem Default` id ON i.name = id.parent
        LEFT JOIN opening_balance ob ON i.item_code = ob.item_code
        LEFT JOIN total_value_change tvc ON i.item_code = tvc.item_code
        {cc_where}
        ORDER BY i.item_code
    """

    stock_closing_balance = frappe.db.sql(stock_closing_balance_query, stock_closing_vals, as_dict=True)

    # -------------------------
    # Your existing report logic continues below (unchanged)
    # -------------------------
    income_data = []
    expense_data = []
    sales_order_data = []
    purchase_order_data = []
    stock_opening_balance_data = []
    stock_closing_balance_data = []

    total_income_balance = 0
    total_expense_balance = 0
    total_sales_order_pending_amount = 0
    total_purchase_order_pending_amount = 0
    total_stock_opening_balance = 0
    total_stock_closing_balance = 0

    income_accounts_map = {}
    expense_accounts_map = {}

    added_income_parents = set()
    added_expense_parents = set()

    for row in data:
        parent_accounts = get_parent_accounts(row["account"])
        if "Income - KFPPL" in parent_accounts:
            for parent in parent_accounts:
                if parent not in added_income_parents:
                    income_accounts_map[parent] = []
                    added_income_parents.add(parent)
            income_accounts_map[parent_accounts[-1]].append(row)

            row["balance"] = (row.get("credit") or 0) - (row.get("debit") or 0)
            total_income_balance += row["balance"]

        elif "Expenses - KFPPL" in parent_accounts:
            for parent in parent_accounts:
                if parent not in added_expense_parents:
                    expense_accounts_map[parent] = []
                    added_expense_parents.add(parent)
            expense_accounts_map[parent_accounts[-1]].append(row)

            row["balance"] = (row.get("debit") or 0) - (row.get("credit") or 0)
            total_expense_balance += row["balance"]

    def map_parent_account(accounts_map):
        result = []
        for parent, children in accounts_map.items():
            for child in children:
                result.append(
                    {
                        "parent_account": "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + child["account"] + "</p>",
                        "balance": child["balance"],
                    }
                )
        return result

    income_data = map_parent_account(income_accounts_map)
    expense_data = map_parent_account(expense_accounts_map)

    if sales_order and sales_order[0].get("Total Delivery Amount") is not None:
        total_sales_order_pending_amount = sales_order[0]["Total Delivery Amount"]

    if purchase_order and purchase_order[0].get("Total Receipt Amount") is not None:
        total_purchase_order_pending_amount = purchase_order[0]["Total Receipt Amount"]

    # FIX: as_dict=True => dict access, not attribute
    if stock_opening_balance and stock_opening_balance[0].get("total_balance") is not None:
        total_stock_opening_balance = stock_opening_balance[0]["total_balance"]

    total_stock_closing_balance = sum(d.get("closing_value") or 0 for d in stock_closing_balance)

    profit = (total_income_balance - total_expense_balance)
    net_stock_adjustment = (
        (total_sales_order_pending_amount + total_stock_closing_balance)
        - total_purchase_order_pending_amount
        - total_stock_opening_balance
    )
    net_profit_or_loss = profit + net_stock_adjustment

    if total_income_balance:
        income_data.append({"parent_account": "<b> Total Income (Credit)", "balance": total_income_balance})
        income_data.append({"parent_account": "", "balance": None})

    if total_expense_balance:
        expense_data.append({"parent_account": "<b> Total Expenses (Debit)", "balance": total_expense_balance})

    if total_income_balance and total_expense_balance:
        expense_data.append({"parent_account": "<b> Profit Of The Year", "balance": profit})
        expense_data.append({"parent_account": "", "balance": ""})

    if total_sales_order_pending_amount:
        sales_order_data.append({"parent_account": "<b> Sales Order Pending Amount", "balance": total_sales_order_pending_amount})

    if total_stock_closing_balance:
        stock_closing_balance_data.append({"parent_account": "<b> Stock Ledger Closing Balance", "balance": total_stock_closing_balance})

    if total_purchase_order_pending_amount:
        purchase_order_data.append({"parent_account": "<b> Purchase Order Pending Amount", "balance": total_purchase_order_pending_amount})

    if total_stock_opening_balance:
        stock_opening_balance_data.append({"parent_account": "<b> Stock Ledger Opening Balance", "balance": total_stock_opening_balance})
        stock_closing_balance_data.append({"parent_account": "", "balance": ""})

    if net_stock_adjustment:
        stock_closing_balance_data.append({"parent_account": "<b> Net Stock Adjustment", "balance": net_stock_adjustment})

    if net_profit_or_loss:
        stock_closing_balance_data.append({"parent_account": "<b> Net Profit And Loss", "balance": net_profit_or_loss})

    columns = get_columns()
    return columns, income_data + expense_data + sales_order_data + purchase_order_data + stock_opening_balance_data + stock_closing_balance_data

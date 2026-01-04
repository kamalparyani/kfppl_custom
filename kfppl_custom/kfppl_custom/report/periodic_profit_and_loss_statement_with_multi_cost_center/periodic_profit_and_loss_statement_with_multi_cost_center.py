# Copyright (c) 2026, V12 Infotech and contributors
# For license information, please see license.txt

# import frappe


import frappe
from frappe import _

def get_columns():
    columns = [
        {
            'fieldname': 'account',
            'label': _('Account'),
            'fieldtype': 'Data',
            'hidden': 1
        },
        {
            'fieldname': 'parent_account',
            'label': _('Account'),
            'fieldtype': 'Data',
            'width': 700
        },
        {
            'fieldname': 'debit',
            'label': _('Debit'),
            'fieldtype': 'Currency',
            'hidden': 1
        },
        {
            'fieldname': 'credit',
            'label': _('Credit'),
            'fieldtype': 'Currency',
            'hidden': 1
        },
        {
            'fieldname': 'balance',
            'label': _('Balance'),
            'fieldtype': 'Currency',
            'width': 150
        },
    ]
    return columns

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

def execute(filters=None):
    f_from_date = filters.get("from_date")
    f_to_date = filters.get("to_date")
    f_cost_center = filters.get("cost_center")

    query = """
        SELECT 
            account, 
            SUM(debit) AS debit,
            SUM(credit) AS credit
        FROM 
            `tabGL Entry`
        WHERE 
            is_cancelled = 0
    """

    sales_order_query = """
    SELECT 
    SUM(dni.amount) AS "Total Delivery Amount"  
    FROM
        `tabSales Order` so
    INNER JOIN 
        `tabSales Order Item` soi ON so.name = soi.parent
    LEFT JOIN 
       `tabDelivery Note Item` dni ON soi.name = dni.so_detail 
    LEFT JOIN 
        `tabDelivery Note` dn ON dn.name = dni.parent
    JOIN
			`tabItem Default` AS ID ON soi.item_code = ID.parent
    WHERE
        dn.posting_date BETWEEN '""" + f_from_date + """' AND '""" + f_to_date + """'
        AND dni.qty > 0                                  
        AND dn.docstatus = 1                             
        AND soi.billed_amt = 0                           
        AND so.docstatus = 1
                                     


    """

    sales_order_query = """

    SELECT 
        SUM(dni.amount) AS "Total Delivery Amount"     
    FROM
        `tabDelivery Note Item` dni
    LEFT JOIN 
        `tabDelivery Note` dn ON dn.name = dni.parent
    LEFT JOIN 
        `tabSales Invoice Item` sii ON sii.dn_detail = dni.name  
    JOIN
			`tabItem Default` AS ID ON dni.item_code = ID.parent
    WHERE
        dn.posting_date BETWEEN '""" + f_from_date + """' AND '""" + f_to_date + """'
        AND dni.qty > 0                                
        AND dn.docstatus = 1                           
        AND (sii.name IS NULL or sii.docstatus = 0)                         

"""





    purchase_order_query = """
    SELECT 
    SUM(pri.amount) AS "Total Receipt Amount"
    FROM
        `tabPurchase Order` po
    INNER JOIN 
        `tabPurchase Order Item` poi ON po.name = poi.parent
    LEFT JOIN 
        `tabPurchase Receipt Item` pri ON poi.name = pri.purchase_order_item
    LEFT JOIN 
        `tabPurchase Receipt` gr ON gr.name = pri.parent
    JOIN
	    `tabItem Default` AS ID ON poi.item_code = ID.parent
    WHERE
        gr.posting_date BETWEEN '""" + f_from_date + """' AND '""" + f_to_date + """'
    AND pri.qty > 0                       
    AND poi.billed_amt = 0                       
    AND po.docstatus = 1 

    """

    purchase_order_query = """

    SELECT 
    SUM(pri.amount) AS "Total Receipt Amount"      
    FROM
        `tabPurchase Receipt Item` pri
    LEFT JOIN 
        `tabPurchase Receipt` gr ON gr.name = pri.parent
    LEFT JOIN 
        `tabPurchase Invoice Item` pii ON pii.item_code = pri.item_code 
        AND pii.purchase_receipt = pri.parent   
     JOIN
	    `tabItem Default` AS ID ON pri.item_code = ID.parent       
    WHERE
        gr.posting_date BETWEEN '""" + f_from_date + """' AND '""" + f_to_date + """'
        AND pri.qty > 0                                
        AND (pii.name IS NULL or pii.docstatus = 0)                           
        AND gr.docstatus = 1                         














"""


    stock_opening_balance_query = """
      SELECT 
        SUM(stock_value_difference) AS total_balance
    FROM (
        SELECT 
        stock_value_difference 
    FROM `tabStock Ledger Entry` 
    LEFT JOIN
		`tabItem Default` ON `tabStock Ledger Entry`.item_code = `tabItem Default`.parent
    WHERE voucher_no LIKE '%%Opening%%'"""
    if f_cost_center:
        stock_opening_balance_query = stock_opening_balance_query + """ And (`tabItem Default`.buying_cost_center ='""" + f_cost_center + """' OR `tabItem Default`.selling_cost_center ='""" + f_cost_center + """')"""
    
    stock_opening_balance_query = stock_opening_balance_query + """
    UNION ALL

    SELECT 
        stock_value_difference 
    FROM `tabStock Ledger Entry` 
    LEFT JOIN
		`tabItem Default` ON `tabStock Ledger Entry`.item_code = `tabItem Default`.parent
    WHERE posting_date < '""" + f_from_date + """'
      AND voucher_no NOT LIKE '%%Opening%%' 
      AND is_cancelled = 0 """
    if f_cost_center:
        stock_opening_balance_query = stock_opening_balance_query + """ And (`tabItem Default`.buying_cost_center ='""" + f_cost_center + """' OR `tabItem Default`.selling_cost_center ='""" + f_cost_center + """')"""
    
    stock_opening_balance_query = stock_opening_balance_query + """
    ) AS combined_totals;
    """

    stock_closing_balance_query = """
       WITH opening_balance AS (
    SELECT 
        item_code,
        SUM(stock_value_difference) AS total_balance
    FROM 
        `tabStock Ledger Entry`
    WHERE 
        (voucher_no LIKE '%%Opening%%' OR posting_date < '""" + f_from_date + """') 
        AND is_cancelled = 0
    GROUP BY 
        item_code
),
total_value_change AS (
    SELECT 
        item_code,
        SUM(stock_value_difference) AS total_change
    FROM 
        `tabStock Ledger Entry`
    WHERE 
        posting_date BETWEEN '""" + f_from_date + """' AND '""" + f_to_date + """'  
        AND voucher_no NOT LIKE '%%Opening%%'  -- Exclude opening transactions
        AND is_cancelled = 0  -- Include only valid, non-cancelled entries
    GROUP BY 
        item_code
)
SELECT 
    i.item_code,
    id.buying_cost_center,
    id.selling_cost_center,
    IFNULL(ob.total_balance, 0) AS opening_balance,  
    IFNULL(tvc.total_change, 0) AS total_change,  
    (IFNULL(ob.total_balance, 0) + IFNULL(tvc.total_change, 0)) AS closing_value  
FROM 
    `tabItem` i
LEFT JOIN 
    `tabItem Default` id ON i.name = id.parent
LEFT JOIN 
    opening_balance ob ON i.item_code = ob.item_code
LEFT JOIN 
    total_value_change tvc ON i.item_code = tvc.item_code
"""
    if f_cost_center:
        stock_closing_balance_query = stock_closing_balance_query + """ 
        WHERE (id.buying_cost_center = '""" + f_cost_center + """' OR id.selling_cost_center = '""" + f_cost_center + """')  """

    stock_closing_balance_query = stock_closing_balance_query + """


    ORDER BY 
    i.item_code;

    """
    

    if f_from_date:
        query = query + """ And `tabGL Entry`.posting_date >='""" + f_from_date + """'"""
       # sales_order_query = sales_order_query + """ And SO.transaction_date >='""" + f_from_date + """'"""
       # purchase_order_query = purchase_order_query + """ And PO.transaction_date >='""" + f_from_date + """'"""
        
    if f_to_date:
        query = query + """ And `tabGL Entry`.posting_date <='""" + f_to_date + """'"""
       # sales_order_query = sales_order_query + """ And SO.transaction_date <='""" + f_to_date + """'"""
        #purchase_order_query = purchase_order_query + """ And PO.transaction_date <='""" + f_to_date + """'"""
       # stock_closing_balance_query = stock_closing_balance_query + """ And `tabStock Ledger Entry`.posting_date <='""" + f_to_date + """'"""
    if f_cost_center:
        query = query + """ And `tabGL Entry`.cost_center ='""" + f_cost_center + """'"""
        sales_order_query = sales_order_query + """ And ID.selling_cost_center = '""" + f_cost_center + """'""" 
        purchase_order_query = purchase_order_query + """ And ID.buying_cost_center ='""" + f_cost_center + """'"""
        #stock_opening_balance_query = stock_opening_balance_query + """ And (`tabItem Default`.buying_cost_center ='""" + f_cost_center + """' OR `tabItem Default`.selling_cost_center ='""" + f_cost_center + """')"""
        #stock_closing_balance_query = stock_closing_balance_query + """ And (`tabItem Default`.buying_cost_center ='""" + f_cost_center + """' OR `tabItem Default`.selling_cost_center ='""" + f_cost_center + """')"""
    query = query + """ GROUP BY `tabGL Entry`.account """
    #sales_order_query = sales_order_query + """ ORDER BY SO.creation ASC """
    #purchase_order_query = purchase_order_query + """ ORDER BY PO.creation ASC """
    


    data = frappe.db.sql(query, as_dict=True)

    sales_order = frappe.db.sql(sales_order_query, as_dict=True)

    purchase_order = frappe.db.sql(purchase_order_query, as_dict=True)

    stock_opening_balance = frappe.db.sql(stock_opening_balance_query, as_dict=True)

    stock_closing_balance = frappe.db.sql(stock_closing_balance_query, as_dict=True)
    
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
        parent_accounts = get_parent_accounts(row['account'])
        if "Income - KFPPL" in parent_accounts:
            for parent in parent_accounts:
                if parent not in added_income_parents:
                    income_accounts_map[parent] = []
                    added_income_parents.add(parent)
            income_accounts_map[parent_accounts[-1]].append(row)

            row['balance'] = row['credit'] - row['debit']
            total_income_balance += row['balance']
        elif "Expenses - KFPPL" in parent_accounts:
            for parent in parent_accounts:
                if parent not in added_expense_parents:
                    expense_accounts_map[parent] = []
                    added_expense_parents.add(parent)
            expense_accounts_map[parent_accounts[-1]].append(row)

            row['balance'] = row['debit'] - row['credit']
            total_expense_balance += row['balance']

    def map_parent_account(accounts_map):
        result = []
        for parent, children in accounts_map.items():
            #result.append({'parent_account': parent + " > "})
            for child in children:
                result.append({'parent_account':  "<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + child['account'] + "</p>", 'balance': child['balance']})
        return result

    income_data = map_parent_account(income_accounts_map)
    expense_data = map_parent_account(expense_accounts_map)
    
    # for row in sales_order:
    #     pending_amount = row['Pending Amount']
    #     if pending_amount is not None:
    #         total_sales_order_pending_amount += pending_amount
    if sales_order[0]['Total Delivery Amount'] is not None:
        total_sales_order_pending_amount = sales_order[0]['Total Delivery Amount']

    # for row in purchase_order:
    #     pending_amount = row['Pending Amount']
    #     if pending_amount is not None:
    #         total_purchase_order_pending_amount += pending_amount
    if purchase_order[0]['Total Receipt Amount'] is not None:
        total_purchase_order_pending_amount = purchase_order[0]['Total Receipt Amount']
    # for row in stock_opening_balance:
    #     balance = row['opening_amount']
    #     if balance is not None:
    #         total_stock_opening_balance += balance
    #total_stock_opening_balance = stock_opening_balance[0][0]
    if stock_opening_balance[0].total_balance is not None:
        total_stock_opening_balance = stock_opening_balance[0].total_balance

    # for row in stock_closing_balance:
    #     balance = row['closing_amount']
    #     if balance is not None:
    #         total_stock_closing_balance += balance
    #if stock_closing_balance[0].total is not None:
    #    total_stock_closing_balance = stock_closing_balance[0].total
    total_stock_closing_balance = sum(d['closing_value'] for d in stock_closing_balance)


    profit = (total_income_balance - total_expense_balance)
    net_stock_adjustment = (total_sales_order_pending_amount + total_stock_closing_balance) - total_purchase_order_pending_amount - total_stock_opening_balance
    net_profit_or_loss = profit + net_stock_adjustment

    if total_income_balance:
        income_data.append({
            'parent_account': '<b> Total Income (Credit)',
            'balance': total_income_balance
        })

        income_data.append({
            'parent_account': '',
            'balance': None
        })

    if total_expense_balance:
        expense_data.append({
            'parent_account': '<b> Total Expenses (Debit)',
            'balance': total_expense_balance
        })

    if total_income_balance and total_expense_balance:
        expense_data.append({
            'parent_account': '<b> Profit Of The Year',
            'balance': profit
        })

        expense_data.append({
            'parent_account': '',
            'balance': ''
        })

    if total_sales_order_pending_amount:
        sales_order_data.append({
            'parent_account': '<b> Sales Order Pending Amount',
            'balance': total_sales_order_pending_amount
        })

    if total_stock_closing_balance:
        stock_closing_balance_data.append({
            'parent_account': '<b> Stock Ledger Closing Balance',
            'balance': total_stock_closing_balance
        })

    if total_purchase_order_pending_amount:
        purchase_order_data.append({
            'parent_account': '<b> Purchase Order Pending Amount',
            'balance': total_purchase_order_pending_amount
        })

    if total_stock_opening_balance:
        stock_opening_balance_data.append({
            'parent_account': '<b> Stock Ledger Opening Balance',
            'balance': total_stock_opening_balance
        })

        stock_closing_balance_data.append({
            'parent_account': '',
            'balance': ''
        })

    if net_stock_adjustment:
        stock_closing_balance_data.append({
            'parent_account': '<b> Net Stock Adjustment',
            'balance': net_stock_adjustment
        })

    if net_profit_or_loss:
        stock_closing_balance_data.append({
            'parent_account': '<b> Net Profit And Loss',
            'balance': net_profit_or_loss
        })

    columns = get_columns()
    return columns, income_data + expense_data + sales_order_data + purchase_order_data + stock_opening_balance_data + stock_closing_balance_data
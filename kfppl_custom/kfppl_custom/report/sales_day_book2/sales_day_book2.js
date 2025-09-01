// Copyright (c) 2025, V12 Infotech and contributors
// For license information, please see license.txt

// apps/kfppl_custom/kfppl_custom/kfppl_custom/report/sales_day_book_1/sales_day_book_1.js
frappe.query_reports['sales day book2'] = {
	filters: [
	  {
		fieldname: 'from_date',
		label: __('From Date'),
		fieldtype: 'Date',
		default: frappe.datetime.month_start()
	  },
	  {
		fieldname: 'to_date',
		label: __('To Date'),
		fieldtype: 'Date',
		default: frappe.datetime.now_date()
	  }
	]
  };
  
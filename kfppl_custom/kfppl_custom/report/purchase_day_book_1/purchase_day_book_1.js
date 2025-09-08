// Copyright (c) 2025, V12 Infotech and contributors
// For license information, please see license.txt

// apps/kfppl_custom/kfppl_custom/kfppl_custom/report/purchase_day_book_1/purchase_day_book_1.js
frappe.query_reports['purchase day book 1'] = {
	filters: [
	  {
		fieldname: 'from_date',
		label: __('From Date'),
		fieldtype: 'Date',
		default: frappe.datetime.month_start() // or now_date()
	  },
	  {
		fieldname: 'to_date',
		label: __('To Date'),
		fieldtype: 'Date',
		default: frappe.datetime.now_date()
	  }
	]
  };
  
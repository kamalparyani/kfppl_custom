// Copyright (c) 2025, V12 Infotech and contributors
// For license information, please see license.txt

// reports/sales_day_book/sales_day_book.js
// frappe.query_reports['sales day book 1'] = {
// 	"filters": [
// 	  {
// 		"fieldname": "from_date",
// 		"label": __("From Date"),
// 		"fieldtype": "Date",
// 		"default": frappe.datetime.now_date()
// 	  },
// 	  {
// 		"fieldname": "to_date",
// 		"label": __("To Date"),
// 		"fieldtype": "Date",
// 		"default": frappe.datetime.now_date()
// 	  }
// 	]
//   };


// // reports/sales_day_book/sales_day_book.js
// frappe.query_reports['sales day book 1'] = {
// 	filters: [
// 	  {
// 		fieldname: 'from_date',
// 		label: __('From Date'),
// 		fieldtype: 'Date',
// 		default: frappe.datetime.month_start() // or now_date() if you prefer
// 	  },
// 	  {
// 		fieldname: 'to_date',
// 		label: __('To Date'),
// 		fieldtype: 'Date',
// 		default: frappe.datetime.now_date()
// 	  }
// 	]
//   };
  
  
  // apps/kfppl_custom/kfppl_custom/kfppl_custom/report/sales_day_book_1/sales_day_book_1.js
frappe.query_reports['sales day book 1'] = {
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
  
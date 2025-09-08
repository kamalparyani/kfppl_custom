// Copyright (c) 2025, V12 Infotech and contributors
// For license information, please see license.txt

frappe.query_reports['day book 1'] = {
	filters: [
	  {
		fieldname: 'from_date',
		label: __('From Date'),
		fieldtype: 'Date',
		width: '80',
		default: frappe.datetime.now_datetime() // preserve your logic
	  },
	  {
		fieldname: 'to_date',
		label: __('To Date'),
		fieldtype: 'Date',
		width: '80',
		default: frappe.datetime.now_datetime() // preserve your logic
	  }
	]
  };
  
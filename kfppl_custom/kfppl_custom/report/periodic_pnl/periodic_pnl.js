// Copyright (c) 2026, V12 Infotech and contributors
// For license information, please see license.txt



frappe.query_reports["Periodic PNL"] = {
  "filters": [
    {
      fieldname: "from_date",
      label: "From Date",
      fieldtype: "Date",
      default: frappe.datetime.now_date(),
      reqd: 1
    },
    {
      fieldname: "to_date",
      label: "To Date",
      fieldtype: "Date",
      default: frappe.datetime.now_date(),
      reqd: 1
    },
    {
      fieldname: "cost_center",
      label: "Cost Center",
      fieldtype: "MultiSelectList",
      get_data: function (txt) {
        return frappe.db.get_link_options("Cost Center", txt);
      }
    }
  ]
};

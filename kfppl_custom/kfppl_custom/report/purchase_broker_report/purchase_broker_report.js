// Copyright (c) 2026, V12 Infotech and contributors
// For license information, please see license.txt
frappe.query_reports["Purchase Broker Report"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date"
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date"
    },
    {
      fieldname: "custom_purchase_partner",
      label: __("Purchase Partner"),
      fieldtype: "Link",
      options: "Purchase Partner"
    },
    {
      fieldname: "supplier",
      label: __("Supplier"),
      fieldtype: "Link",
      options: "Supplier"
    },
    {
      fieldname: "item_code",
      label: __("Item"),
      fieldtype: "Link",
      options: "Item"
    }
  ],

  onload: function (report) {
    // Set defaults to Current FY Start/End
    frappe.call({
      method: "erpnext.accounts.utils.get_fiscal_year",
      args: {
        date: frappe.datetime.get_today()
        // company not required in most setups; add if your FY differs by company
      },
      callback: function (r) {
        if (!r.message) return;

        // get_fiscal_year typically returns: [fy_name, start_date, end_date]
        const fy = r.message;
        const start_date = fy[1];
        const end_date = fy[2];

        // Only auto-set if user hasn't already chosen values
        const current_from = report.get_filter_value("from_date");
        const current_to = report.get_filter_value("to_date");

        if (!current_from) report.set_filter_value("from_date", start_date);
        if (!current_to) report.set_filter_value("to_date", end_date);
      }
    });
  }
};


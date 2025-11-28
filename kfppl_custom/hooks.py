app_name = "kfppl_custom"
app_title = "Kfppl Custom"
app_publisher = "V12 Infotech"
app_description = "Custom changes for kfppl"
app_email = "kamal@v12infotech.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kfppl_custom",
# 		"logo": "/assets/kfppl_custom/logo.png",
# 		"title": "Kfppl Custom",
# 		"route": "/kfppl_custom",
# 		"has_permission": "kfppl_custom.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kfppl_custom/css/kfppl_custom.css"
# app_include_js = "/assets/kfppl_custom/js/kfppl_custom.js"

# include js, css files in header of web template
# web_include_css = "/assets/kfppl_custom/css/kfppl_custom.css"
# web_include_js = "/assets/kfppl_custom/js/kfppl_custom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kfppl_custom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

doctype_js = {
    'Sales Invoice' : '/custom_folder/sales_invoice/sales_invoice.js',
    'Sales Order' : '/custom_folder/sales_order/sales_order.js',
    'Delivery Note' : '/custom_folder/delivery_note/delivery_note.js'
    }

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kfppl_custom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kfppl_custom.utils.jinja_methods",
# 	"filters": "kfppl_custom.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kfppl_custom.install.before_install"
# after_install = "kfppl_custom.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kfppl_custom.uninstall.before_uninstall"
# after_uninstall = "kfppl_custom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kfppl_custom.utils.before_app_install"
# after_app_install = "kfppl_custom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kfppl_custom.utils.before_app_uninstall"
# after_app_uninstall = "kfppl_custom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kfppl_custom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }
doc_events = {
    "Sales Invoice": {
        "validate": "kfppl_custom.custom_folder.sales_invoice.sales_invoice.set_payment_terms_template"
    },
    "Delivery Note": {
        "before_submit": "kfppl_custom.custom_folder.delivery_note.delivery_note.dn_credit_limit",
        "before_save": "kfppl_custom.custom_folder.delivery_note.delivery_note.dn_credit_limit"

    }
}


# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"kfppl_custom.tasks.all"
# 	],
# 	"daily": [
# 		"kfppl_custom.tasks.daily"
# 	],
# 	"hourly": [
# 		"kfppl_custom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kfppl_custom.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kfppl_custom.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kfppl_custom.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kfppl_custom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kfppl_custom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kfppl_custom.utils.before_request"]
# after_request = ["kfppl_custom.utils.after_request"]

# Job Events
# ----------
# before_job = ["kfppl_custom.utils.before_job"]
# after_job = ["kfppl_custom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"kfppl_custom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [{
        "doctype": "Custom Field",
        "filters": [
            ["module", "=", "Kfppl Custom"]
        ]
    }]
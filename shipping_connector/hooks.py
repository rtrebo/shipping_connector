from . import __version__ as app_version

app_name = "shipping_connector"
app_title = "Shipping Connector"
app_publisher = "INOOVA GmbH"
app_description = "Shipping Connector for ERPNext - GLS Integration with Shopify tracking sync"
app_email = "roland@inoova.it"
app_icon = "octicon octicon-package"
app_color = "#3498db"
app_license = "MIT"
required_apps = ["frappe/erpnext"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/shipping_connector/css/shipping_connector.css"
# app_include_js = "/assets/shipping_connector/js/shipping_connector.js"

# include js in doctype views
doctype_js = {
	"Delivery Note": "public/js/delivery_note.js",
}

# Installation
# ------------

after_install = "shipping_connector.install.after_install"
after_migrate = "shipping_connector.install.after_install"

# Document Events
# ---------------
# Hook on document methods and events

# Uncomment to auto-create shipment on DN submit
# doc_events = {
# 	"Delivery Note": {
# 		"on_submit": "shipping_connector.api.auto_create_shipment"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"shipping_connector.tasks.update_tracking_status",
	],
}

# Override whitelisted methods
# ----------------------------

# override_whitelisted_methods = {
# 	"original.method": "shipping_connector.overrides.method"
# }

# Fixtures
# --------

# fixtures = ["Custom Field"]

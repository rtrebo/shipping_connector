app_name = "shipping_connector"
app_title = "Shipping Connector"
app_publisher = "INOOVA GmbH"
app_description = "Shipping Connector for ERPNext - GLS Integration"
app_email = "roland@inoova.it"
app_license = "mit"

# Required Apps
# required_apps = ["erpnext"]

# Installation
after_install = "shipping_connector.install.after_install"
after_migrate = "shipping_connector.install.after_install"

# Document Events (optional - for auto-create shipment on submit)
# doc_events = {
#     "Delivery Note": {
#         "on_submit": "shipping_connector.api.auto_create_shipment"
#     }
# }

"""
Shipping Connector Installation
Creates Custom Fields for shipping integration on Delivery Note.
"""
import frappe


def after_install():
	"""Run after app installation and migration."""
	create_custom_fields()
	frappe.db.commit()
	print("Shipping Connector: Installation complete")


def create_custom_fields():
	"""Create Custom Fields on Delivery Note for shipping info."""

	fields = [
		{
			"dt": "Delivery Note",
			"fieldname": "shipping_section",
			"label": "Shipping",
			"fieldtype": "Section Break",
			"insert_after": "terms",
			"collapsible": 1,
		},
		{
			"dt": "Delivery Note",
			"fieldname": "shipping_carrier",
			"label": "Carrier",
			"fieldtype": "Select",
			"options": "\nGLS\nBRT\nDHL\nUPS\nOther",
			"insert_after": "shipping_section",
			"allow_on_submit": 1,
		},
		{
			"dt": "Delivery Note",
			"fieldname": "tracking_number",
			"label": "Tracking Number",
			"fieldtype": "Data",
			"insert_after": "shipping_carrier",
			"allow_on_submit": 1,
		},
		{
			"dt": "Delivery Note",
			"fieldname": "shipping_col_break",
			"fieldtype": "Column Break",
			"insert_after": "tracking_number",
		},
		{
			"dt": "Delivery Note",
			"fieldname": "shipping_status",
			"label": "Shipping Status",
			"fieldtype": "Select",
			"options": "\nLabel Created\nPicked Up\nIn Transit\nOut for Delivery\nDelivered\nReturned\nException",
			"insert_after": "shipping_col_break",
			"allow_on_submit": 1,
		},
		{
			"dt": "Delivery Note",
			"fieldname": "shipping_label_url",
			"label": "Label URL",
			"fieldtype": "Data",
			"insert_after": "shipping_status",
			"read_only": 1,
			"hidden": 1,
			"allow_on_submit": 1,
		},
	]

	for f in fields:
		field_name = f"{f['dt']}-{f['fieldname']}"
		if not frappe.db.exists("Custom Field", field_name):
			doc = frappe.get_doc({"doctype": "Custom Field", **f})
			doc.insert(ignore_permissions=True)
			print(f"Created Custom Field: {field_name}")
		else:
			print(f"Custom Field exists: {field_name}")

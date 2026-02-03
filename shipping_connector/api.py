"""
Shipping Connector API - GLS Integration
Whitelisted methods for creating shipments and syncing tracking.
"""
import frappe
from frappe import _


@frappe.whitelist()
def create_shipment(delivery_note: str) -> dict:
	"""
	Create a GLS shipment for a Delivery Note.
	
	Args:
		delivery_note: Name of the Delivery Note
		
	Returns:
		dict with tracking_number and label_url
	"""
	dn = frappe.get_doc("Delivery Note", delivery_note)

	if dn.docstatus != 1:
		frappe.throw(_("Delivery Note must be submitted"))

	if dn.tracking_number:
		frappe.throw(_("Shipment already exists: {0}").format(dn.tracking_number))

	# Get settings from site_config
	settings = get_gls_settings()

	# Build request payload
	request_data = build_shipment_request(dn)

	# Call GLS API
	result = call_gls_api(request_data, settings)

	# Update Delivery Note with tracking info
	frappe.db.set_value(
		"Delivery Note",
		delivery_note,
		{
			"tracking_number": result["tracking_number"],
			"shipping_label_url": result.get("label_url"),
			"shipping_status": "Label Created",
			"shipping_carrier": "GLS",
		},
	)

	# Sync tracking to Shopify if order came from Shopify
	shopify_order_id = dn.get("shopify_order_id")
	if shopify_order_id:
		sync_tracking_to_shopify(dn, result["tracking_number"])

	frappe.msgprint(_("Shipment created: {0}").format(result["tracking_number"]))

	return result


def get_gls_settings() -> dict:
	"""
	Get GLS API credentials from site_config.
	
	Expected keys in site_config.json:
	- gls_api_url: API base URL
	- gls_contact_id: GLS contact/user ID
	- gls_password: API password
	- gls_customer_id: GLS customer number
	- gls_sandbox: True for sandbox mode (default: True)
	"""
	return {
		"api_url": frappe.conf.get("gls_api_url", "https://api.gls-group.eu/public/v1"),
		"contact_id": frappe.conf.get("gls_contact_id"),
		"password": frappe.conf.get("gls_password"),
		"customer_id": frappe.conf.get("gls_customer_id"),
		"sandbox": frappe.conf.get("gls_sandbox", True),
	}


def build_shipment_request(dn) -> dict:
	"""
	Build GLS API request from Delivery Note data.
	
	Args:
		dn: Delivery Note document
		
	Returns:
		dict formatted for GLS Shipment API
	"""
	# Get shipping address
	if not dn.shipping_address_name:
		frappe.throw(_("Shipping address is required"))

	address = frappe.get_doc("Address", dn.shipping_address_name)

	# Calculate total weight (minimum 1kg)
	weight = sum([item.total_weight or 0 for item in dn.items])
	weight = max(weight, 1.0)

	# Get country code
	country_code = "IT"
	if address.country:
		country_code = frappe.db.get_value("Country", address.country, "code") or "IT"

	# Build recipient address
	recipient = {
		"name1": address.address_title or dn.customer_name,
		"street1": address.address_line1,
		"zipCode": address.pincode,
		"city": address.city,
		"countryCode": country_code.upper(),
	}

	# Add phone if available
	if address.phone:
		recipient["phone"] = address.phone
	if address.email_id:
		recipient["email"] = address.email_id

	# Add address line 2 if present
	if address.address_line2:
		recipient["street2"] = address.address_line2

	return {
		"shipperId": frappe.conf.get("gls_customer_id"),
		"references": [dn.name],
		"addresses": {"delivery": recipient},
		"parcels": [
			{
				"weight": weight,
				"comment": dn.get("shopify_order_number") or dn.name,
			}
		],
	}


def call_gls_api(data: dict, settings: dict) -> dict:
	"""
	Call GLS Shipment API.
	
	If credentials are not configured, returns demo data.
	
	Args:
		data: Request payload
		settings: GLS API settings
		
	Returns:
		dict with tracking_number and label_url
	"""
	import requests
	from requests.auth import HTTPBasicAuth

	# Demo mode if not configured
	if not settings.get("contact_id"):
		import random

		frappe.msgprint(
			_("GLS API not configured - using demo mode"),
			indicator="orange",
			alert=True,
		)
		return {
			"tracking_number": f"DEMO{random.randint(100000000, 999999999)}",
			"label_url": None,
		}

	# Build URL
	base_url = settings["api_url"]
	if settings.get("sandbox"):
		base_url = "https://api.gls-group.eu/public/v1/sandbox"

	url = f"{base_url}/shipments"

	try:
		response = requests.post(
			url,
			json=data,
			auth=HTTPBasicAuth(settings["contact_id"], settings["password"]),
			timeout=30,
		)
		response.raise_for_status()

		result = response.json()
		parcel = result.get("parcels", [{}])[0]

		return {
			"tracking_number": parcel.get("trackingNumber"),
			"label_url": parcel.get("labelUrl"),
		}

	except requests.exceptions.RequestException as e:
		frappe.log_error(
			message=str(e),
			title="GLS API Error",
		)
		frappe.throw(_("GLS API Error: {0}").format(str(e)))


def sync_tracking_to_shopify(dn, tracking_number: str) -> None:
	"""
	Sync tracking number to Shopify by creating a fulfillment.
	
	Uses the Shopify Admin API to:
	1. Get fulfillment orders for the Shopify order
	2. Create a fulfillment with tracking info
	
	Requires ecommerce_integrations app to be installed and configured.
	
	Args:
		dn: Delivery Note document
		tracking_number: Tracking number to sync
	"""
	try:
		from ecommerce_integrations.shopify.constants import SETTING_DOCTYPE
		
		setting = frappe.get_doc(SETTING_DOCTYPE)
		if not setting.enable_shopify:
			return
		
		order_id = dn.shopify_order_id
		if not order_id:
			return
		
		# Build API URL and headers
		shop_url = setting.shopify_url.rstrip("/")
		api_version = "2024-01"
		headers = {
			"X-Shopify-Access-Token": setting.get_password("password"),
			"Content-Type": "application/json",
		}
		
		import requests
		
		# Step 1: Get fulfillment orders for this order
		fo_url = f"https://{shop_url}/admin/api/{api_version}/orders/{order_id}/fulfillment_orders.json"
		fo_response = requests.get(fo_url, headers=headers, timeout=30)
		fo_response.raise_for_status()
		
		fulfillment_orders = fo_response.json().get("fulfillment_orders", [])
		if not fulfillment_orders:
			frappe.logger().warning(f"No fulfillment orders found for Shopify order {order_id}")
			return
		
		# Get the first open fulfillment order
		fulfillment_order = None
		for fo in fulfillment_orders:
			if fo.get("status") == "open":
				fulfillment_order = fo
				break
		
		if not fulfillment_order:
			frappe.logger().info(f"No open fulfillment orders for Shopify order {order_id}")
			return
		
		# Step 2: Create fulfillment with tracking
		fulfillment_url = f"https://{shop_url}/admin/api/{api_version}/fulfillments.json"
		fulfillment_data = {
			"fulfillment": {
				"line_items_by_fulfillment_order": [
					{"fulfillment_order_id": fulfillment_order["id"]}
				],
				"tracking_info": {
					"number": tracking_number,
					"company": "GLS",
					"url": f"https://gls-group.com/IT/it/servizi-online/tracking?match={tracking_number}",
				},
				"notify_customer": True,
			}
		}
		
		ff_response = requests.post(fulfillment_url, headers=headers, json=fulfillment_data, timeout=30)
		ff_response.raise_for_status()
		
		frappe.logger().info(f"Shopify fulfillment created for order {order_id}: {tracking_number}")
		frappe.msgprint(_("Tracking synced to Shopify"), indicator="green")

	except ImportError:
		frappe.logger().info("ecommerce_integrations not installed - skipping Shopify sync")

	except Exception as e:
		frappe.log_error(
			message=str(e),
			title="Shopify Tracking Sync Error",
		)
		frappe.msgprint(
			_("Note: Shopify sync pending - manual update may be needed"),
			indicator="orange",
		)


@frappe.whitelist()
def get_tracking_status(tracking_number: str) -> dict:
	"""
	Get current tracking status for a shipment.
	
	Args:
		tracking_number: The tracking number to check
		
	Returns:
		dict with status information
	"""
	# Placeholder - GLS tracking requires partner API access
	return {
		"tracking_number": tracking_number,
		"status": "unknown",
		"message": "Tracking status lookup not yet implemented",
	}


@frappe.whitelist()
def bulk_create_shipments(delivery_notes: list) -> dict:
	"""
	Create shipments for multiple Delivery Notes.
	
	Args:
		delivery_notes: List of Delivery Note names
		
	Returns:
		dict with success/error counts and details
	"""
	if isinstance(delivery_notes, str):
		import json
		delivery_notes = json.loads(delivery_notes)

	results = {"success": [], "errors": []}

	for dn_name in delivery_notes:
		try:
			result = create_shipment(dn_name)
			results["success"].append(
				{"delivery_note": dn_name, "tracking_number": result["tracking_number"]}
			)
		except Exception as e:
			results["errors"].append({"delivery_note": dn_name, "error": str(e)})

	return results

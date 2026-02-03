"""
Scheduled tasks for Shipping Connector.
"""
import frappe


def update_tracking_status():
	"""
	Hourly task: Update tracking status for all shipments that are not delivered.
	"""
	# Get all DNs with tracking numbers that are not delivered
	delivery_notes = frappe.get_all(
		"Delivery Note",
		filters={
			"docstatus": 1,
			"tracking_number": ["is", "set"],
			"shipping_status": ["not in", ["Delivered", "Returned", ""]],
		},
		fields=["name", "tracking_number", "shipping_carrier"],
		limit=100,
	)

	if not delivery_notes:
		return

	for dn in delivery_notes:
		try:
			status = get_tracking_status_from_carrier(
				dn.shipping_carrier or "GLS",
				dn.tracking_number
			)
			if status and status != dn.get("shipping_status"):
				frappe.db.set_value("Delivery Note", dn.name, "shipping_status", status)
				frappe.logger().info(f"Updated tracking status for {dn.name}: {status}")
		except Exception as e:
			frappe.log_error(
				message=str(e),
				title=f"Tracking Update Error: {dn.name}"
			)

	frappe.db.commit()


def get_tracking_status_from_carrier(carrier: str, tracking_number: str) -> str | None:
	"""
	Get tracking status from carrier API.
	Currently only GLS is implemented.
	"""
	if carrier == "GLS":
		return get_gls_tracking_status(tracking_number)
	
	# Other carriers not yet implemented
	return None


def get_gls_tracking_status(tracking_number: str) -> str | None:
	"""
	Get tracking status from GLS.
	Note: GLS public tracking API requires scraping or partner API access.
	This is a placeholder for future implementation.
	"""
	# TODO: Implement GLS tracking API
	# GLS has a partner API that requires authentication
	# For now, return None to skip updates
	return None

"""
Shipping Connector API - GLS Integration
"""
import frappe
from frappe import _


@frappe.whitelist()
def create_shipment(delivery_note: str) -> dict:
    """Create a GLS shipment for a Delivery Note."""
    
    dn = frappe.get_doc("Delivery Note", delivery_note)
    
    if dn.docstatus != 1:
        frappe.throw(_("Delivery Note must be submitted"))
    
    if dn.tracking_number:
        frappe.throw(_("Shipment already exists: {0}").format(dn.tracking_number))
    
    # Get settings
    settings = _get_gls_settings()
    
    # Build request
    request_data = _build_shipment_request(dn)
    
    # Call GLS API
    result = _call_gls_api(request_data, settings)
    
    # Update DN
    frappe.db.set_value("Delivery Note", delivery_note, {
        "tracking_number": result["tracking_number"],
        "shipping_label_url": result.get("label_url"),
        "shipping_status": "Label Created",
        "shipping_carrier": "GLS"
    })
    
    # Sync to Shopify
    if dn.shopify_order_id:
        _sync_to_shopify(dn, result["tracking_number"])
    
    frappe.msgprint(_("Shipment created: {0}").format(result["tracking_number"]))
    
    return result


def _get_gls_settings() -> dict:
    """Get GLS API credentials from site config."""
    return {
        "api_url": frappe.conf.get("gls_api_url", "https://api.gls-group.eu/public/v1"),
        "contact_id": frappe.conf.get("gls_contact_id"),
        "password": frappe.conf.get("gls_password"),
        "customer_id": frappe.conf.get("gls_customer_id"),
        "sandbox": frappe.conf.get("gls_sandbox", True)
    }


def _build_shipment_request(dn) -> dict:
    """Build GLS API request from Delivery Note."""
    
    address = frappe.get_doc("Address", dn.shipping_address_name) if dn.shipping_address_name else None
    if not address:
        frappe.throw(_("Shipping address required"))
    
    weight = sum([item.total_weight or 0 for item in dn.items]) or 1.0
    
    return {
        "shipperId": frappe.conf.get("gls_customer_id"),
        "references": [dn.name],
        "addresses": {
            "delivery": {
                "name1": address.address_title or dn.customer_name,
                "street1": address.address_line1,
                "zipCode": address.pincode,
                "city": address.city,
                "countryCode": frappe.db.get_value("Country", address.country, "code") or "IT"
            }
        },
        "parcels": [{
            "weight": weight,
            "comment": dn.shopify_order_number or dn.name
        }]
    }


def _call_gls_api(data: dict, settings: dict) -> dict:
    """Call GLS API. Returns demo data if not configured."""
    
    if not settings.get("contact_id"):
        # Demo mode
        import random
        frappe.msgprint(_("GLS not configured - Demo mode"), indicator="orange")
        return {
            "tracking_number": f"DEMO{random.randint(100000000, 999999999)}",
            "label_url": None
        }
    
    import requests
    from requests.auth import HTTPBasicAuth
    
    url = settings["api_url"]
    if settings.get("sandbox"):
        url = "https://api.gls-group.eu/public/v1/sandbox"
    
    try:
        resp = requests.post(
            f"{url}/shipments",
            json=data,
            auth=HTTPBasicAuth(settings["contact_id"], settings["password"]),
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
        parcel = result.get("parcels", [{}])[0]
        return {
            "tracking_number": parcel.get("trackingNumber"),
            "label_url": parcel.get("labelUrl")
        }
    except Exception as e:
        frappe.log_error(str(e), "GLS API Error")
        frappe.throw(_("GLS Error: {0}").format(str(e)))


def _sync_to_shopify(dn, tracking_number: str):
    """Sync tracking to Shopify."""
    try:
        from ecommerce_integrations.shopify.fulfillment import create_fulfillment
        create_fulfillment(dn.shopify_order_id, tracking_number, "GLS")
    except Exception as e:
        frappe.log_error(str(e), "Shopify Sync Error")


@frappe.whitelist()
def get_tracking_status(tracking_number: str) -> dict:
    """Get tracking status from GLS."""
    return {"status": "unknown", "tracking_number": tracking_number}

# Shipping Connector

Shipping integration for ERPNext with GLS carrier support and Shopify tracking sync.

## Features

- **GLS Integration**: Create shipments directly from Delivery Notes
- **Shopify Sync**: Automatically sync tracking numbers to Shopify fulfillments
- **Multi-Carrier Support**: Extensible architecture for BRT, DHL, UPS
- **Tracking Updates**: Scheduled task to update shipment status

## Installation

### Frappe Cloud

1. Go to your bench → Apps → Get App
2. Enter: `https://github.com/rtrebo/shipping_connector`
3. Install on your site

### Local Development

```bash
cd frappe-bench
bench get-app https://github.com/rtrebo/shipping_connector
bench --site your-site install-app shipping_connector
```

## Configuration

Add the following to your `site_config.json`:

```json
{
  "gls_contact_id": "your-contact-id",
  "gls_password": "your-password",
  "gls_customer_id": "your-customer-number",
  "gls_sandbox": true
}
```

Set `gls_sandbox` to `false` for production.

## Usage

### Creating a Shipment

1. Open a submitted Delivery Note
2. Click **Shipping → Create Shipment**
3. The tracking number will be saved and synced to Shopify (if applicable)

### Tracking

- Click **Shipping → Track Package** to open the carrier's tracking page
- Tracking status is updated hourly via scheduled task

## Custom Fields

The app creates these Custom Fields on Delivery Note:

| Field | Type | Description |
|-------|------|-------------|
| shipping_carrier | Select | GLS, BRT, DHL, UPS, Other |
| tracking_number | Data | Shipment tracking number |
| shipping_status | Select | Label Created, In Transit, Delivered, etc. |
| shipping_label_url | Data | URL to download shipping label |

## API

### create_shipment

```python
from shipping_connector.api import create_shipment
result = create_shipment("DN-00001")
# {'tracking_number': '1234567890', 'label_url': '...'}
```

### bulk_create_shipments

```python
from shipping_connector.api import bulk_create_shipments
results = bulk_create_shipments(["DN-00001", "DN-00002"])
```

## Requirements

- Frappe Framework >= 15.0
- ERPNext >= 15.0
- ecommerce_integrations (optional, for Shopify sync)

## License

MIT

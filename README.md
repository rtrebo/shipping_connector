# Shipping Connector

ERPNext app for shipping integration, starting with GLS.

## Features

- Create Shipment button on Delivery Note
- GLS API integration
- Auto-sync tracking to Shopify
- Demo mode for testing

## Installation

```bash
bench get-app https://github.com/rtrebo/shipping_connector
bench --site your-site install-app shipping_connector
```

## Configuration

Add to `site_config.json`:

```json
{
  "gls_contact_id": "YOUR_CONTACT_ID",
  "gls_password": "YOUR_PASSWORD", 
  "gls_customer_id": "YOUR_CUSTOMER_ID",
  "gls_sandbox": true
}
```

## License

MIT

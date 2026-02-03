"""
Shipping Connector Installation
Creates Custom Fields and Client Scripts for shipping integration.
"""
import frappe


def after_install():
    """Run after app installation."""
    create_custom_fields()
    create_client_script()
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
            "collapsible": 1
        },
        {
            "dt": "Delivery Note",
            "fieldname": "shipping_carrier",
            "label": "Carrier",
            "fieldtype": "Data",
            "insert_after": "shipping_section",
            "read_only": 1,
        },
        {
            "dt": "Delivery Note",
            "fieldname": "tracking_number",
            "label": "Tracking Number",
            "fieldtype": "Data",
            "insert_after": "shipping_carrier",
            "read_only": 1,
        },
        {
            "dt": "Delivery Note",
            "fieldname": "shipping_col_break",
            "fieldtype": "Column Break",
            "insert_after": "tracking_number"
        },
        {
            "dt": "Delivery Note",
            "fieldname": "shipping_status",
            "label": "Shipping Status",
            "fieldtype": "Data",
            "insert_after": "shipping_col_break",
            "read_only": 1,
        },
        {
            "dt": "Delivery Note",
            "fieldname": "shipping_label_url",
            "label": "Label URL",
            "fieldtype": "Data",
            "insert_after": "shipping_status",
            "read_only": 1,
            "hidden": 1
        }
    ]
    
    for f in fields:
        if not frappe.db.exists("Custom Field", {"dt": f["dt"], "fieldname": f["fieldname"]}):
            doc = frappe.get_doc({"doctype": "Custom Field", **f})
            doc.insert(ignore_permissions=True)
            print(f"Created: {f['dt']}-{f['fieldname']}")


def create_client_script():
    """Create Client Script for shipping button on Delivery Note."""
    
    script_name = "DN Shipping Button"
    
    if frappe.db.exists("Client Script", script_name):
        print(f"Client Script '{script_name}' already exists")
        return
    
    script = '''
frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1 && !frm.doc.tracking_number) {
            frm.add_custom_button(__('Create Shipment'), function() {
                frappe.call({
                    method: 'shipping_connector.api.create_shipment',
                    args: { delivery_note: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Creating shipment...'),
                    callback: function(r) {
                        if (r.message) {
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Shipping'));
        }
        
        if (frm.doc.tracking_number) {
            frm.add_custom_button(__('Track'), function() {
                let url = 'https://gls-group.com/IT/it/servizi-online/tracking?match=' + frm.doc.tracking_number;
                window.open(url, '_blank');
            }, __('Shipping'));
            
            frm.dashboard.add_indicator(__('Tracking: {0}', [frm.doc.tracking_number]), 'blue');
        }
    }
});
'''
    
    doc = frappe.get_doc({
        "doctype": "Client Script",
        "name": script_name,
        "dt": "Delivery Note",
        "view": "Form",
        "enabled": 1,
        "script": script
    })
    doc.insert(ignore_permissions=True)
    print(f"Created Client Script: {script_name}")

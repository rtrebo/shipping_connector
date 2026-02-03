frappe.ui.form.on("Delivery Note", {
	refresh: function(frm) {
		// Only show button on submitted DNs without tracking
		if (frm.doc.docstatus === 1 && !frm.doc.tracking_number) {
			frm.add_custom_button(__("Create Shipment"), function() {
				frappe.call({
					method: "shipping_connector.api.create_shipment",
					args: { delivery_note: frm.doc.name },
					freeze: true,
					freeze_message: __("Creating shipment..."),
					callback: function(r) {
						if (r.message) {
							frappe.show_alert({
								message: __("Shipment created: {0}", [r.message.tracking_number]),
								indicator: "green"
							});
							frm.reload_doc();
						}
					},
					error: function(r) {
						frappe.msgprint({
							title: __("Error"),
							indicator: "red",
							message: r.message || __("Failed to create shipment")
						});
					}
				});
			}, __("Shipping"));
		}

		// Show tracking button if we have a tracking number
		if (frm.doc.tracking_number) {
			frm.add_custom_button(__("Track Package"), function() {
				let carrier = frm.doc.shipping_carrier || "GLS";
				let url = get_tracking_url(carrier, frm.doc.tracking_number);
				window.open(url, "_blank");
			}, __("Shipping"));

			// Add tracking indicator
			frm.dashboard.add_indicator(
				__("Tracking: {0}", [frm.doc.tracking_number]),
				"blue"
			);
		}

		// Show label download if available
		if (frm.doc.shipping_label_url) {
			frm.add_custom_button(__("Download Label"), function() {
				window.open(frm.doc.shipping_label_url, "_blank");
			}, __("Shipping"));
		}
	}
});

function get_tracking_url(carrier, tracking_number) {
	const urls = {
		"GLS": "https://gls-group.com/IT/it/servizi-online/tracking?match=" + tracking_number,
		"BRT": "https://vas.brt.it/vas/sped_det_boll.hsm?referer=sped_numspe.htm&bession=&Ession=&bession=&Ession=&ESSION=&SESSION=&Session=&numSped=" + tracking_number,
		"DHL": "https://www.dhl.com/it-it/home/tracking.html?tracking-id=" + tracking_number,
		"UPS": "https://www.ups.com/track?loc=it_IT&tracknum=" + tracking_number,
	};
	return urls[carrier] || urls["GLS"];
}

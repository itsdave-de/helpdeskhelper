// Copyright (c) 2024, itsdave GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on('Helpdesk App Settings', {
	refresh: function(frm) {
		// Add "App Registrieren" button
		frm.add_custom_button(__('App Registrieren'), function() {
			show_app_registration_dialog(frm);
		});
	}
});

function show_app_registration_dialog(frm) {
	let dialog = new frappe.ui.Dialog({
		title: __('App Registrieren'),
		fields: [
			{
				fieldname: 'user',
				fieldtype: 'Link',
				label: __('User'),
				options: 'User',
				reqd: 1,
				onchange: function() {
					const user = dialog.get_value('user');
					if (user) {
						generate_qr_code_for_user(dialog, user);
					} else {
						// Clear QR code if user is deselected
						dialog.fields_dict.qr_code_html.$wrapper.html('');
					}
				}
			},
			{
				fieldname: 'qr_code_html',
				fieldtype: 'HTML',
				label: __('QR Code')
			}
		],
		primary_action_label: __('Close'),
		primary_action: function() {
			dialog.hide();
		}
	});

	dialog.show();
}

function generate_qr_code_for_user(dialog, user) {
	// Show loading message
	dialog.fields_dict.qr_code_html.$wrapper.html('<p>Loading API credentials...</p>');

	// Get decrypted API credentials using custom server method
	frappe.call({
		method: 'helpdeskhelper.helpdeskhelper.doctype.helpdesk_app_settings.helpdesk_app_settings.get_user_api_credentials',
		args: {
			user: user
		},
		callback: function(r) {
			if (r.message && r.message.api_key && r.message.api_secret) {
				// User already has API credentials, use existing ones (now properly decrypted)
				const api_key = r.message.api_key;
				const api_secret = r.message.api_secret;
				const site_url = window.location.origin;

				// Create JSON data for QR code in the required format
				const qr_data = {
					apiKey: api_key,
					apiSecret: api_secret,
					url: site_url
				};

				const qr_json = JSON.stringify(qr_data);

				// Generate QR code
				display_qr_code(dialog, qr_json, qr_data, user);
			} else {
				// User doesn't have API credentials, ask for confirmation to generate
				dialog.fields_dict.qr_code_html.$wrapper.html('');
				frappe.confirm(
					__('Der Benutzer {0} hat noch keine API-Schlüssel. Möchten Sie neue Schlüssel generieren?', [user]),
					function() {
						// User confirmed, generate new keys
						generate_new_keys_for_user(dialog, user);
					},
					function() {
						// User declined
						dialog.fields_dict.qr_code_html.$wrapper.html('<p style="color: #888;">Keine API-Schlüssel generiert.</p>');
					}
				);
			}
		},
		error: function(r) {
			frappe.msgprint(__('Error retrieving API credentials'));
			dialog.fields_dict.qr_code_html.$wrapper.html('<p style="color: red;">Error loading credentials</p>');
		}
	});
}

function generate_new_keys_for_user(dialog, user) {
	dialog.fields_dict.qr_code_html.$wrapper.html('<p>Generating new API credentials...</p>');

	frappe.call({
		method: 'frappe.core.doctype.user.user.generate_keys',
		args: {
			user: user
		},
		callback: function(r) {
			if (r.message && r.message.api_secret) {
				// generate_keys only returns api_secret, we need to fetch api_key separately
				const api_secret = r.message.api_secret;

				// Fetch the api_key from the User document
				frappe.call({
					method: 'frappe.client.get_value',
					args: {
						doctype: 'User',
						filters: { name: user },
						fieldname: ['api_key']
					},
					callback: function(r2) {
						if (r2.message && r2.message.api_key) {
							const api_key = r2.message.api_key;
							const site_url = window.location.origin;

							// Create JSON data for QR code in the required format
							const qr_data = {
								apiKey: api_key,
								apiSecret: api_secret,
								url: site_url
							};

							const qr_json = JSON.stringify(qr_data);

							// Generate QR code
							display_qr_code(dialog, qr_json, qr_data, user);
						} else {
							frappe.msgprint(__('Failed to retrieve API key'));
							dialog.fields_dict.qr_code_html.$wrapper.html('<p style="color: red;">Error retrieving API key</p>');
						}
					}
				});
			} else {
				frappe.msgprint(__('Failed to generate API credentials'));
				dialog.fields_dict.qr_code_html.$wrapper.html('<p style="color: red;">Error generating credentials</p>');
			}
		},
		error: function(r) {
			frappe.msgprint(__('Error generating API credentials'));
			dialog.fields_dict.qr_code_html.$wrapper.html('<p style="color: red;">Error generating QR code</p>');
		}
	});
}

function display_qr_code(dialog, qr_json, qr_data, user) {
	// Create container for QR code
	const qr_container_id = 'qrcode_' + frappe.utils.get_random(6);
	const html = `
		<div style="text-align: center; padding: 20px;">
			<div id="${qr_container_id}" style="display: inline-block;"></div>
			<div style="margin-top: 20px;">
				<h5>Configuration Details:</h5>
				<div style="text-align: left; background-color: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; overflow-x: auto;">
					<strong>User:</strong> ${user}<br>
					<strong>URL:</strong> ${qr_data.url}<br>
					<strong>API Key:</strong> ${qr_data.apiKey}<br>
					<strong>API Secret:</strong> ${qr_data.apiSecret.substring(0, 20)}...
				</div>
				<div style="margin-top: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 4px; font-size: 11px;">
					<strong>QR Code JSON:</strong>
					<pre style="margin: 5px 0 0 0; font-size: 10px;">${JSON.stringify(qr_data, null, 2)}</pre>
				</div>
			</div>
		</div>
	`;

	dialog.fields_dict.qr_code_html.$wrapper.html(html);

	// Load QRCode library from CDN if not already loaded
	if (typeof QRCode === 'undefined') {
		const script = document.createElement('script');
		script.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';
		script.onload = function() {
			generate_qr_code_element(qr_container_id, qr_json);
		};
		script.onerror = function() {
			dialog.fields_dict.qr_code_html.$wrapper.html('<p style="color: red;">Error loading QR code library.</p>');
		};
		document.head.appendChild(script);
	} else {
		generate_qr_code_element(qr_container_id, qr_json);
	}
}

function generate_qr_code_element(container_id, qr_json) {
	try {
		new QRCode(document.getElementById(container_id), {
			text: qr_json,
			width: 256,
			height: 256,
			colorDark: '#000000',
			colorLight: '#ffffff',
			correctLevel: QRCode.CorrectLevel.H
		});
	} catch (e) {
		console.error('QRCode generation error:', e);
		document.getElementById(container_id).innerHTML = '<p style="color: red;">Error generating QR code. Please try again.</p>';
	}
}

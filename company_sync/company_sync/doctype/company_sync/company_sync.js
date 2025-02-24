// Copyright (c) 2024, Dante Devenir and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company Sync", {
	setup(frm) {
		frm.toggle_display("section_sync_preview", false);
		console.log("Setup Step")
		frappe.realtime.on("company_sync_refresh", ({ percentage, company_sync }) => {		
			// Validar que el sync corresponda al documento actual
			if (company_sync !== frm.doc.name) return;
			
			updateProgressBar(frm, percentage);
			//reloadDocument(frm);
		})
		frappe.realtime.on("company_sync_error_log", ({ error_log, company_sync }) => {
			console.log(error_log)
			console.log(company_sync)
			console.log(frm.doc.name)

			if (company_sync !== frm.doc.name) return;
			
			render_sync_log(frm);
			//reloadDocument(frm);
		})
	},
	onload(frm) {
		if (frm.is_new()) {
			frm.toggle_display("section_sync_preview", false);
		}
	},
	refresh(frm) {
        frm.toggle_display("section_sync_preview", false);
        frm.trigger("update_primary_action");
		frm.trigger("render_sync_log");
    },
    onload_post_render(frm) {
		frm.trigger("update_primary_action");
	},
    update_primary_action(frm) {
		if (frm.is_dirty()) {
			frm.enable_save();
			return;
		}
		frm.disable_save();
		if (frm.doc.status !== "Success") {
			if (!frm.is_new()) {
				let label = frm.doc.status === "Pending" ? __("Start Sync") : __("Retry");
				frm.page.set_primary_action(label, () => frm.events.start_sync(frm));
			} else {
				frm.page.set_primary_action(__("Save"), () => frm.save());
			}
		}
	},
	start_sync(frm) {
		frm.toggle_display("section_sync_preview", true);
		frm.call({
			method: "form_start_sync",
			args: { company_sync: frm.doc.name },
			btn: frm.page.btn_primary,
		}).then((r) => {
			if (r.message === true) {
				frm.disable_save();
			}
		});
	},
	render_sync_log(frm) {
		console.log("Render Sync Log")
		console.log(frm.doc.name)
		frm.call({
			doc: frm.doc,
			method: "get_sync_logs",
			args: { company_sync: frm.doc.name },
		}).then((r) => {
			if (r.message === true) {
				frm.disable_save();
				let logs = r.message;
				console.log("logs!!!")
				let rows = logs.map((log) => {
					return log;
				});
				frm.get_field("import_log_preview").$wrapper.html(`
					<table class="table table-bordered">
						<tr class="text-muted">
							<th width="20%">${__("Member ID")}</th>
							<th width="80%">${__("Message")}</th>
						</tr>
						${rows}
					</table>
				`);
			}
		});
	},
	show_sync_log(frm) {
		frm.toggle_display("section_sync_log_preview", false);

		if (frm.is_new() || frm.import_in_progress) {
			return;
		}

		frappe.call({
			method: "frappe.client.get_count",
			args: {
				doctype: "Company Sync Log",
				filters: {
					data_import: frm.doc.name,
				},
			},
			callback: function (r) {
				let count = r.message;
				if (count < 5000) {
					frm.trigger("render_import_log");
				} else {
					frm.toggle_display("section_sync_log_preview", false);
					//frm.add_custom_button(__("Export Import Log"), () =>
					//	frm.trigger("export_import_log")
					//);
				}
			},
		});
	},
});

function updateProgressBar(frm, percentage) {
	const $wrapper = frm.get_field("sync_preview").$wrapper;
	$wrapper.empty();
	
	const $progress = $('<div class="progress">').appendTo($wrapper);
	$('<div class="progress-bar progress-bar-striped progress-bar-animated bg-primary">')
		.attr({
			'role': 'progressbar',
			'style': `width: ${percentage}%`,
			'aria-valuenow': percentage,
			'aria-valuemin': '0', 
			'aria-valuemax': '100'
		})
		.text(`${percentage}%`)
		.appendTo($progress);
}

function reloadDocument(frm) {
	frappe.model.with_doc("Company Sync", frm.doc.name)
		.then(() => frm.reload_doc());
}

// Copyright (c) 2024, Dante Devenir and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company Sync Scheduler", {
	setup(frm) {
		frappe.realtime.on("company_sync_refresh", ({ percentage, company_sync }) => {		
			// Validar que el sync corresponda al documento actual
			if (company_sync !== frm.doc.name) return;
			
			updateProgressBar(frm, percentage);
			//reloadDocument(frm);
		})
		frappe.realtime.on("company_sync_error_log", ({ error_log, company_sync, memberID, company, broker }) => {
			console.log(company_sync)
			console.log(frm.doc.name)

			if (company_sync !== frm.doc.name) return;
			
			//render_sync_log(frm);
			//reloadDocument(frm);

			frm.toggle_display("section_sync_log_preview", true);
			const $field = frm.get_field("sync_log_preview").$wrapper;

			// Mapear cada log para crear una fila de la tabla
			let newRow = `<tr>
				<td>${memberID}</td>
				<td>${error_log}</td>
			</tr>`;

			// Verificar si ya existe la tabla
			let $table = $field.find("table");
			if (!$table.length) {
				// Si la tabla no existe, crearla con el encabezado
				$table = $(`
					<table class="table table-bordered">
						<tr class="text-muted">
							<th width="20%">${__("Member ID")}</th>
							<th width="80%">${__("Message")}</th>
						</tr>
					</table>
				`);
				$field.append($table);
			}
		
			// Agregar la nueva fila a la tabla existente
			$table.append(newRow);
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
		frm.call({
			method: "form_start_sync",
			args: { company_sync_scheduler: frm.doc.name },
			btn: frm.page.btn_primary,
		}).then((r) => {
			if (r.message === true) {
				frm.disable_save();
			}
		});
		frm.toggle_display("section_sync_preview", true);
	},
	render_sync_log(frm) {
		console.log("Render Sync Log")
		console.log(frm.doc.name)
		if (frm.is_new()) {
			return;
		}
		frappe.call({
			method: "company_sync.company_sync.doctype.company_sync_scheduler.company_sync_scheduler.get_sync_logs",
			args: { company_sync_scheduler: frm.doc.name },
			callback: function (r) {
				console.log(r)
				console.log(r.message.length)
				if (r.message.length === 0) {
					frm.toggle_display("section_sync_log_preview", false);
					return;
				}
				frm.toggle_display("section_sync_log_preview", true);
				const $wrapper = frm.get_field("sync_log_preview").$wrapper;
				$wrapper.empty();

				frm.disable_save();
				let logs = r.message;
				console.log(r)

				const memberIdMap = {};

				// Mapear cada log para crear una fila de la tabla
				let rows = logs.map((log, index) => {
					const selectId = `review-select-${index}`;
					// Guardamos la correspondencia en el objeto
					memberIdMap[selectId] = log.memberid;
					return `<tr>
						<td>${log.memberid}</td>
						<td>${log.messages}</td>
						<td>
						<div class="control-input-wrapper">
							<div class="control-input flex align-center">
								<select id="${selectId}" type="text" autocomplete="off" class="input-with-feedback form-control ellipsis review-select">
									<option></option>
									<option value="Create Issue" ${log.review === 'Create Issue' ? 'selected' : ''} >Create Issue</option>
									<option value="Portal Error" ${log.review === 'Portal Error' ? 'selected' : ''} >Portal Error</option>
									<option value="Sync Error" ${log.review === 'Sync Error' ? 'selected' : ''} >Sync Error</option>
								</select>
								<div class="select-icon ">
									<svg class="icon  icon-sm" style="" aria-hidden="true">
										<use class="" href="#icon-select"></use>
									</svg>
								</div>
							</div>
							<div class="control-value like-disabled-input" style="display: none;">MySQL</div>
							<p class="help-box small text-muted"></p>
						</div>
						</td>
					</tr>`;
				}).join('');

				$(`
					<table class="table table-bordered">
						<tr class="text-muted">
						<th width="20%">${__("Member ID")}</th>
						<th width="65%">${__("Message")}</th>
						<th width="15%">${__("Review")}</th>
						</tr>
						${rows}
					</table>
				`).appendTo($wrapper);

				console.log(memberIdMap)

				$wrapper.on('change', '.review-select', function() {
					let newValue = $(this).val();
					// Obtener el id único asignado
					let selectID = $(this).attr('id');
					// Buscar el member id en el objeto de correspondencia
					let memberID = memberIdMap[selectID];


					frappe.call({
						method: "company_sync.company_sync.doctype.company_sync_scheduler.company_sync_scheduler.update_log_review",
						args: { company_sync_scheduler: frm.doc.name, memberid: memberID, review: newValue },
						callback: function (r) {
							console.log("Update")
						}
					});
				});
			},
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
				doctype: "Company Sync Scheduler Log",
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
	frappe.model.with_doc("Company Sync Scheduler", frm.doc.name)
		.then(() => frm.reload_doc());
}

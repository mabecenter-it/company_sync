// Copyright (c) 2024, Dante Devenir and contributors
// For license information, please see license.txt
frappe.ui.form.on("Company Sync Log", "review", function(frm, cdt, cdn) {
	var item = locals[cdt][cdn]; // this is where the magic happens
	// locals is a global array that contains all the local documents opened by the user
	// item is the row that the user is working with
	// to what you need to do and update it back

	console.log(item);
	
	let newValue = item.review;
	let memberID = item.memberid;

	frappe.call({
		method: "company_sync.company_sync.doctype.company_sync_scheduler.company_sync_scheduler.update_log_review",
		args: { name: item.name, review: newValue },
		callback: function (r) {
			//console.log("Update")
		}
	});
});

frappe.ui.form.on("Company Sync Log", "description", function(frm, cdt, cdn) {
	frm.save();
});

frappe.ui.form.on("Company Sync Scheduler", {
	setup(frm) {
		frappe.realtime.on("company_sync_refresh", ({ percentage, company_sync }) => {		
			// Solo la primera vez se muestra la sección
			if (!frm._has_shown_sync_log_preview) {
				console.log("Acá activo section_sync_preview");
				frm.toggle_display("section_sync_preview", true);
				frm._has_shown_sync_log_preview = true;
			}
			updateProgressBar(frm, percentage);
			//reloadDocument(frm);
		});
		frappe.realtime.on("company_sync_error_log", ({ error_log, company_sync, memberID, company, broker }) => {
			if (!frm._has_shown_sync_error_log_preview) {
				console.log("Acá activo section_sync_log_preview");
				frm.toggle_display("section_sync_log_preview", true);
				frm._has_shown_sync_error_log_preview = true;
			}

			var d = frm.add_child("sync_log");
			d.memberid = memberID;
			d.messages = error_log;

			frm.refresh_field('sync_log');
			
		})
		frappe.realtime.on("company_sync_success", ({ company_sync }) => {		
			successProgressBar(frm);
		})
	},
	onload(frm) {
		/* if (frm.is_new()) {
			frm.toggle_display("section_sync_preview", false);
		} */
	},
	refresh(frm) {
        frm.trigger("update_primary_action");
		frm.trigger("order_by_table");
		frm._has_shown_sync_log_preview = false;
		frm._has_shown_sync_error_log_preview = false;
	},
	hide_index(frm) {
		const $sync_log_wrapper = frm.get_field("sync_log").$wrapper;
		console.log($sync_log_wrapper)
		let $header_index = $sync_log_wrapper.find('.row-index');

		$header_index.each(function(index, element) {
			$(element).hide();
		});

		let $header_check = $sync_log_wrapper.find('.row-check');

		$header_check.each(function(index, element) {
			$(element).hide();
		});
	},
    onload_post_render(frm) {
		frm.trigger("update_primary_action");
		console.log("No debi entrar acá");
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
		//valide if child table sync_log is empty
		console.log(frm.doc.sync_log.length)
		if (frm.doc.sync_log.length > 0) {
			frm.toggle_display("section_sync_log_preview", true);
			frm._has_shown_sync_log_preview = false;
			console.log("Acá active en update_primary_action -> section_sync_log_preview");
			frm.disable_save();
			frm.set_df_property("company_file", "read_only", 1);
		} else {
			frm.enable_save();
			let label = frm.doc.status === "Pending" ? __("Start Sync") : __("Retry");
			frm.page.set_primary_action(label, () => frm.events.start_sync(frm));
			frm._has_shown_sync_error_log_preview = false;
		}
	},
	start_sync(frm) {
		frm.set_df_property("company_file", "read_only", 1);
		frm.call({
			method: "form_start_sync",
			args: { company_sync_scheduler: frm.doc.name },
			btn: frm.page.btn_primary,
		}).then((r) => {
			if (r.message === true) {
				frm.disable_save();
			}
		});
	},
	order_by_table(frm) {
		if (frm.is_new()) return;
	  
		const $sync_log_wrapper = frm.get_field("sync_log").$wrapper;
	  
		function attachClickEvent() {
		  let $header = $sync_log_wrapper.find('.grid-heading-row div[data-fieldname="messages"]').first();
		  if ($header.length) {
			// Aplicar estilo global (si no lo tienes ya en CSS)
			$header.css({
			  "cursor": "pointer",
			  "text-decoration": "underline"
			});
	  
			// Quitar cualquier listener previo y asignar el de toggle
			$header.off('click.sort_toggle').on('click.sort_toggle', function() {
			  // Almacenar el orden original la primera vez
			  if (!frm._sync_log_original) {
				frm._sync_log_original = frm.doc.sync_log.slice(); // Realiza una copia del arreglo
			  }
			  if (frm._is_sorted_desc) {
				// Si ya está ordenado de forma descendente, restaurar el orden original
				frm.doc.sync_log = frm._sync_log_original.slice();
				frm._is_sorted_desc = false;
			  } else {
				// Ordenar de forma descendente
				frm.doc.sync_log.sort((a, b) => {
				  if (a.messages < b.messages) return 1;
				  if (a.messages > b.messages) return -1;
				  return 0;
				});
				frm._is_sorted_desc = true;
			  }
			  // Refrescar el campo para actualizar la vista
			  frm.refresh_field('sync_log');
			});
		  }
		}
	  
		// Asignar el listener inicialmente
		attachClickEvent();
	  
		// MutationObserver para reactivar el listener cuando el grid se re-renderice
		const observer = new MutationObserver(() => {
		  attachClickEvent();
		});
		observer.observe($sync_log_wrapper.get(0), { childList: true, subtree: true });
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

function successProgressBar(frm) {
	const $wrapper = frm.get_field("sync_preview").$wrapper;
	$wrapper.empty();
	
	const $progress = $('<div class="progress">').appendTo($wrapper);
	$('<div class="progress-bar progress-bar-striped progress-bar-animated bg-success">')
		.attr({
			'role': 'progressbar',
			'style': `width: 100%`,
			'aria-valuenow': '100',
			'aria-valuemin': '0', 
			'aria-valuemax': '100'
		})
		.text(`100%`)
		.appendTo($progress);
	
	frm.doc.status = "Success";
	frm.refresh_field("status");
}

function reloadDocument(frm) {
	frappe.model.with_doc("Company Sync Scheduler", frm.doc.name)
		.then(() => frm.reload_doc());
}

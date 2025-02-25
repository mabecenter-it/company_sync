frappe.provide("configurator.setup");

frappe.pages["setup-wizard"].on_page_load = function (wrapper) {
	if (frappe.sys_defaults.company) {
		frappe.set_route("desk");
		return;
	}
};

frappe.setup.on("before_load", function () {
	configurator.setup.slides_settings.map(frappe.setup.add_slide);
});

configurator.setup.slides_settings = [
	{
		name: "Database",
		title: __("Setup your config"),
		icon: "fa fa-building",
		fields: [
			{
				fieldname: "host",
				label: __("Host"),
				fieldtype: "Data",
				reqd: 1,
			},
            {
				fieldname: "port",
				label: __("Port"),
				fieldtype: "Int",
				reqd: 1,
			},
            {
				fieldname: "name_db",
				label: __("Name"),
				fieldtype: "Data",
				reqd: 1,
			},
            {
				fieldname: "user",
				label: __("User DB"),
				fieldtype: "Data",
				reqd: 1,
			},
            {
				fieldname: "password",
				label: __("Password"),
				fieldtype: "Password",
				reqd: 1,
			},
            {
				fieldname: "type",
				label: __("Type"),
				fieldtype: "Select",
				reqd: 1,
			},
            {
				fieldname: "connector",
				label: __("Connector"),
				fieldtype: "Select",
				reqd: 1,
			}
		],

		onload: function (slide) {
            let type_field = slide.get_field("type");
            if(type_field) {
                type_field.set_data(['', 'MariaDB', 'MySQL']);
            }
            
            let conn_field = slide.get_field("connector");
            if(conn_field) {
                conn_field.set_data(['', 'pymysql']);
            }
            
		},
	}
]
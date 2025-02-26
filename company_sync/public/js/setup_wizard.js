frappe.provide("company_sync.setup");

frappe.pages["setup-wizard"].on_page_load = function (wrapper) {
	if (frappe.sys_defaults.company) {
		frappe.set_route("desk");
		return;
	}
};

frappe.setup.on("before_load", function () {
	company_sync.setup.slides_settings.map(frappe.setup.add_slide);
});

company_sync.setup.slides_settings = [
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
                type_field.df.options = ['', 'MariaDB', 'MySQL'].join('\n');
				type_field.refresh();
            }
            
            let conn_field = slide.get_field("connector");
            if(conn_field) {
                conn_field.df.options = ['', 'pymysql'].join('\n');
				conn_field.refresh();
            }
            
		},
	},
	{
		name: "API",
		title: __("Setup your config"),
		icon: "fa fa-building",
		fields: [
			{
				fieldname: "endpoint",
				label: __("Endpoint"),
				fieldtype: "Data",
				reqd: 1,
			},
            {
				fieldname: "user_db",
				label: __("User DB"),
				fieldtype: "Data",
				reqd: 1,
			},
            {
				fieldname: "token",
				label: __("Token"),
				fieldtype: "Data",
				reqd: 1,
			},
		],

		onload: function (slide) {
            /* let type_field = slide.get_field("type");
            if(type_field) {
                type_field.df.options = ['', 'MariaDB', 'MySQL'].join('\n');
				type_field.refresh();
            }
            
            let conn_field = slide.get_field("connector");
            if(conn_field) {
                conn_field.df.options = ['', 'pymysql'].join('\n');
				conn_field.refresh();
            } */
		},
	}
]
frappe.dashboards.chart_sources[ "Company Sync Data" ] = {
    method: "company_sync.company_sync.dashboard_chart_source.company_sync_data.company_sync_data.get_data",
    filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
               {
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
	]
};

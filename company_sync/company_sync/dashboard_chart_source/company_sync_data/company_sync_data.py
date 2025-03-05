import frappe 

@frappe.whitelist()
def get_data():
    
    return {
        "labels": ["A", "B", "C"], 
        "datasets": 
        [
            {"values": [23, 45, 56] , "name" : "Demo1", "chartType" : "line"},
            {"values": [12, 40, 60] , "name" : "Demo2", "chartType" : "bar"},
            {"values": [67, 30, 20] , "name" : "Demo3", "chartType" : "bar"}

        ],
        "type": "axis-mixed",
     }
import frappe
from frappe.desk.form.assign_to import add as assign_to
from frappe.desk.form.assign_to import clear as assing_clear
from frappe.desk.form.assign_to import get as assing_get
import json


@frappe.whitelist()
def get_teams(user_id):
    """
    Returns a list of all Teams, the current Agent is Member of
    """
    print("get_teams called ", user_id)
    teams = frappe.get_all(
        "HD Team Member", 
        fields = ["name", "parent", "user"],
        filters = { "user": user_id})
    teams_list = []
    for el in teams:
        teams_list.append(el["parent"])
    return teams_list

@frappe.whitelist()
def get_teams_members(user_id):
    """
    Returns a list of all Members of all Teams, the current Agent is Member of
    """
    print("get_teams_memebers called ", user_id)
    teams_list = get_teams(user_id)
    user_id_list = []
    for team in teams_list:
        user_for_team = frappe.get_all(
            "HD Team Member", 
            fields = ["name", "parent", "user"],
            filters = { "parent": team})
        for user in user_for_team:
            if user["user"] not in user_id_list:
                user_id_list.append(user["user"])
    return user_id_list

@frappe.whitelist()
def get_assigned_tickets_for_user(user_id):
    """
    returns a list of all Tickets assigned to current agent
    """
    ticket_list = []
    tickets = frappe.get_all(
		"ToDo",
		fields=["reference_name"],
		filters={
			"reference_type": "HD Ticket",
			"allocated_to": user_id,
            "status": "Open"
		}
	)
    for ticket in tickets:
        if ticket["reference_name"] not in ticket_list:
            ticket_list.append(ticket["reference_name"])
    print("returned own ticket list", ticket_list)
    return ticket_list

@frappe.whitelist()
def get_assigned_tickets_for_teams(user_id):
    """
    returns a list of all Tickets assigned every member of every team of current agent
    """
    ticket_list = []
    tickets = frappe.get_all(
		"ToDo",
		fields=["reference_name"],
		filters={
			"reference_type": "HD Ticket",
			#"allocated_to": ["in", get_teams_members(user_id)],
		}
	)
    for ticket in tickets:
        if ticket["reference_name"] not in ticket_list:
            ticket_list.append(ticket["reference_name"])
    print("returned teams ticket list", ticket_list)

    return ticket_list


@frappe.whitelist()
def assign_ticket(ticket, user_id):
    """
    assigns ticket to current Agent
    """
    print("assign_ticket called ", ticket, user_id)

@frappe.whitelist()
def print_data(ticket_id):
    print("called print_data with: " , ticket_id)
    return

@frappe.whitelist()
def assing_ticket_to_me(ticketId, user_id):
    user_id_list = [user_id]
    """add in someone's to do list
    args = {
        "assign_to": [],
        "doctype": ,
        "name": ,
        "description": ,
    "assignment_rule": 
    }

    """
    data = {
        "assign_to": json.dumps(user_id_list),
        "doctype": "HD Ticket",
        "name": str(ticketId),
        "description": "Self assigned in Custom-Portal"
    }
    res = assign_to(data)
    return res

@frappe.whitelist()
def remove_assignment(ticketId):
    res = assing_clear("HD Ticket", str(ticketId))
    print(res)
    return res

@frappe.whitelist()
def get_unassigned_tickets_of_my_teams(user_id):
    print("get_unassigned_tickets_of_my_teams called")
    my_teams = get_teams(user_id)
    ticket_list = []
    tickets = frappe.get_all("HD Ticket",
                             filters= {
                                 "agent_group": ["in", my_teams] },
                             fields= ["name", "_assign"]
                            
                             )
    print(tickets, "ticketsssss")
    for ticket in tickets:
        if ticket["name"] not in ticket_list:
            if ticket["_assign"] != "[]":
                continue
            ticket_list.append(ticket["name"])
    print("ticket list ", ticket_list)
    return ticket_list
    


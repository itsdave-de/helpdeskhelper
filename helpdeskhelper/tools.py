import frappe
from frappe.desk.form.assign_to import add as assign_to
from frappe.desk.form.assign_to import clear as assing_clear
from frappe.desk.form.assign_to import get as assing_get
import json
from frappe.utils import now_datetime
import datetime
import time

@frappe.whitelist()
def get_homescreen_content():
   
    roles = frappe.get_all("Has Role", filters={"parent": frappe.session.user, "role": "frappe_rezze-intern_lesen"}, fields=["role"])
    print(roles)
    if roles:
        if roles[0]["role"] == "frappe_rezze-intern_lesen":
            news_to_display = frappe.get_all("SSC News")
    else:
        news_to_display = frappe.get_all("SSC News", filters={"kategorie": ["not in", "Mitteilungen Rezeption intern"]})
    news = []
    for n in news_to_display:
        news_doc = frappe.get_doc("SSC News", n["name"])
        news.append(news_doc)
    return {"news": news}

def convert_to_unix_timestamp(dt):
    try:
        print("Attempting to convert:", dt)
        if isinstance(dt, datetime.datetime):
            unix_timestamp = int(time.mktime(dt.timetuple()))
            print("Conversion successful:", unix_timestamp)
            return unix_timestamp
        else:
            print("Error: The provided input is not a datetime object", dt)
            frappe.throw("The provided input is not a datetime object", ValueError)
    except Exception as e:
        print("Exception occurred in convert_to_unix_timestamp:", str(e))
        raise e


def translate_location_for_app(ssc_standort, ssc_standorte=None):
    if not ssc_standorte:
        ssc_standorte = frappe.get_all("SSC Standort", fields=["name", "caption", "app_caption"])
    for el in ssc_standorte:
            if el["name"] == ssc_standort:
                if el["app_caption"]:
                    ssc_standort = el["app_caption"]
                else:
                    ssc_standort = el["caption"]
    return ssc_standort

@frappe.whitelist()
def app_get_tickets():
    try:
        user_id = frappe.session.user
        print("User ID:", user_id)
        
        ticket_ids = get_tickets_for_my_teams(user_id)
        print("Ticket IDs:", ticket_ids)
        
        ssc_standorte = frappe.get_all("SSC Standort", fields=["name", "caption", "app_caption"])


        tickets = []
        for id in ticket_ids:
            ticket = frappe.get_doc("HD Ticket", id)
            
            # Convert custom_wiedervorlage to Unix timestamp
            if 'custom_wiedervorlage' in ticket.__dict__ and ticket.custom_wiedervorlage:
                print("custom_wiedervorlage:", ticket.custom_wiedervorlage)
                ticket.custom_wiedervorlage = convert_to_unix_timestamp(ticket.custom_wiedervorlage)
                print(ticket.custom_wiedervorlage)
            else:
                ticket.custom_wiedervorlage = 0
            # Replace Location
            ticket.custom_ort_bezeichnung = translate_location_for_app(ticket.custom_ort, ssc_standorte)
            tickets.append(ticket.__dict__)
        
        return tickets
    except Exception as e:
        print("Exception occurred in app_get_tickets:", str(e))
        raise e

@frappe.whitelist()
def get_user_id():
    return frappe.session.user

@frappe.whitelist()
def set_ticket_field(ticket, field, value):
    print("set ticket field called", ticket, field, value )
    hd_ticket_doc = frappe.get_doc("HD Ticket", ticket)
    print(hd_ticket_doc.owner)
    setattr(hd_ticket_doc, "owner", value)
    print(hd_ticket_doc.owner)
    hd_ticket_doc.save()


@frappe.whitelist()
def set_ticket(data, command=False):
    print(data)
    app_settings = frappe.get_single("Helpdesk App Settings")

    if command == "set_warten":
        hd_ticket_doc = frappe.get_doc("HD Ticket", data["name"])
        hd_ticket_doc.priority = "Warten"
        hd_ticket_doc.custom_color = frappe.get_value("HD Ticket Priority", "Warten", "custom_color")
        hd_ticket_doc.save()
        remove_assignment(hd_ticket_doc.name)
        return "Ticket set to priority=Warten."

    if data["name"] == "Neues Ticket":
        print("ertelle neues Ticket ", data["subject"], data["description"] )
        agent_group = get_teams(frappe.session.user)[0]
        hd_ticket_doc = frappe.get_doc({
            "doctype": "HD Ticket",
            "subject": str(data["subject"]),
            "description": str(data["description"]),
            "agent_group": agent_group,
            "custom_zugang": app_settings.default_zugang,
            "ticket_type":app_settings.default_ticket_type}
            )
        hd_ticket_doc.insert()
        return "Ticket created sucessfully"
    
    if "ticket_type" in data.keys():
        if str(data["ticket_type"]).lower() == "strom rauf-runter-ablesen":
            print("strom rauf-runter-ablesen Prozess called")
            hd_ticket_doc = frappe.get_doc("HD Ticket", data["name"])
            if str(data["custom_strom_prozess"]) == "erfasst":
                if float(data["custom_zählerstand_anfang"]) > 0:
                    hd_ticket_doc.custom_zählerstand_anfang = float(data["custom_zählerstand_anfang"])
                    hd_ticket_doc.custom_strom_prozess = "hochgestellt"
                    hd_ticket_doc.status = "Replied"
                    hd_ticket_doc.save()
                    remove_assignment(hd_ticket_doc.name)
                    return "Ticket updated sucessfully"
                else:
                    frappe.throw("Zählerstand Anfang muss > 0 sein")
                    return
            if str(data["custom_strom_prozess"]) == "hochgestellt":
                if float(data["custom_zählerstand_ende"]) > 0:
                    hd_ticket_doc.custom_zählerstand_ende = float(data["custom_zählerstand_ende"])
                    hd_ticket_doc.custom_strom_prozess = "runtergestellt"
                    hd_ticket_doc.custom_verbrauch_kwh = hd_ticket_doc.custom_zählerstand_ende - hd_ticket_doc.custom_zählerstand_anfang
                    hd_ticket_doc.status = "Closed"
                    hd_ticket_doc.save()
                    remove_assignment(hd_ticket_doc.name)
                    return "Ticket updated sucessfully"
                else:
                    frappe.throw("Zählerstand Anfang muss > 0 sein")
                    return
    

    # Close Ticket in other cases
    hd_ticket_doc = frappe.get_doc("HD Ticket", data["name"])
    
    if data.get("zaehlerstand") and float(data["zaehlerstand"]) > 0:
        hd_ticket_doc.custom_zählerstand = float(data["zaehlerstand"])
    hd_ticket_doc.status = "Closed"
    hd_ticket_doc.save()
    return "Ticket closed successfully"



def apply_wiedervorlage():
    print("running apply_wiedervorlage")
    ticket_list = frappe.get_all("HD Ticket", 
                                 filters={
                                     "custom_wiedervorlage": ['is', 'set'],
                                     "status": ['!=', 'Closed'],
    #                                 "feedback": 0,
                                 }, 
                                 fields=["name", "status", "ticket_type", "custom_wiedervorlage", "custom_strom_prozess"])
    print("Ticket List for apply_wiedervorlage: ", ticket_list)
    for t in ticket_list:
        # Since we now also fetch custom_wiedervorlage in the get_all, we can check it directly
        if t["custom_wiedervorlage"] <= now_datetime():
            print("found wiedervorlage for ticket", t["name"])
            # Only get the document if we need to update it
            hd_ticket_doc = frappe.get_doc("HD Ticket", t["name"])
            if hd_ticket_doc.status not in ["Closed", "Resolved"]:
                hd_ticket_doc.status = "Open"
            # Spezialfall strom rauf-runter-ablesen bei abreise des Gastes
            # 21.08.24: sollte eigentlich nicht mehr notwendig sein.
            # if str(hd_ticket_doc.ticket_type).lower() == "strom rauf-runter-ablesen":
            #     print("setting to abgereist")
            #     hd_ticket_doc.custom_strom_prozess = "abgereist"
            hd_ticket_doc.custom_wiedervorlage = None
            hd_ticket_doc.save()
    frappe.db.commit()



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
			"allocated_to": user_id
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
			"allocated_to": ["in", get_teams_members(user_id)],
                        "status": "open"
		}
	)
    for ticket in tickets:
        if ticket["reference_name"] not in ticket_list:
            ticket_list.append(ticket["reference_name"])
    print("returned teams ticket list", ticket_list)

    return ticket_list


@frappe.whitelist()
def get_tickets_for_my_teams(user_id):
    """
    returns a list of all Tickets assigned every member of every team of current agent
    """
    my_teams = get_teams(user_id)
    ticket_list = []
    #first query for all tickets except the closed ones
    tickets = frappe.get_all("HD Ticket",
                             filters= {
                                 "agent_group": ["in", my_teams],
                                 "status": ["not in", "Closed"] },
                             fields= ["name", "_assign"]
                            
                             )
    for ticket in tickets:
        if ticket["name"] not in ticket_list:
            ticket_list.append(ticket["name"])
    
    #...and now some closed tickets, if chosen
    #get number of closed tickets to fetch
    helpdesk_app_settings = frappe.get_single("Helpdesk App Settings")
    closed_tickets_sync_count = helpdesk_app_settings.closed_tickets_sync_count
    
    if closed_tickets_sync_count > 0:
        print("fetching closed: ", closed_tickets_sync_count)
        tickets = frappe.get_all("HD Ticket",
                             filters= {
                                 "agent_group": ["in", my_teams],
                                 "status": ["in", "Closed"] },
                             fields= ["name", "_assign"],
                             order_by="modified desc",  # Sort by modification date in descending order
                             limit_page_length=closed_tickets_sync_count
                             )
        for ticket in tickets:
            print("appending closed ", ticket["name"])
            if ticket["name"] not in ticket_list:
                ticket_list.append(ticket["name"])
    print(ticket_list)
    return ticket_list

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
    print("checking if assigned...")
    if not check_is_allready_assigned(ticketId):
        print("no")
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
            "description": "selbst per App zugewiesen."
        }
        res = assign_to(data)
        return res
    else:
        frappe.throw("Das Ticket ist bereits übernommen worden. Aktualisiere deine Ansicht durch herunterziehen.")

def check_is_allready_assigned(ticketId):
    """check if a Ticket is allready assigned."""
    data = {
        "doctype": "HD Ticket",
        "name": str(ticketId),
    }
    res = assing_get(data)
    if res == []:
        return False
    else:
        return True



@frappe.whitelist()
def remove_assignment(ticketId):
    hd_ticket_doc = frappe.get_doc("HD Ticket", ticketId)
    if hd_ticket_doc.ticket_type == "Strom rauf-runter-ablesen":
        res = assing_clear("HD Ticket", str(ticketId))
        print(res)
        return res

    if is_last_entry_by_current_user(ticketId):
        res = assing_clear("HD Ticket", str(ticketId))
        print(res)
        return res
    else:
        frappe.throw("Ticket konnte nicht freigegeben werden. Bitte erst einen Kommentar hinzufügen.")
   

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
    

@frappe.whitelist()
def get_settings():

    HDTeams_list = []
    HDTeams = frappe.get_all("HD Team")
    for el in HDTeams:
        HDTeams_list.append(el["name"])
    
    HDPriorities_list = []
    HDPriorities = frappe.get_all("HD Ticket Priority")
    for el in HDPriorities:
        HDPriorities_list.append(el["name"])
    
    Locations_list = []
    Locations = frappe.get_all("SSC Standort", fields=["name","caption"])
    for el in Locations:
        Locations_list.append(el["caption"])
        

    result = {
        "HDTeams":HDTeams_list,
        "HDPriorities": HDPriorities_list,
        "Locations": Locations_list}
    
    return result


def is_last_entry_by_current_user(ticket_id):
    """
    Checks if the last comment or communication on the HD Ticket is by the currently logged-in user,
    ignoring entries where content ends with "hat sich diese Aufgabe selbst zugewiesen: selbst per App zugewiesen."
    """
    def get_last_relevant_entry(ticket_id):
        """
        Retrieves the last relevant comment or communication, ignoring entries with specific content.
        """
        # Get the last few comments (in case we need to skip some)
        comments = frappe.get_all(
            "Comment", 
            filters={"reference_doctype": "HD Ticket", "reference_name": ticket_id}, 
            fields=["name", "owner", "creation", "subject", "content"],
            order_by="creation desc", 
            limit_page_length=5
        )

        # Get the last few communications (in case we need to skip some)
        communications = frappe.get_all(
            "Communication", 
            filters={"reference_doctype": "HD Ticket", "reference_name": ticket_id},
            fields=["name", "owner", "creation", "subject", "content"],
            order_by="creation desc", 
            limit_page_length=5
        )

        # Combine and sort by creation date
        entries = comments + communications
        entries = sorted(entries, key=lambda x: x['creation'], reverse=True)

        # Iterate over the entries to find the first relevant one
        for entry in entries:
            if not entry['content'].strip().endswith("hat sich diese Aufgabe selbst zugewiesen: selbst per App zugewiesen."):
                return entry

        return None

    # Get the last relevant entry
    last_entry = get_last_relevant_entry(ticket_id)
    
    if last_entry:
        print("last entry check: ", last_entry, frappe.session.user)
        # Check if the last entry was made by the currently logged-in user
        return last_entry.get('owner') == frappe.session.user
    else:
        return False  # No relevant comments or communications found



@frappe.whitelist()
def app_get_anleitungen():
    try:
        # Query the File doctype for files in the "anleitungen" folder
        files = frappe.get_all(
            'File',
            filters={'folder': 'Home/Anleitungen'},  # Adjust the path if necessary
            fields=['name', 'file_name', 'file_url', 'file_size']
        )

        if not files:
            return {
                'message': _("No files found in the 'anleitungen' folder.")
            }

        return {
            'message': files
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "app_get_anleitungen")
        return {
            'error': str(e)
        }

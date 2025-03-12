import json
import requests
import sys

# Function to get OAuth Access Token
def get_access_token():
    INSTANCE_URL = "https://dovercorporationdev.service-now.com"
    TOKEN_URL = f"{INSTANCE_URL}/oauth_token.do"

    USERNAME = "iautomate"
    PASSWORD = "Dover@123"

    payload = {
        'username': USERNAME,
        'password': PASSWORD
    }

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    token_response = requests.post(TOKEN_URL, headers=headers, data=payload)
    token_response.raise_for_status()
    
    return token_response.json().get('access_token')

# Function to fetch incident details from ServiceNow
def fetch_incident_details(incident_number, headers):
    INSTANCE_URL = "https://dovercorporationdev.service-now.com"
    URL_FETCH = f"{INSTANCE_URL}/api/now/v1/table/incident?sysparm_query=number={incident_number}&sysparm_fields=sys_id,incident_state,assignment_group"

    fetch_response = requests.get(URL_FETCH, headers=headers)
    fetch_response.raise_for_status()

    return fetch_response.json().get("result", [])

# Function to update an incident in ServiceNow
def update_incident(sys_id, body, headers):
    INSTANCE_URL = "https://dovercorporationdev.service-now.com"
    URL_UPDATE = f"{INSTANCE_URL}/api/ashe/iautomate/updateTicket"

    update_response = requests.put(URL_UPDATE, headers=headers, json=body)
    update_response.raise_for_status()

    return update_response.json()

# Main function to orchestrate the workflow
def main():
    try:
        # Fetch access token
        access_token = get_access_token()

        # Authorization Header
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Parse input arguments
        resp = json.loads(sys.argv[2])
        incident_number = resp.get("incident_number")
        work_notes = resp.get("work_notes", "")
        resolution_category = resp.get("resolution_category", "")
        resolution_subcategory = resp.get("resolution_subcategory", "")

        # Define static values
        assignment_group = "546607d71b26e050e983ecadee4bcb7a"
        assigned_to = "sn.iAutomate.integration"
        incident_state = "6"

        # Fetch incident details
        incidents = fetch_incident_details(incident_number, headers)

        if not incidents:
            print(json.dumps({"status": "Incident not found"}))
            return

        # Extract relevant details
        incident = incidents[0]
        sys_id = incident.get("sys_id")
        current_state = incident.get("incident_state")
        current_assignment_group = incident.get("assignment_group")

        # Check if incident is in iAutomate queue and needs update
        if current_assignment_group == assignment_group and current_state in ['1', '2', '5']:
            body = {
                "number": incident_number,
                "incident_state": incident_state,
                "work_notes": work_notes,
                "assignment_group": "Automation",
                "assigned_to": assigned_to,
                "resolution_category": resolution_category,
                "resolution_subcategory": resolution_subcategory
            }
            
            update_response = update_incident(sys_id, body, headers)
            print(json.dumps({"status": "Incident is resolved with required parameters", "response": update_response}))
        else:
            print(json.dumps({"status": "Incident is not in iAutomate queue or is already resolved"}))

    except Exception as e:
        print(json.dumps({"Error": f"Error in running script: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()

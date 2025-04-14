from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import requests
import logging
import uuid
from dotenv import load_dotenv
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token=os.getenv("SLACK_TOKEN"))

def send_slack_notification(message: str):
    webhook_url = os.getenv("SLACK_TOKEN")
    try:
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload)
        if response.status_code != 200:
            error_logger.error(f"Slack webhook failed: {response.text}")
    except Exception as e:
        error_logger.error(f"Slack notification error: {str(e)}")

# logs settings
logging.basicConfig(level=logging.INFO)

# logs for webhook
webhook_logger = logging.getLogger("webhook_logger")
webhook_handler = logging.FileHandler("webhook.log")
webhook_handler.setLevel(logging.INFO)
webhook_formatter = logging.Formatter('%(asctime)s - %(message)s')
webhook_handler.setFormatter(webhook_formatter)
webhook_logger.addHandler(webhook_handler)

# logs for errors
error_logger = logging.getLogger("error_logger")
error_handler = logging.FileHandler("errors.log")
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(message)s')
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

# logs for actions
action_logger = logging.getLogger("action_logger")
action_handler = logging.FileHandler("actions.log")
action_handler.setLevel(logging.INFO)
action_formatter = logging.Formatter('%(asctime)s - %(message)s')
action_handler.setFormatter(action_formatter)
action_logger.addHandler(action_handler)

load_dotenv()

app = FastAPI()

class WebhookData(BaseModel):
    event: str
    data: dict

#----------------------------#
# Get Data from Form
#----------------------------#
@app.post("/webhook")
async def webhook_endpoint(payload: WebhookData):
    request_id = str(uuid.uuid4())
    webhook_logger.info(f"Received webhook: {request_id} | {payload.model_dump_json()}")
    action_logger.info(f"\n--- Request ID: {request_id} --- Data: {payload.model_dump_json()} ---")
    error_logger.error(f"\n--- Request ID: {request_id} --- Data: {payload.model_dump_json()} ---")
    try:
        API_KEY = os.getenv("API_KEY")
        URL = f"https://rest.gohighlevel.com"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Version": "2021-04-15",
            "Content-Type": "application/json"
        }

        search_contact_ghl = search_contact(payload.data["email"], URL, headers)  # Search contact

        # contact doesnt exist
        if "email" in search_contact_ghl and search_contact_ghl["email"]["message"] == "The email address is invalid.":
            email, name, phone = payload.data["email"], payload.data["name"], payload.data["phone"]
            new_contact = create_contact(email, name, phone, URL, headers)  # Create contact
            contact_id = new_contact["contact"]["id"]
            action_logger.info(f"Created contact: {new_contact}")
            
            create_deal(contact_id, email, name, URL, headers)
            action_logger.info(f"Created deal for contact_id={contact_id}")
        # contact exist
        else:
            contact_id = search_contact_ghl["contacts"][0]["id"]
            updated_contact = update_contact(contact_id, payload.data["name"], URL, headers)
            action_logger.info(f"Updated contact: {updated_contact}")
            
            email, name, phone = updated_contact["contact"]["email"], updated_contact["contact"]["fullNameLowerCase"], updated_contact["contact"]["phone"]
            deal = search_deal(contact_id, URL, headers)
            if deal is None:
                create_deal(contact_id, email, name, URL, headers)
                action_logger.info(f"Created deal for contact_id={contact_id}")
            else:
                deal_id = deal.get('id')
                update_deal(deal_id, contact_id, email, name, URL, headers)
                action_logger.info(f"Updated deal: deal_id={deal_id}, contact_id={contact_id}")

        return {"status": "ok"}
    except Exception as e:
        error_logger.error(f"Error in webhook processing: {str(e)}")
        send_slack_notification(f'{e}')
        return {"status": "error", "message": str(e)}

#----------------------------#
# GoHighLevel Search Contact
#----------------------------#
def search_contact(email: str, URL, headers):
    response = requests.get(f'{URL}/v1/contacts/lookup?email={email}', headers=headers)
    try:
        result = response.json()
        action_logger.info(f"Searched contact by email: {email}, Result: {result}")
        return result
    except requests.exceptions.JSONDecodeError as e:
        error_logger.error(f"Failed to decode JSON response for search_contact: {str(e)}")
        send_slack_notification(f'{e}')
        return {"error": "Failed to decode JSON response"}

#----------------------------#
# GoHighLevel Create Contact
#----------------------------#
def create_contact(email, name, phone, URL, headers):
    data_raw = {
        "email": email,
        "name": name,
        "phone": phone
    }

    response = requests.post(f'{URL}/v1/contacts/', headers=headers, json=data_raw)
    try:
        result = response.json()
        action_logger.info(f"Contact created: {result}")
        return result
    except requests.exceptions.JSONDecodeError as e:
        error_logger.error(f"Failed to decode JSON response for create_contact: {str(e)}")
        send_slack_notification(f'{e}')
        return {"error": "Failed to decode JSON response"}
    
#----------------------------#
# GoHighLevel Update Contact
#----------------------------#
def update_contact(id, name,  URL, headers):
    data_raw = {
        "name": name
    }

    response = requests.put(f'{URL}/v1/contacts/{id}', headers=headers, json=data_raw)
    
    try:
        result = response.json()
        action_logger.info(f"Contact updated: {result}")
        return result
    except requests.exceptions.JSONDecodeError as e:
        error_logger.error(f"Failed to decode JSON response for update_contact: {str(e)}")
        send_slack_notification(f'{e}')
        return {"error": "Failed to decode JSON response"}

#----------------------------#
# GoHighLevel Search Deal
#----------------------------#
def search_deal(contact_id, URL, headers):
    response = requests.get(f'{URL}/v1/pipelines/UuhQYJN98JQKkWP0HcC6/opportunities', headers=headers)
    try:
        deals = response.json().get("opportunities", [])
        for deal in deals:
            if deal.get("contact", {}).get("id") == contact_id: 
                action_logger.info(f"Deal found for contact_id={contact_id}: {deal}")
                return deal  
        
        action_logger.info(f"No deal found for contact_id={contact_id}")
        return None
    except requests.exceptions.JSONDecodeError as e:
        error_logger.error(f"Failed to decode JSON response for search_deal: {str(e)}")
        send_slack_notification(f'{e}')
        return {"error": "Failed to decode JSON response"}

#----------------------------#
# GoHighLevel Create Deal
#----------------------------#
def create_deal(contact_id, email, name, URL, headers):
    data = {
        "title": f"{email} - {name}",
        "status": "open",
        "pipelineId": "UuhQYJN98JQKkWP0HcC6",
        "stageId": "0eaab081-3e7a-4b46-8b35-0fd7135c1540",
        "contactId": contact_id,
    }

    response = requests.post(f'{URL}/v1/pipelines/UuhQYJN98JQKkWP0HcC6/opportunities/', headers=headers, json=data)
    try:
        result = response.json()
        action_logger.info(f"Deal created: {result}")
        return result
    except requests.exceptions.JSONDecodeError as e:
        error_logger.error(f"Failed to decode JSON response for create_deal: {str(e)}")
        send_slack_notification(f'{e}')
        return {"error": "Failed to decode JSON response"}

#----------------------------#
# GoHighLevel Update Deal
#----------------------------#
def update_deal(deal_id, contact_id, email, name, URL, headers):
    data = {
        "title": f"{email} - {name}",
        "status": "open", 
        "pipelineId": "UuhQYJN98JQKkWP0HcC6", 
        "stageId": "0eaab081-3e7a-4b46-8b35-0fd7135c1540",
        "contactId": contact_id
    }

    response = requests.put(f'{URL}/v1/pipelines/UuhQYJN98JQKkWP0HcC6/opportunities/{deal_id}', headers=headers, json=data)
    try:
        result = response.json()
        action_logger.info(f"Deal updated: {result}")
        return result
    except requests.exceptions.JSONDecodeError as e:
        send_slack_notification(f'{e}')
        error_logger.error(f"Failed to decode JSON response for update_deal: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

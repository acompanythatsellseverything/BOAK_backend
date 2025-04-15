from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import requests
from ghl_logging import *
import uuid
from dotenv import load_dotenv
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


"""
Notes
small form
"""

class GoHighLevelAPI:
    def __init__(self):
        load_dotenv()
        # self.client = WebClient(token=os.getenv("SLACK_TOKEN"))
        self.API_KEY = os.getenv("API_KEY")
        self.URL = f"https://rest.gohighlevel.com"
        self.headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Version": "2021-04-15",
            "Content-Type": "application/json"
        }

     #--------------------------
     # SLACK ERROR NOTIFICATIONS
     # ------------------------- 
    def send_slack_notification(self, message: str):
        try:
            webhook_url = os.getenv("SLACK_TOKEN")
            payload = {"text": message}
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                error_logger.error(f"Slack webhook failed: {response.text}")
        except Exception as e:
            error_logger.error(f"Slack notification error: {str(e)}")

    #--------------------------
    #       SEARCH CONTACT
    # ------------------------- 
    def search_contact(self, email: str):
        response = requests.get(f'{self.URL}/v1/contacts/lookup?email={email}', headers=self.headers)
        try:
            result = response.json()
            action_logger.info(f"Searched contact by email: {email}, Result: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            error_logger.error(f"Failed to decode JSON response for search_contact: {str(e)}")
            self.send_slack_notification(f'{e}')
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #       CREATE CONTACT
    # ------------------------- 
    def create_contact(self, email, name, phone):
        data_raw = {
            "email": email,
            "name": name,
            "phone": phone
        }
        response = requests.post(f'{self.URL}/v1/contacts/', headers=self.headers, json=data_raw)
        try:
            result = response.json()
            action_logger.info(f"Contact created: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            error_logger.error(f"Failed to decode JSON response for create_contact: {str(e)}")
            self.send_slack_notification(f'{e}')
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #       UPDATE CONTACT
    # ------------------------- 
    def update_contact(self, id, name):
        data_raw = {
            "name": name
        }
        response = requests.put(f'{self.URL}/v1/contacts/{id}', headers=self.headers, json=data_raw)
        try:
            result = response.json()
            action_logger.info(f"Contact updated: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            error_logger.error(f"Failed to decode JSON response for update_contact: {str(e)}")
            self.send_slack_notification(f'{e}')
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #       SEARCH DEAL
    # ------------------------- 
    def search_deal(self, contact_id):
        response = requests.get(f'{self.URL}/v1/pipelines/UuhQYJN98JQKkWP0HcC6/opportunities', headers=self.headers)
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
            self.send_slack_notification(f'{e}')
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #       CREATE DEAL
    # ------------------------- 
    def create_deal(self, contact_id, email, name):
        data = {
            "title": f"{email} - {name}",
            "status": "open",
            "pipelineId": "UuhQYJN98JQKkWP0HcC6",
            "stageId": "0eaab081-3e7a-4b46-8b35-0fd7135c1540",
            "contactId": contact_id,
        }
        response = requests.post(f'{self.URL}/v1/pipelines/UuhQYJN98JQKkWP0HcC6/opportunities/', headers=self.headers, json=data)
        try:
            result = response.json()
            action_logger.info(f"Deal created: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            error_logger.error(f"Failed to decode JSON response for create_deal: {str(e)}")
            self.send_slack_notification(f'{e}')
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #       UPDATE DEAL
    # ------------------------- 
    def update_deal(self, deal_id, contact_id, email, name):
        data = {
            "title": f"{email} - {name}",
            "status": "open", 
            "pipelineId": "UuhQYJN98JQKkWP0HcC6", 
            "stageId": "0eaab081-3e7a-4b46-8b35-0fd7135c1540",
            "contactId": contact_id
        }
        response = requests.put(f'{self.URL}/v1/pipelines/UuhQYJN98JQKkWP0HcC6/opportunities/{deal_id}', headers=self.headers, json=data)
        try:
            result = response.json()
            action_logger.info(f"Deal updated: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            self.send_slack_notification(f'{e}')
            error_logger.error(f"Failed to decode JSON response for update_deal: {str(e)}")

    #--------------------------
    #       ADD NOTES
    # ------------------------- 
    def add_notes(self, contact_id, comment_body):
        data = {
        "body": comment_body,
        "resourceType": "opportunity",
        "resourceId": contact_id
        }
        print(f"[DEBUG] Deal ID перед нотаткою: {contact_id}")

        response = requests.post(f'{self.URL}/v1/contacts/{contact_id}/notes/', headers=self.headers, json=data)
        try:
            result = response.json()
            action_logger.info(f"Deal updated: {result}")
            print(f'res:{result}')
            return result
        except requests.exceptions.JSONDecodeError as e:
            self.send_slack_notification(f'{e}')
            error_logger.error(f"Failed to decode JSON response for update_deal: {str(e)}")
    


class WebhookData(BaseModel):
    event: str
    data: dict


app = FastAPI()

@app.post("/webhook")
async def webhook_endpoint(payload: WebhookData):
    request_id = str(uuid.uuid4())
    webhook_logger.info(f"Received webhook: {request_id} | {payload.model_dump_json()}")
    action_logger.info(f"\n--- Request ID: {request_id} --- Data: {payload.model_dump_json()} ---")
    error_logger.error(f"\n--- Request ID: {request_id} --- Data: {payload.model_dump_json()} ---")
    comment_body = payload.data["comment"]

    try:
        ghl_api = GoHighLevelAPI()
        search_contact_ghl = ghl_api.search_contact(payload.data["email"])

        # contact doesn't exist
        if "email" in search_contact_ghl and search_contact_ghl["email"]["message"] == "The email address is invalid.":
            email, name, phone = payload.data["email"], payload.data["name"], payload.data["phone"]
            new_contact = ghl_api.create_contact(email, name, phone)
            contact_id = new_contact["contact"]["id"]
            action_logger.info(f"Created contact: {new_contact}")
            deal_data = ghl_api.create_deal(contact_id, email, name)
            action_logger.info(f"Created deal for contact_id={contact_id}")
            deal_id = deal_data["id"]
            ghl_api.add_notes(contact_id, comment_body)
            action_logger.info(f"Created comment for contact_id={contact_id}")

        # contact exists
        else:
            contact_id = search_contact_ghl["contacts"][0]["id"]
            updated_contact = ghl_api.update_contact(contact_id, payload.data["name"])
            action_logger.info(f"Updated contact: {updated_contact}")
            deal = ghl_api.search_deal(contact_id)
            if deal is None:
                deal_data = ghl_api.create_deal(contact_id, payload.data["email"], payload.data["name"])
                action_logger.info(f"Created deal for contact_id={contact_id}")
                deal_id = deal_data["id"]
                ghl_api.add_notes(contact_id, comment_body)
                action_logger.info(f"Created comment for contact_id={contact_id}")
            else:
                deal_id = deal.get('id')
                deal_data = ghl_api.update_deal(deal_id, contact_id, payload.data["email"], payload.data["name"])
                action_logger.info(f"Updated deal: deal_id={deal_id}, contact_id={contact_id}")
                deal_id = deal_data["id"]
                print(deal_id)
                ghl_api.add_notes(contact_id, comment_body)
                action_logger.info(f"Created comment for contact_id={contact_id}")

        return {"status": "ok"}
    except Exception as e:
        error_logger.error(f"Error in webhook processing: {str(e)}")
        ghl_api.send_slack_notification(f'{e}')
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

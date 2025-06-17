from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import requests
from ghl_logging import *
import uuid
from dotenv import load_dotenv
import os
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from fastapi.middleware.cors import CORSMiddleware

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
    #   SEARCH CONTACT(email)
    # ------------------------- 
    def search_contact(self, email: str):
        response = requests.get(f'{self.URL}/v1/contacts/lookup?email={email}', headers=self.headers)
        try:
            result = response.json()
            action_logger.info(f"Searched contact by email: {email}, Result: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            error_logger.error(f"Failed to decode JSON response for search_contact: {str(e)}")
            self.send_slack_notification(f'Failed to decode JSON response for search_contact: {e}')
            return {"error": "Failed to decode JSON response"}
        
    #--------------------------
    #   SEARCH CONTACT(phone)
    # ------------------------- 
    def search_contact_small_form(self, phone: str):
        phone = f'+1{phone}'
        params={'phone': phone}
        response = requests.get(f'{self.URL}/v1/contacts/lookup', params=params, headers=self.headers)
        try:
            result = response.json()
            action_logger.info(f"Searched contact by phone: {phone}, Result: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            error_logger.error(f"Failed to decode JSON response for search_contact: {str(e)}")
            self.send_slack_notification(f"Failed to decode JSON response for search_contact: {str(e)}")
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #   CREATE CONTACT(email)
    # ------------------------- 
    def create_contact(self, email, name, phone, url):
        data_raw = {
            "email": email,
            "name": name,
            "phone": phone,
            "customField": {
                "npIW2acDJLVxtzLav4pg": url
            }
        }
        response = requests.post(f'{self.URL}/v1/contacts/', headers=self.headers, json=data_raw)
        try:
            result = response.json()
            action_logger.info(f"Contact created: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            error_logger.error(f"Failed to decode JSON response for create_contact: {str(e)}")
            self.send_slack_notification(f"Failed to decode JSON response for create_contact: {str(e)}")
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #   CREATE CONTACT(phone)
    # ------------------------- 
    def create_contact_small_form(self, name, phone, url):
        data_raw = {
            "name": name,
            "phone": phone,
            "customField": {
                "npIW2acDJLVxtzLav4pg": url
            }
        }
        response = requests.post(f'{self.URL}/v1/contacts/', headers=self.headers, json=data_raw)
        try:
            result = response.json()
            action_logger.info(f"Contact created: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            error_logger.error(f"Failed to decode JSON response for create_contact: {str(e)}")
            self.send_slack_notification(f"Failed to decode JSON response for create_contact: {str(e)}")
            return {"error": "Failed to decode JSON response"}
    
    #--------------------------
    #       UPDATE CONTACT
    # ------------------------- 
    def update_contact(self, id, name, phone, url):
        data_raw = {
            "name": name,
            "phone": phone,
            "customField": {
                "npIW2acDJLVxtzLav4pg": url
            }
        }
        response = requests.put(f'{self.URL}/v1/contacts/{id}', headers=self.headers, json=data_raw)
        try:
            result = response.json()
            action_logger.info(f"Contact updated: {result}")
            return result
        except requests.exceptions.JSONDecodeError as e:
            error_logger.error(f"Failed to decode JSON response for update_contact: {str(e)}")
            self.send_slack_notification(f"Failed to decode JSON response for update_contact: {str(e)}")
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
            self.send_slack_notification(f"Failed to decode JSON response for search_deal: {str(e)}")
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #   CREATE DEAL(email)
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
            self.send_slack_notification(f"Failed to decode JSON response for create_deal: {str(e)}")
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #   CREATE DEAL(phone)
    # ------------------------- 
    def create_deal_small_form(self, contact_id, phone, name):
        data = {
            "title": f"{phone} - {name}",
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
            self.send_slack_notification(f"Failed to decode JSON response for create_deal: {str(e)}")
            return {"error": "Failed to decode JSON response"}

    #--------------------------
    #       UPDATE DEAL(email)
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
            self.send_slack_notification(f'Failed to decode JSON response for update_deal: {e}')
            error_logger.error(f"Failed to decode JSON response for update_deal: {str(e)}")


    #--------------------------
    #       UPDATE DEAL(phone)
    # ------------------------- 
    def update_deal_small_form(self, deal_id, contact_id, phone, name):
        data = {
            "title": f"{phone} - {name}",
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
            self.send_slack_notification(f'Failed to decode JSON response for update_deal: {e}')
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

        response = requests.post(f'{self.URL}/v1/contacts/{contact_id}/notes/', headers=self.headers, json=data)
        try:
            result = response.json()
            action_logger.info(f"added notes: {result}")
            print(f'res:{result}')
            return result
        except requests.exceptions.JSONDecodeError as e:
            self.send_slack_notification(f'Failed to decode JSON response for add_notes: {e}')
            error_logger.error(f"Failed to decode JSON response for add_notes: {str(e)}")
    

class WebhookData(BaseModel):
    event: str
    data: dict
    utm_url: Optional[str] = None


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/webhook")
async def webhook_endpoint(payload: WebhookData):
    request_id = str(uuid.uuid4())
    webhook_logger.info(f"Received webhook: {request_id} | {payload.model_dump_json()}")
    action_logger.info(f"\n--- Request ID: {request_id} --- Data: {payload.model_dump_json()} ---")
    error_logger.error(f"\n--- Request ID: {request_id} --- Data: {payload.model_dump_json()} ---")
    comment_body = payload.data["comment"]
    url = payload.utm_url

    try:
        ghl_api = GoHighLevelAPI()
        search_contact_ghl = ghl_api.search_contact(payload.data["email"])

        # contact doesn't exist
        if "email" in search_contact_ghl and search_contact_ghl["email"]["message"] == "The email address is invalid.":
            email, name, phone = payload.data["email"], payload.data["name"], payload.data["phone"]
            new_contact = ghl_api.create_contact(email, name, phone, url)
            contact_id = new_contact["contact"]["id"]
            deal_data = ghl_api.create_deal(contact_id, email, name)
            deal_id = deal_data["id"]

        # contact exists
        else:
            contact_id = search_contact_ghl["contacts"][0]["id"]
            ghl_api.update_contact(contact_id, payload.data["name"], payload.data["phone"], url)
            deal = ghl_api.search_deal(contact_id)
            if deal is None:
                deal_data = ghl_api.create_deal(contact_id, payload.data["email"], payload.data["name"])
                deal_id = deal_data["id"]
                ghl_api.add_notes(contact_id, comment_body)
            else:
                deal_id = deal.get('id')
                deal_data = ghl_api.update_deal(deal_id, contact_id, payload.data["email"], payload.data["name"])
                deal_id = deal_data["id"]
                ghl_api.add_notes(contact_id, comment_body)

        return {"status": "ok"}
    except Exception as e:
        error_logger.error(f"Error in webhook processing: {str(e)}")
        ghl_api.send_slack_notification(f'Error in webhook processing: {e}')
        return {"status": "error", "message": str(e)}


@app.post("/small_form")
async def webhook_small_form_endpoint(payload: WebhookData):
    request_id = str(uuid.uuid4())
    webhook_logger.info(f"Received webhook: {request_id} | {payload.model_dump_json()}")
    action_logger.info(f"\n--- Request ID: {request_id} --- Data: {payload.model_dump_json()} ---")
    error_logger.error(f"\n--- Request ID: {request_id} --- Data: {payload.model_dump_json()} ---")
    url = payload.utm_url

    try:
        ghl_api = GoHighLevelAPI()
        search_contact_ghl = ghl_api.search_contact_small_form(payload.data["phone"])

        # contact doesn't exist
        if "phone" in search_contact_ghl and search_contact_ghl["phone"]["message"] == "The phone number is invalid.":
            name, phone = payload.data["name"], payload.data["phone"]
            new_contact = ghl_api.create_contact_small_form(name, phone, url)
            contact_id = new_contact["contact"]["id"]
            ghl_api.create_deal_small_form(contact_id,  phone, name)

        # contact exists
        else:
            contact_id = search_contact_ghl["contacts"][0]["id"]
            ghl_api.update_contact(contact_id, payload.data["name"], payload.data["phone"], url)
            deal = ghl_api.search_deal(contact_id)
            if deal is None:
                ghl_api.create_deal_small_form(contact_id, payload.data["phone"], payload.data["name"])
            else:
                deal_id = deal.get('id')
                ghl_api.update_deal_small_form(deal_id, contact_id, payload.data["phone"], payload.data["name"])
        return {"status": "ok"}
    
    except Exception as e:
        error_logger.error(f"Error in webhook processing: {str(e)}")
        ghl_api.send_slack_notification(f'Error in webhook processing: {e}')
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

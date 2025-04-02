from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import requests

app = FastAPI()

class WebhookData(BaseModel):
    event: str
    data: dict

@app.post("/webhook")
async def webhook_endpoint(payload: WebhookData):
    API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ink1eXUzMGhkMTMzOVpKRG5vVjV6IiwidmVyc2lvbiI6MSwiaWF0IjoxNzM4NTgwODMzMjgwLCJzdWIiOiJpV08xNmo1aU5zWnVDSnBtZmtUNyJ9.YNu_kDA7f6Q66m9KQ7SAJhV6pzmXGm2U606eDDDaPew"
    URL = f"https://rest.gohighlevel.com"
    print(f"Received webhook: {payload}")
    search_contact_ghl = ghl_search_contact(payload.data["email"], API_KEY, URL)

    if "email" in search_contact_ghl and search_contact_ghl["email"]["message"] == "The email address is invalid.":
        create_ghl_contact = ghl_create_contact(payload.data["email"], payload.data["name"], payload.data["phone"], API_KEY, URL)
        print(create_ghl_contact)
    else:
        contact_id = search_contact_ghl["contacts"][0]["id"]
        contact_name = search_contact_ghl["contacts"][0]["id"]
        print(f'update contact {payload.data["email"]}')
        update_ghl_contact = ghl_update_contact(contact_id, payload.data["name"], API_KEY, URL)
        print(f'create {update_ghl_contact}')

    return {"status": "ok"}

# GoHighLevel Search Contact
def ghl_search_contact(email: str, API_KEY, URL):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Version": "2021-04-15",
        "Content-Type": "application/json"
    }
    response = requests.get(f'{URL}/v1/contacts/lookup?email={email}', headers=headers)
    return response.json()

# GoHighLevel Update Contact
def ghl_update_contact(id, name, API_KEY, URL):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Version": "2021-04-15",
        "Content-Type": "application/json"
    }
    data_raw = {
        "name": name
    }

    response = requests.put(f'{URL}/v1/contacts/{id}', headers=headers, json=data_raw)
    
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error: Failed to decode JSON response")
        return {"error": "Failed to decode JSON response"}

# GoHighLevel Create Contact
def ghl_create_contact(email, name, phone, API_KEY, URL):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Version": "2021-04-15",
        "Content-Type": "application/json"
    }
    data_raw = {
        "email": email,
        "name": name,
        "phone": phone
    }

    response = requests.post(f'{URL}/v1/contacts/', headers=headers, json=data_raw)
    
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error: Failed to decode JSON response")
        return {"error": "Failed to decode JSON response"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

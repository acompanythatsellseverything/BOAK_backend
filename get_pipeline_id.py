import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
URL = "https://rest.gohighlevel.com/v1/pipelines/"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

response = requests.get(URL, headers=headers)

if response.status_code == 200:
    pipelines = response.json()
    print(pipelines)
else:
    print("Ошибка:", response.status_code, response.text)

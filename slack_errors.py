from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

slack_token = os.getenv("SLACK_TOKEN")
client = WebClient(token=slack_token)

def send_slack_notification(message: str):
    try:
        response = client.chat_postMessage(
            channel="#your-channel",  # Заміни на свій канал
            text=message
        )
    except SlackApiError as e:
        error_logger.error(f"Slack notification error: {e.response['error']}")

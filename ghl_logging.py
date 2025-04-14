import logging

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
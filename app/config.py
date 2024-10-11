import sys
import os
from dotenv import load_dotenv
import logging

def load_configurations(app):
    load_dotenv()
    app.state.config = {
        "ACCESS_TOKEN": os.getenv("ACCESS_TOKEN"),
        "YOUR_PHONE_NUMBER": os.getenv("YOUR_PHONE_NUMBER"),
        "APP_ID": os.getenv("APP_ID"),
        "APP_SECRET": os.getenv("APP_SECRET"),
        "RECIPIENT_WAID": os.getenv("RECIPIENT_WAID"),
        "VERSION": os.getenv("VERSION"),
        "PHONE_NUMBER_ID": os.getenv("PHONE_NUMBER_ID"),
        "VERIFY_TOKEN": os.getenv("VERIFY_TOKEN"),
    }
    logging.info("Configurations loaded:")
    logging.info(app.state.config)  # Log the loaded configurations for debugging

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,

    )

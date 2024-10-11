import logging
import json
from fastapi import FastAPI, Request, HTTPException, Depends, Response
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)
from .decorators.security import signature_required

app = FastAPI()

@app.get("/")
async def home():
    """
    Home route to display a simple welcome message.
    """
    return "Welcome to the WhatsApp API!"


def handle_message(body):
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    """
    logging.info(f"Handling new message: {body}")

    try:
        if not body:
            logging.error("No JSON body found in the request")
            raise HTTPException(status_code=400, detail="No data provided")

        if is_valid_whatsapp_message(body):
            value = body["entry"][0]["changes"][0]["value"]
            if "messages" in value:
                logging.info("Processing message")
                process_whatsapp_message(body)
            elif "statuses" in value:
                logging.info("Received a status update")
                # Do not trigger message sending on status updates
            return {"status": "ok"}
        else:
            logging.error("Invalid WhatsApp API event structure")
            raise HTTPException(status_code=400, detail="Not a WhatsApp API event")
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON provided")
    except KeyError as e:
        logging.error(f"Missing expected key in the JSON data: {e}")
        raise HTTPException(status_code=400, detail=f"Malformed data provided: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.get("/webhook")
async def webhook_get(request: Request):
    """
    Verify the webhook with the token provided by WhatsApp.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
            logging.info("WEBHOOK_VERIFIED")
            return Response(content=challenge, media_type="text/plain")
        else:
            logging.info("VERIFICATION_FAILED")
            raise HTTPException(status_code=403, detail="Verification failed")
    else:
        logging.info("MISSING_PARAMETER")
        raise HTTPException(status_code=400, detail="Missing parameters")


@app.post("/webhook")
@signature_required  # Ensure your decorator is adapted for FastAPI
async def webhook_post(request: Request):
    try:
        body = await request.json()
        logging.info(f"Received WhatsApp message: {json.dumps(body, indent=4)}")

        # Extract the relevant data from the payload
        if "entry" in body:
            for entry in body["entry"]:
                for change in entry["changes"]:
                    if "value" in change and "messages" in change["value"]:
                        for message in change["value"]["messages"]:
                            from_id = message["from"]
                            message_body = message.get("text", {}).get("body", "")
                            sender_name = change["value"]["contacts"][0]["profile"].get("name", "Unknown")
                            
                            logging.info(f"Message from {sender_name} ({from_id}): {message_body}")
                            
                            # Process the message (e.g., send a response)
                            process_whatsapp_message(body)

                            return {"status": "success", "from": from_id, "message": message_body}

        return {"status": "no_message_found"}

    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON provided")
    except KeyError as e:
        logging.error(f"Missing expected key in the JSON data: {e}")
        raise HTTPException(status_code=400, detail=f"Malformed data provided: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


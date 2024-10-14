import logging
import json
from fastapi import Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse
from app.utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)
from app.decorators.security import signature_required
from app import app  # Import the app from __init__.py

@app.get("/")
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My Website</title>
    </head>
    <body>
        <h1>Hello world!</h1>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/webhook")
async def webhook_get(request: Request):
    verify_token = request.app.state.config.get("VERIFY_TOKEN")  # Access config correctly
    logging.info(f"VERIFY_TOKEN loaded: {verify_token}")

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logging.info(f"Mode: {mode}, Token: {token}, Challenge: {challenge}")

    if mode and token:
        if mode == "subscribe" and token == verify_token:
            logging.info("WEBHOOK_VERIFIED")
            return Response(content=challenge, media_type="text/plain")
        else:
            logging.error("Verification failed. Invalid token.")
            raise HTTPException(status_code=403, detail="Verification failed")
    else:
        logging.error("Missing parameters.")
        raise HTTPException(status_code=400, detail="Missing parameters")

processed_messages = set()  # Keep track of processed message IDs

@app.post("/webhook")
async def webhook_post(request: Request):
    try:
        body = await request.json()
        logging.info(f"Parsed JSON body: {json.dumps(body, indent=4)}")

        if "entry" in body:
            for entry in body["entry"]:
                for change in entry["changes"]:
                    if "value" in change and "messages" in change["value"]:
                        for message in change["value"]["messages"]:
                            message_id = message["id"]
                            
                            # Check if the message has already been processed
                            if message_id in processed_messages:
                                logging.info(f"Message {message_id} has already been processed. Skipping.")
                                continue

                            from_id = message["from"]
                            message_body = message.get("text", {}).get("body", "")
                            sender_name = change["value"]["contacts"][0]["profile"].get("name", "Unknown")

                            logging.info(f"Message from {sender_name} ({from_id}): {message_body}")

                            # Process the message here
                            await process_whatsapp_message(request, body)

                            # Mark this message as processed
                            processed_messages.add(message_id)

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

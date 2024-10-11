import logging
from fastapi import Request, HTTPException
import json
import requests
import re


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text, context):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "context": {
            "message_id": context
            },
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

import logging
from fastapi import Request, HTTPException

async def send_message(request: Request, data):
    config = request.app.state.config  # Access config once
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{config['VERSION']}/{config['PHONE_NUMBER_ID']}/messages"

    try:
        logging.info(f"Sending message with payload: {data}")
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        raise HTTPException(status_code=408, detail="Request timed out")
    except requests.RequestException as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        logging.error(f"Response content: {response.text}")
        raise HTTPException(status_code=500, detail="Failed to send message")
    else:
        return response.json()
    
def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"

    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


async def process_whatsapp_message(request: Request, body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    fname = name.split()[0]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_type = message["type"]

    # Check if the message is an interactive list reply
    if message_type == "interactive" and message["interactive"]["type"] == "list_reply":
        selected_option = message["interactive"]["list_reply"]["id"]

        if selected_option == "option1":  # The "Book a Consultation" option
            # First, send the text message
            response_message = "You have selected to book a consultation.\nPlease contact us to schedule your appointment."
            appointment_message = get_text_message_input(wa_id, response_message, message["id"])
            await send_message(request, appointment_message)

            # Then, send the contact info
            contact_info_message = get_contact_info(wa_id)
            await send_message(request, contact_info_message)

        elif selected_option == "option2":  # The "Book Online" option
            response_message = "You have selected *online booking*. \nPlease visit our website at https://www.exampleclinic.com/appointments to book your appointment online."
            online_booking_message = get_text_message_input(wa_id, response_message, message["id"])
            await send_message(request, online_booking_message)

        elif selected_option == "option3":  # The "Get Directions" option
            directions_message = get_text_message_input(wa_id, "Here is the link to our clinic:", message["id"])
            await send_message(request, directions_message)

            location_info_message = get_location(wa_id)
            await send_message(request, location_info_message)

        elif selected_option == "option4":  # The "Leave a Review" option
            response_message = "Loved our care? Let us know!\nGive us 5 stars to help us grow!"
            review_message = get_text_message_input(wa_id, response_message, message["id"])
            await send_message(request, review_message)

            ask_review_message = get_review(wa_id)
            await send_message(request, ask_review_message)

        elif selected_option == "option5":  # The "Request Refill" option
            response_message = "You have selected to request a prescription refill. Please reply with the medication name and dosage, or contact our pharmacy at 123-456-7890."
            refill_message = get_text_message_input(wa_id, response_message, message["id"])
            await send_message(request, refill_message)

        return

    # If it's the first interaction, directly send the interactive message
    interactive_message = get_interactive_message(wa_id, fname)
    await send_message(request, interactive_message)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    if "object" not in body or "entry" not in body:
        return False
    entry = body["entry"][0]
    if "changes" not in entry:
        return False
    change = entry["changes"][0]["value"]
    return "messages" in change or "statuses" in change


def get_interactive_message(recipient, fname):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": f" Hello {fname}, Welcome to Dr.Rajkannya's Clinic"
                },
                "body": {
                    "text": "Save time and manage your healthcare easily through WhatsApp."
                },
                "footer": {
                    "text": "👇 Choose an option to get started:"
                },
                "action": {
                    "button": "Explore Services",
                    "sections": [
                        {
                            "title": "Our Services",
                            "rows": [
                                {
                                    "id": "option1",
                                    "title": "📅 Book a Consultation",
                                    "description": "Schedule your consult today"
                                },
                                {
                                    "id": "option2",
                                    "title": "💻 Book Online",
                                    "description": "Quick and easy online booking"
                                },
                                {
                                    "id": "option3",
                                    "title": "📍 Get Directions",
                                    "description": "Find us with ease"
                                },
                                {
                                    "id": "option4",
                                    "title": "⭐ Leave a Review",
                                    "description": "Share your experience with us"
                                },
                                {
                                    "id": "option5",
                                    "title": "🔄 Request Refill",
                                    "description": "Easily request a prescription refill"
                                }  
                            ]
                        }
                    ]
                }
            }
        }
    )

def get_contact_info(recipient):
    return json.dumps(
        {
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": recipient,
    "type": "contacts",
    "contacts": [
                {
                    "name": {
                        "first_name": "Rajkannya",
                        "formatted_name": "Dr. Rajkannya Chandewar",
                        "last_name": "Chandewar"
                    },"phones": [
                        {
                            "phone": "+91 7030578661",
                            "type": "HOME",
                            "wa_id": "917030578661"
                        }
                    ]
                }
            ]
        }
    )

def get_location(recipient):
    return json.dumps(
       {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "context": {
                "message_id": "<MSGID_OF_PREV_MSG>"
            },
            "type": "location",
            "location": {
                "latitude": "21.13173300",
                "longitude": "79.09852990",
                "name": "Dr. Rajkannya's Homeopathy Clinic"
            }
        }
    )

def get_review(recipient):
    return json.dumps(
       {
            "messaging_product": "whatsapp",
            "to": recipient,
            "text": {
                "preview_url": "true",
                "body": "Please visit https://g.page/r/CWXu8ky3dBd3EBM/review"
            }
        }
    )
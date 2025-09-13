import base64
import os
from datetime import date
from email.mime.text import MIMEText

import requests
from auth0_ai.authorizers.federated_connection_authorizer import \
    get_access_token_for_connection
from auth0_ai_langchain.auth0_ai import Auth0AI
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

load_dotenv()
auth0_ai = Auth0AI()

with_send_email_gmail = auth0_ai.with_federated_connection(
    connection="google-oauth2",
    scopes=["https://www.googleapis.com/auth/gmail.send"],
)


def send_email(to_email: str, subject: str, body: str) -> str:
    try:
        gmail_access_token = get_access_token_for_connection()
        message = MIMEText(body)
        message["to"] = to_email
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        response = requests.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={
                "Authorization": f"Bearer {gmail_access_token}",
                "Content-Type": "application/json",
            },
            json={"raw": raw_message},
        )
        response.raise_for_status()
        sent_message = response.json()
        return (
            f"Email sent successfully to {to_email}. Message ID: {sent_message['id']}"
        )
    except Exception as e:
        return f"Unexpected error sending email: {e}"


class AskVeterinarianSuppliesArgs(BaseModel):
    medicine_description: str = Field(..., description="Description of the medicine")
    quantity: int = Field(..., description="Quantity of the medicine")
    due_date: date = Field(..., description="Due date of the medicine")
    animal_id: str = Field(..., description="ID of the animal to take the medicine")


def ask_for_veterianarian_supplies(
    medicine_description: str, quantity: int, due_date: date, animal_id: str
) -> str:
    return send_email(
        to_email=os.getenv("VETERINARIAN_SUPPLIES_EMAIL"),
        subject=f"Medicine request for animal {animal_id}",
        body=f"Medicine request for animal {animal_id}:\n\n"
        f"Medicine description: {medicine_description}"
        f"\nQuantity: {quantity}"
        f"\nDue date: {due_date}",
    )


ask_for_veterinarian_supplies_tool = with_send_email_gmail(
    StructuredTool.from_function(
        func=ask_for_veterianarian_supplies,
        name="ask_for_medical_supplies",
        description="Veterinarians can ask for supplies to be delivered to an animal.",
        args_schema=AskVeterinarianSuppliesArgs,
    )
)


class AskCleaningSuppliesArgs(BaseModel):
    supplies_description: str = Field(..., description="Description of the supplies")
    location: str = Field(..., description="Location of to deliver")
    due_date: date = Field(..., description="Due date of the supplies")


def ask_for_cleaning_supplies(
    supplies_description: str,
    location: str,
    due_date: date,
) -> str:
    return send_email(
        to_email=os.getenv("CLEANING_SUPPLIES_EMAIL"),
        subject=f"Cleaning supplies request location {location}",
        body=f"Cleaning supplies request for location {location}:\n"
        f"\nSupplies description: {supplies_description}"
        f"\nLocation: {location}"
        f"\nDue date: {due_date}",
    )


ask_for_cleaning_supplies_tool = with_send_email_gmail(
    StructuredTool.from_function(
        func=ask_for_cleaning_supplies,
        name="ask_for_cleaning_supplies",
        description="Zookeepers can ask for cleaning supplies to be delivered to a specific location.",
        args_schema=AskCleaningSuppliesArgs,
    )
)

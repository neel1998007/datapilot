import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

client = Client(TWILIO_SID, TWILIO_AUTH)


def send_whatsapp_message(to_number, message):
    """Send a WhatsApp message using Twilio"""

    # WhatsApp has 1600 character limit per message
    # Split long messages into chunks
    chunks = split_message(message, 1500)

    for i, chunk in enumerate(chunks):
        msg = client.messages.create(
            body=chunk,
            from_=TWILIO_PHONE,
            to=to_number
        )
        print(f"Message {i+1}/{len(chunks)} sent! SID: {msg.sid}")

    return True


def split_message(message, max_length=1500):
    """Split long message into smaller chunks"""

    if len(message) <= max_length:
        return [message]

    chunks = []
    current_chunk = ""

    lines = message.split("\n")

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def send_scaling_report(to_number, report_text):
    """Send the full DataPilot scaling report"""

    print(f"Sending DataPilot report to {to_number}...")
    success = send_whatsapp_message(to_number, report_text)

    if success:
        print("Report sent successfully!")
    else:
        print("Failed to send report.")

    return success


if __name__ == "__main__":
    print("Testing WhatsApp sender...")
    print(f"Sending to: {MY_PHONE}")

    test_message = """📊 *DataPilot Test Message*

This is a test from DataPilot.

If you received this, WhatsApp integration is working!

✅ Connection successful
🚀 Ready to send scaling reports

_Powered by DataPilot_"""

    send_whatsapp_message(MY_PHONE, test_message)
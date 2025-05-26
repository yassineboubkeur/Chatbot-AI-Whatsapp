import requests
import os
from io import BytesIO
import logging
from openai import OpenAI
from models.tenant import Tenant

from config import WHATSAPP_TOKEN, OPENAI_API_KEY

def transcribe_audio(bytesAudio):

    if not bytesAudio:
        logging.error("No audio data provided for transcription")
        return None

    try:
        if not OPENAI_API_KEY:
            logging.error("OpenAI API key not found in environment variables")
            return None

        client  = OpenAI(api_key=OPENAI_API_KEY)

        bytesAudio.seek(0)

        temp_file_path = "/tmp/temp_audio_file.mp3"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(bytesAudio.getvalue())

        with open(temp_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )

        os.remove(temp_file_path)

        return transcript.text

    except Exception as e:
        logging.error(f"Error transcribing audio: {str(e)}")
        return None


def download_whatsapp_media(media_id):
    """
    Download media from WhatsApp using the WhatsApp Business API

    Args:
        media_id (str): The ID of the media to download

    Returns:
        BytesIO: The binary content of the media file as a file-like object
                or None if download failed
    """

    if not WHATSAPP_TOKEN:
        logging.error("WhatsApp access token not found in environment variables")
        return None

    # Step 1: Get the media URL
    url = f"https://graph.facebook.com/v18.0/{media_id}"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logging.error(f"Failed to get media URL. Status: {response.status_code}, Response: {response.text}")
            return None

        media_data = response.json()

        if 'url' not in media_data:
            logging.error(f"Media URL not found in response: {media_data}")
            return None

        media_url = media_data['url']

        media_response = requests.get(media_url, headers=headers)

        if media_response.status_code != 200:
            logging.error(f"Failed to download media. Status: {media_response.status_code}")
            return None

        # Return the media content as a file-like object
        return BytesIO(media_response.content)

    except Exception as e:
        logging.error(f"Error downloading media: {str(e)}")
        return None



def validate_message(msg):
    if not msg or len(msg.strip()) < 3:
        return False
    if len(msg) > 500:
        return False
    return True

def is_audio_message(data):
    try:
        if 'entry' in data and data['entry']:
            for entry in data['entry']:
                if 'changes' in entry and entry['changes']:
                    for change in entry['changes']:
                        if 'value' in change and 'messages' in change['value']:
                            for message in change['value']['messages']:
                                if message.get('type') == 'audio':
                                    return True
        return False
    except Exception:
        # If any error occurs during extraction, assume it's not an audio message
        return False


def extract_audio_data(data):
    """
    Extract the audio data from a WhatsApp audio message.

    Args:
        data (dict): The webhook payload from WhatsApp

    Returns:
        dict: Dictionary containing audio information or None if not found
    """
    try:
        for entry in data['entry']:
            for change in entry['changes']:
                if 'value' in change and 'messages' in change['value']:
                    for message in change['value']['messages']:
                        if message.get('type') == 'audio':
                            return {
                                'id': message['audio'].get('id'),
                                'mime_type': message['audio'].get('mime_type'),
                                'is_voice': message['audio'].get('voice', False),
                                'message_id': message.get('id'),
                                'from': message.get('from')
                            }
        return None
    except Exception:
        return None



def extract_client_phone(data):
    """Extract the client's phone number from WhatsApp webhook data"""
    try:
        # Check if the necessary elements exist in the data
        if (data.get('object') == 'whatsapp_business_account' and
                data.get('entry') and
                len(data['entry']) > 0 and
                data['entry'][0].get('changes') and
                len(data['entry'][0]['changes']) > 0):

            # Navigate to the contacts array
            value = data['entry'][0]['changes'][0].get('value', {})
            contacts = value.get('contacts', [])

            # Check if there are any contacts
            if contacts and len(contacts) > 0:
                # Get the wa_id (WhatsApp ID/phone number)
                return contacts[0].get('wa_id')

        return None  # Return None if no phone number found
    except Exception as e:
        print(f"Error extracting client phone: {e}")
        return None


def extract_whatsapp_message(data):
    """Extract the message text from WhatsApp webhook data"""
    try:
        # Check if the necessary elements exist in the data
        if (data.get('object') == 'whatsapp_business_account' and
                data.get('entry') and
                len(data['entry']) > 0 and
                data['entry'][0].get('changes') and
                len(data['entry'][0]['changes']) > 0):

            # Navigate to the messages array
            value = data['entry'][0]['changes'][0].get('value', {})
            messages = value.get('messages', [])

            # Check if there are any messages
            if messages and len(messages) > 0:
                # Get the message type
                message_type = messages[0].get('type')

                # Handle different message types
                if message_type == 'text' and 'text' in messages[0]:
                    # Extract the text message
                    return messages[0]['text'].get('body', '')
                elif message_type == 'image':
                    return '[IMAGE]'  # Or handle image message differently
                elif message_type == 'document':
                    return '[DOCUMENT]'  # Or handle document message differently
                # Add more message types as needed

        return None  # Return None if no message found
    except Exception as e:
        print(f"Error extracting message: {e}")
        return None


def format_response(products):

    return 1


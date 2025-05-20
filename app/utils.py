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


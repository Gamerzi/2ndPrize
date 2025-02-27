from twilio.rest import Client

def send_call():
    # Twilio credentials (replace with your actual credentials)
    account_sid = 'ACc76f71b7f5263355311640ce8a076734'
    auth_token = '6728f552f807a82f8c3d6b97c8084138'
    twilio_number = '+15393525165'
    to_number = '+917207581690'  # Replace with the target phone number

    client = Client(account_sid, auth_token)

    # Define the TwiML response inline.
    twiml_response = '<Response><Say voice="alice" language="en-US">I need to get the hospital now.</Say></Response>'

    try:
        # Initiate the call using the inline TwiML.
        call = client.calls.create(
            twiml=twiml_response,
            to=to_number,
            from_=twilio_number
        )
        print("Call initiated, SID:", call.sid)
    except Exception as e:
        print("Error initiating call:", e)

if __name__ == "__main__":
    send_call()
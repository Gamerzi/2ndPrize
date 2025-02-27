
'''
from flask import Flask, request, jsonify, render_template, Response
from twilio.rest import Client
import pywhatkit

app = Flask(__name__)

##########################
# Twilio Configuration
##########################

client = Client(account_sid, auth_token)

##########################
# Target Phone (for WhatsApp and Call)
##########################
TARGET_PHONE = '+917207581690'

##########################
# Routes
##########################

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_all', methods=['POST'])
def send_all():
    responses = {}

    # Send WhatsApp message using pywhatkit
    try:
        pywhatkit.sendwhatmsg_instantly(
            TARGET_PHONE,
            "I need to get the hospital now",
            wait_time=10,
            tab_close=True,
            close_time=3
        )
        responses['whatsapp'] = "WhatsApp message sent successfully."
    except Exception as e:
        responses['whatsapp'] = f"WhatsApp sending failed: {e}"

    # Trigger automated call using Twilio
    try:
        call = client.calls.create(
            url='http://your-public-domain.com/voice',  # Replace with your public URL (e.g., via ngrok)
            to=TARGET_PHONE,
            from_=twilio_number
        )
        responses['call'] = f"Call initiated, SID: {call.sid}"
    except Exception as e:
        responses['call'] = f"Call initiation failed: {e}"

    overall_message = "Server actions:\n" + "\n".join([f"{k}: {v}" for k, v in responses.items()])
    return jsonify({'message': overall_message})

@app.route('/voice', methods=['GET', 'POST'])
def voice():
    from twilio.twiml.voice_response import VoiceResponse
    resp = VoiceResponse()
    resp.say("I need to get the hospital now.", voice="alice", language="en-US")
    return Response(str(resp), mimetype='application/xml')

@app.route('/help')
def help_page():
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=True, port=8000)
'''
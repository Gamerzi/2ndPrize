
'''
from flask import Flask, Response, request, render_template_string
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client

app = Flask(__name__)

# Your provided Twilio credentials
account_sid = 'ACc76f71b7f5263355311640ce8a076734'
auth_token = '6728f552f807a82f8c3d6b97c8084138'
twilio_number = '+15393525165'

client = Client(account_sid, auth_token)

# Optional: A simple homepage with a button to trigger the call
@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Automated Call</title>
    </head>
    <body>
      <h1>Make Automated Call</h1>
      <button id="callBtn">Make Call</button>
      <script>
        document.getElementById("callBtn").addEventListener("click", function() {
          fetch("/make_call", { method: "POST" })
            .then(response => response.text())
            .then(text => alert(text))
            .catch(error => console.error(error));
        });
      </script>
    </body>
    </html>
    """)

@app.route('/make_call', methods=['POST'])
def make_call():
    # Hard-coded target phone number (ensure this is verified if on a trial account)
    to_number = '+917207581690'  # Replace with your target phone number
    
    # IMPORTANT: Update the URL to a publicly accessible URL using ngrok or similar.
    call = client.calls.create(
        url='https://your-public-domain.com/voice',  # Replace with your public URL, e.g., https://abcd1234.ngrok.io/voice
        to=to_number,
        from_=twilio_number
    )
    
    return f"Call initiated, SID: {call.sid}"

@app.route('/voice', methods=['GET', 'POST'])
def voice():
    # Create a TwiML response that speaks your message.
    resp = VoiceResponse()
    resp.say("I need to get the hospital now.", voice="alice", language="en-US")
    return Response(str(resp), mimetype='application/xml')

if __name__ == '__main__':
    app.run(debug=True)

'''

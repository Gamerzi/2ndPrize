
'''
from flask import Flask, render_template, request, jsonify
import pywhatkit

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    phone = request.form.get('phone')
    try:
        # Using sendwhatmsg_instantly to try to send the message immediately.
        # Note: wait_time is the seconds to wait after opening WhatsApp Web before sending.
        pywhatkit.sendwhatmsg_instantly(phone, "I need to get the hospital now", wait_time=10, tab_close=True, close_time=3)
        return jsonify({'status': 'success', 'message': 'Message sent!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

'''

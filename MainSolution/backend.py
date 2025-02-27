import os
import datetime
import inspect
import logging
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import pywhatkit
import requests

# Set up logging for debugging.
logging.basicConfig(level=logging.DEBUG)

# --- PHI Agent Setup ---
try:
    from phi.agent import Agent, RunResponse
    from phi.model.base import Model as PhiModel
    from phi.tools.duckduckgo import DuckDuckGo
    from phi.tools.newspaper4k import Newspaper4k
except ImportError:
    # Dummy agent for demonstration if PHI modules are not installed.
    class RunResponse:
        def __init__(self, content):
            self.content = content

    class DummyAgent:
        def run(self, prompt):
            dummy_output = {
                "medicines": [
                    {"name": "Paracetamol", "dosage": "500mg", "time": "08:00"},
                    {"name": "Ibuprofen", "dosage": "200mg", "time": "20:00"}
                ]
            }
            return RunResponse(content=str(dummy_output))
    Agent = DummyAgent

if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

# Load environment variables.
load_dotenv()

class GroqLLM(PhiModel):
    id: str
    api_key: str
    temperature: float = 0.1
    max_tokens: int = 8000

    def generate(self, prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            json_data = response.json()
            try:
                return json_data["choices"][0]["message"]["content"]
            except Exception as e:
                return f"Error extracting response: {e}"
        else:
            return f"Error: {response.status_code} {response.text}"

    def response(self, messages: list) -> RunResponse:
        prompt = "\n".join([getattr(msg, "content", str(msg)) for msg in messages])
        generated_text = self.generate(prompt)
        return RunResponse(content=generated_text)

groq_model = GroqLLM(id="llama3-8b-8192", api_key=os.getenv("GROQ_API_KEY"))

medical_report_agent = Agent(
    model=groq_model,
    description=(
        "You are a medical data analyzer. Given a prescription text, extract all medicine details "
        "such as medicine name, dosage, and scheduled time of intake. Return the result as a JSON object "
        "with a key 'medicines' containing an array of objects. For example: "
        "{'medicines': [{'name': 'Paracetamol', 'dosage': '500mg', 'time': '08:00'}, ...]}"
    ),
    instructions=[
        "Extract each medicine's name, dosage, and timing from the text.",
        "Provide a brief summary of the medicine and what precausions should be taken while consumption"
        "Return the result as JSON."
    ],
    markdown=True,
    show_tool_calls=True,
    add_datetime_to_instructions=True,
)

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# New endpoint: Extract text from the uploaded prescription image using Google Cloud Vision.
@app.route('/extract_prescription', methods=['POST'])
def extract_prescription():
    if 'file' not in request.files:
        app.logger.error("No file provided.")
        return jsonify({"error": "No file provided."}), 400
    file = request.files['file']
    content = file.read()

    try:
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        extracted_text = ""
        if response.full_text_annotation:
            extracted_text = response.full_text_annotation.text
        if response.error.message:
            app.logger.error(f"Vision API error: {response.error.message}")
            return jsonify({"error": response.error.message}), 500

        app.logger.debug(f"Extracted text: {extracted_text}")
        return jsonify({"extractedText": extracted_text})
    except Exception as e:
        app.logger.exception("Error during text extraction.")
        return jsonify({"error": str(e)}), 500

# Process the extracted prescription text.
@app.route('/process_prescription', methods=['POST'])
def process_prescription():
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        app.logger.error("No prescription text provided.")
        return jsonify({"error": "No prescription text provided."}), 400
    try:
        response = medical_report_agent.run(text)
        app.logger.debug(f"Agent raw response: {response.content}")
        content = response.content.strip()
        
        if not content:
            raise ValueError("Empty response from medical_report_agent")
        
        json_start_marker = "```json"
        json_end_marker = "```"
        start_idx = content.find(json_start_marker)
        end_idx = content.find(json_end_marker, start_idx + len(json_start_marker))
        
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx + len(json_start_marker):end_idx].strip()
            app.logger.debug(f"Extracted JSON string: {json_str}")
            result = json.loads(json_str)
        else:
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                app.logger.debug("JSON decode failed, attempting to fix single quotes.")
                fixed_content = content.replace("'", "\"")
                result = json.loads(fixed_content)
        
        return jsonify(result)
    except Exception as e:
        app.logger.exception("Failed to process prescription.")
        return jsonify({
            "error": "Failed to parse AI response", 
            "content": response.content, 
            "exception": str(e)
        }), 500

@app.route('/send_whatsapp', methods=['POST'])
def send_whatsapp():
    data = request.get_json()
    medicine = data.get('medicine')
    time_str = data.get('time')
    phone_number = os.getenv("WHATSAPP_PHONE_NUMBER")
    message = f"Reminder: It's time to take your medicine: {medicine}"
    now = datetime.datetime.now()
    send_time = now + datetime.timedelta(minutes=1)
    try:
        pywhatkit.sendwhatmsg(phone_number, message, send_time.hour, send_time.minute)
        return jsonify({"status": "success", "message": "WhatsApp reminder scheduled."})
    except Exception as e:
        app.logger.exception("Failed to schedule WhatsApp reminder.")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

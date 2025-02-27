import inspect
import collections

# Monkey-patch inspect.getargspec to support older usage if needed.
if not hasattr(inspect, 'getargspec'):
    ArgSpec = collections.namedtuple('ArgSpec', ['args', 'varargs', 'keywords', 'defaults'])
    def getargspec(func):
        spec = inspect.getfullargspec(func)
        return ArgSpec(spec.args, spec.varargs, spec.varkw, spec.defaults)
    inspect.getargspec = getargspec

import os
import datetime
import logging
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import pymongo
import requests
from werkzeug.utils import secure_filename
import base64
from PIL import Image
import io
from google.cloud import vision
from bson.objectid import ObjectId

# --- PHI Imports (using latest phi) ---
from phi.agent import Agent, RunResponse
from phi.model.base import Model as PhiModel

load_dotenv()

# --- Database Setup ---
try:
    MONGO_URI = os.getenv("MONGODB_URI")
    client = pymongo.MongoClient(
        MONGO_URI,
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        maxPoolSize=50,  # Add connection pooling
        retryWrites=True
    )
    
    db = client["medical_db"]
    collection = db["patients"]
    
    # Create indexes for faster queries
    collection.create_index([("name", pymongo.ASCENDING)])
    collection.create_index([("created_at", pymongo.DESCENDING)])
    
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

# --- Agent Setup ---
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
        "You are a medical data analyzer. Given the prescription data, extract all medicine details "
        "such as medicine name, dosage, and scheduled time of intake. Return the result as JSON with a key "
        "'medicines' containing an array of objects."
    ),
    instructions=[
        "Extract each medicine's name, dosage, and timing from the data.",
        "Provide a brief summary and any precautions related to each medicine.",
        "Return the result as text file"
    ],
    markdown=True,
    show_tool_calls=True,
    add_datetime_to_instructions=True,
)

# --- Flask Setup ---
app = Flask(__name__)
CORS(app)

# Add these configurations after creating the Flask app
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Add this after your imports
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './config/nomadic-entry-451513-q4-c65ad06a6e7c.json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def optimize_image(image_file):
    # Open the image
    img = Image.open(image_file)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize if too large (e.g., max 1024px width)
    max_size = 1024
    if img.width > max_size:
        ratio = max_size / img.width
        height = int(img.height * ratio)
        img = img.resize((max_size, height), Image.Resampling.LANCZOS)
    
    # Save with optimized settings
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)
    return buffer.getvalue()

def extract_text_from_image(image_content):
    """Extract text from image using Google Cloud Vision API"""
    try:
        # Create a client
        client = vision.ImageAnnotatorClient()

        # Create image object
        image = vision.Image(content=image_content)

        # Perform text detection
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if texts:
            return texts[0].description
        return ""

    except Exception as e:
        print(f"Error in OCR: {e}")
        return ""

@app.route('/submit_prescription', methods=['POST'])
def submit_prescription():
    try:
        name = request.form.get('name')
        age = request.form.get('age')
        prescription_text = request.form.get('prescription')
        
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
            
        image_file = request.files['image']
        if image_file.filename == '' or not allowed_file(image_file.filename):
            return jsonify({"error": "Invalid file"}), 400

        # Read image content for OCR
        image_content = image_file.read()
        
        # Extract text using Google Cloud Vision
        extracted_text = extract_text_from_image(image_content)
        print(f"Extracted text: {extracted_text}")  # Debug print

        # Reset file pointer and optimize image for storage
        image_file.seek(0)
        optimized_image = optimize_image(image_file)
        image_base64 = base64.b64encode(optimized_image).decode('utf-8')

        # Prepare prompt for AI analysis
        agent_prompt = f"""
        Analyze this medical prescription and provide a clear, readable summary:

        Patient Information:
        Name: {name}
        Age: {age}

        Manual Prescription Text:
        {prescription_text}

        Extracted Text from Prescription Image:
        {extracted_text}

        Please provide the analysis in the following format:

        MEDICINES:
        - [Medicine Name]
          Dosage: [amount]
          Schedule: [when to take]
          Precautions: [specific precautions]
          Side Effects: [possible side effects]
          
        GENERAL PRECAUTIONS:
        [List overall precautions and important notes]

        NEXT CHECKUP:
        [Recommended next visit date if mentioned]
        """

        # Get AI analysis
        response = medical_report_agent.run(agent_prompt)
        ai_analysis = response.content.strip()

        # Store in MongoDB
        data = {
            "name": name,
            "age": int(age),
            "prescription_text": prescription_text,
            "extracted_text": extracted_text,
            "prescription_image": image_base64,
            "ai_analysis": ai_analysis,
            "created_at": datetime.datetime.utcnow()
        }

        insert_result = collection.insert_one(data)
        
        # Return the redirect URL with the correct path
        return jsonify({
            "redirect": f"/analysis/{str(insert_result.inserted_id)}"
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/analysis/<prescription_id>')
def analysis(prescription_id):
    try:
        # Fetch prescription data from MongoDB
        prescription = collection.find_one({"_id": ObjectId(prescription_id)})
        if not prescription:
            return "Prescription not found", 404
        
        # Prepare data for template
        data = {
            "name": prescription["name"],
            "age": prescription["age"],
            "extracted_text": prescription["extracted_text"],
            "analysis": prescription["ai_analysis"]  # Use the raw text directly
        }
        
        return render_template('analysis.html', data=data)
    except Exception as e:
        print(f"Error displaying analysis: {e}")
        return f"Error displaying analysis: {str(e)}", 500

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import time
import mtranslate as mt
from selenium.webdriver.support.ui import WebDriverWait

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

InputLanguage = "en"

# Define the complete HTML code for the speech recognition interface.
# All literal curly braces in the HTML/JS code are doubled ({{ and }}) except for the placeholder {lang}.
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        // Check if the SpeechRecognition API is supported
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{
            document.getElementById("output").innerText = "Speech Recognition not supported in this browser.";
        }} else {{
            var recognition = new SpeechRecognition();
            recognition.lang = '{lang}';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onresult = function(event) {{
                // When a result is returned, update the output element with the transcript
                document.getElementById("output").innerText = event.results[0][0].transcript;
            }};

            recognition.onerror = function(event) {{
                console.error("Speech recognition error:", event.error);
            }};

            function startRecognition() {{
                document.getElementById("output").innerText = "";
                recognition.start();
            }}

            function stopRecognition() {{
                recognition.stop();
            }}
        }}
    </script>
</body>
</html>'''.format(lang=InputLanguage)

# Write the modified HTML code to a file.
html_file_path = os.path.join("Data", "Voice.html")
os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
with open(html_file_path, "w", encoding="utf-8") as f:
    f.write(HtmlCode)

# Get the current working directory.
current_dir = os.getcwd()
# Generate the file URL for the HTML file (ensure forward slashes).
Link = f"file:///{current_dir.replace(os.sep, '/')}/Data/Voice.html"

# Set Chrome options
chrome_options = Options()
user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/89.0.142.86 Safari/537.36")
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")

# Initialize the Chrome WebDriver using the ChromeDriverManager.
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Define the path for temporary files.
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
os.makedirs(TempDirPath, exist_ok=True)

# Function to set the assistant's status by writing it to a file.
def SetAssistantStatus(Status):
    status_file = os.path.join(TempDirPath, "Status.data")
    with open(status_file, "w", encoding='utf-8') as file:
        file.write(Status)

# Function to modify a query to ensure proper punctuation and formatting.
def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why",
                      "which", "whose", "whom", "can you", "what's", "wh"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    return new_query.capitalize()

# Function to translate text into English using the mtranslate library.
def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

# Function to perform speech recognition using the WebDriver.
def SpeechRecognition():
    # Open the HTML file in the browser.
    driver.get(Link)
    driver.find_element(By.ID, "start").click()
    
    try:
        # Wait until the output element's text is non-empty (polling every 0.1 sec)
        recognized_text = WebDriverWait(driver, 10, poll_frequency=0.1).until(
            lambda d: d.find_element(By.ID, "output").text.strip() or None
        )
        driver.find_element(By.ID, "end").click()
        if InputLanguage.lower() == "en":
            return QueryModifier(recognized_text)
        else:
            SetAssistantStatus("Translating... ")
            return QueryModifier(UniversalTranslator(recognized_text))
    except Exception as e:
        try:
            driver.find_element(By.ID, "end").click()
        except Exception:
            pass
        return ""

# Main execution block.
if __name__ == "__main__":
    try:
        while True:
            recognized_text = SpeechRecognition()
            if recognized_text:
                print("Recognized:", recognized_text)
            else:
                print("No speech recognized. Retrying...")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        driver.quit()

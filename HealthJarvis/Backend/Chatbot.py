from groq import Groq  # Import the Groq library to use its API.
from json import load, dump  # For reading and writing JSON files.
import datetime  # For real-time date and time.
from dotenv import dotenv_values  # To read environment variables from a .env file.
import os  # For file and directory operations.

# Ensure the "Data" directory exists.
os.makedirs("Data", exist_ok=True)

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

# Retrieve specific environment variables for username, assistant name, and API key.
Username = "Baqer Ali"
Assistantname = "Jarvis"
GroqAPIKey = "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"

# Initialize the Groq client using the provided API key.
client = Groq(api_key=GroqAPIKey)

# Define a system message that provides context to the AI chatbot about its role and behavior.
System = f"""Hello, I am {Username}. You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

# Create a system prompt message list.
SystemChatBot = [
    {"role": "system", "content": System}
]

# Define the full path for the ChatLog.json file.
chatlog_path = os.path.join("Data", "ChatLog.json")

# Attempt to open the chat log file; if it doesn't exist, create an empty JSON file.
try:
    with open(chatlog_path, "r") as f:
        messages = load(f)  # Load existing messages from the chat log.
except FileNotFoundError:
    with open(chatlog_path, "w") as f:
        dump([], f)
    messages = []

# Function to get real-time date and time information.
def RealTimeInformation():
    current_date_time = datetime.datetime.now()  # Get the current date and time.
    day = current_date_time.strftime("%A")  # Day of the week.
    date = current_date_time.strftime("%d")  # Day of the month.
    month = current_date_time.strftime("%B")  # Full month name.
    year = current_date_time.strftime("%Y")  # Year.
    hour = current_date_time.strftime("%H")  # Hour in 24-hour format.
    minute = current_date_time.strftime("%M")  # Minute.
    second = current_date_time.strftime("%S")  # Second.
    data = f"Real-Time Info:\nDay: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\nTime: {hour} hours : {minute} minutes : {second} seconds.\n"
    return data

# Function to modify the chatbot's response for better formatting.
def AnswerModifier(Answer):
    lines = Answer.split('\n')  # Split the response into lines.
    non_empty_lines = [line for line in lines if line.strip()]  # Remove empty lines.
    modified_answer = '\n'.join(non_empty_lines)  # Join the cleaned lines.
    return modified_answer

# Main chatbot function to handle user queries.
def ChatBot(Query):
    """This function sends the user's query to the chatbot and returns the AI's response."""
    try:
        # Load the existing chat log.
        with open(chatlog_path, "r") as f:
            messages = load(f)
        
        # Append the user's query to the messages list.
        messages.append({"role": "user", "content": f"{Query}"})
        
        # Build the complete context: system instructions (with username/assistant name),
        # real-time info, and prior chat messages.
        context = SystemChatBot + [{"role": "system", "content": RealTimeInformation()}] + messages[-10:]


        # Make a request to the Groq API for a response.
        completion = client.chat.completions.create(
            model="llama3-70b-8192",  # Specify the AI model.
            messages=context,         # Pass the complete context.
            temperature=0.7,          # Set response randomness.
            top_p=1,                  # Control token selection diversity.
            stream=True,              # Enable streaming responses.
            stop=None                 # Let the model decide when to stop.
        )

        Answer = ""
        # Process the streamed response.
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
        
        Answer = Answer.replace("^x", "")  # Clean up any unwanted tokens.
        
        # Append the AI's response to the messages.
        messages.append({"role": "assistant", "content": Answer})
        
        # Save the updated chat log.
        with open(chatlog_path, "w") as f:
            dump(messages, f)
        
        return AnswerModifier(Answer)
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Sorry, an error occurred: {e}"

# Main entry point for the script.
if __name__ == "__main__":
    while True:
        try:
            user_input = input("User:")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                break
            response = ChatBot(user_input)
            print("Chart Bot:",response)
        except KeyboardInterrupt:
            print("\nExiting the chatbot...")
            break

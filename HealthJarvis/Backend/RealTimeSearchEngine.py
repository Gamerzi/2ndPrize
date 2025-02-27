from groq import Groq  # Import the Groq library to use its API.
from json import load, dump  # For reading and writing JSON files.
import datetime  # For real-time date and time.
from dotenv import dotenv_values  # To read environment variables from a .env file.
import os  # For file and directory operations.
from googlesearch import search  # Ensure this library is installed.

# Ensure the "Data" directory exists.
os.makedirs("Data", exist_ok=True)

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

# Retrieve specific environment variables for username, assistant name, and API key.
Username = "Baqer Ali"
Assistantname = "Jarvis"
GroqAPIKey = ""

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
        messages = load(f)
except FileNotFoundError:
    with open(chatlog_path, "w") as f:
        dump([], f)
    messages = []

# Function to perform a Google search and format the results.
def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=5))
    Answer = f"The search results for '{query}' are:\n[start]\n"
    for i in results:
        Answer += f"Title: {i.title}\nDescription: {i.description}\n\n"
    Answer += "[end]"
    print(Answer)
    return Answer

# Function to modify the chatbot's response for better formatting.
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

# Function to get real-time date and time information.
def RealTimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data = (f"Real-Time Info:\nDay: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
            f"Time: {hour} hours, {minute} minutes, {second} seconds.\n")
    return data

# Helper function: trim the chat history to only the most recent entries.
def trim_chat_history(history, max_entries=5):
    return history[-max_entries:]

# Function to handle real-time search and response generation.
def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages
    
    # Load the chat log.
    with open(chatlog_path, "r") as f:
        messages = load(f)
    
    # Append the user's query.
    messages.append({"role": "user", "content": f"[{prompt}"})
    
    # Append Google search results to SystemChatBot.
    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})
    
    # Build the context using trimmed chat history.
    trimmed_messages = trim_chat_history(messages, max_entries=5)
    context = SystemChatBot + [{"role": "system", "content": RealTimeInformation()}] + trimmed_messages

    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=context,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True,
            stop=None
        )
    except Exception as e:
        print("Error in completion:", e)
        return AnswerModifier("Error generating response.")
    
    Answer = ""
    # Concatenate response chunks.
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content
    
    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})
    
    # Save the updated chat log.
    with open(chatlog_path, "w") as f:
        dump(messages, f, indent=4)
    
    # Remove the most recent system message (Google search result) from SystemChatBot.
    if len(SystemChatBot) > 1:
        SystemChatBot.pop()
    
    return AnswerModifier(Answer)

if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ").strip()
        if not prompt:
            continue  # Do nothing for empty input.
        print(RealtimeSearchEngine(prompt))

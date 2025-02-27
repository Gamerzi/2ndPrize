# Import required libraries
from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
GroqAPIKey = "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"

# Define CSS classes for parsing specific elements in HTML content.
classes = [
    "zCubwf", "hgKElc", "LTKOO sY7ric", "Z0lcW", "gsrt vk_bk FzvWSb YwPhnf",
    "pclqee", "tw-Data-text tw-text-small tw-ta", "IZ6rdc", "O5uR6d LTKOO",
    "vlzY6d", "webanswers-webanswers_table__webanswers-table",
    "dDoNo ikb4Bb gsrt", "sXLaOe", "LWkfke", "vQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"
]

# Define a user-agent for making web requests.
useragent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
             'AppleWebKit/537.36 (KHTML, like Gecko) '
             'Chrome/100.0.4896.75 Safari/537.36')

# Initialize the Groq client with the API key.
client = Groq(api_key=GroqAPIKey)

# Predefined professional responses for user interactions.
professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask.",
]

# List to store chatbot messages.
messages = []

# System message to provide context to the chatbot.
# Using os.environ.get to avoid KeyError if 'Username' is not set.
SystemChatBot = [{
    "role": "system",
    "content": f"Hello, I am {os.environ.get('Username', 'User')}, You're a content writer. You have to write content like letter"
}]

# Function to perform a Google search.
def GoogleSearch(Topic):
    search(Topic)
    return True

# Function to generate content using AI and save it to a file.
def Content(Topic):
    def OpenNotepad(File):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, File])

    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )
        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer  # Return the generated content

    Topic = Topic.replace("Content ", "")
    ContentByAI = ContentWriterAI(Topic)
    file_path = rf"Data\{Topic.lower().replace(' ', '')}.txt"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(ContentByAI)
    OpenNotepad(file_path)
    return True

# Function to search for a video on YouTube.
def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

# Function to play a video on YouTube.
def PlayYoutube(query):
    playonyt(query)
    return True

# Function to open an application or a relevant webpage.
def OpenApp(app, sess=requests.session()):
    # Fallback mapping for known web-based apps
    fallback_urls = {
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "telegram": "https://web.telegram.org",
        "youtube": "https://www.youtube.com"
        # Add more mappings if necessary
    }
    app_lower = app.lower().strip()
    if app_lower in fallback_urls:
        webopen(fallback_urls[app_lower])
        return True

    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception as e:
        print(f"appopen failed for '{app}' with error: {e}")
        # Fallback: Use Google search to open results for any topic.
        query_url = f"https://www.google.com/search?q={app}"
        webopen(query_url)
        return True

# Function to perform system-related actions.
def System(command):
    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume mute")

    def volume_up():
        keyboard.press_and_release("volume up")

    def volume_down():
        keyboard.press_and_release("volume down")

    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()
    return True

# Function to close an application.
def CloseApp(app):
    if "chrome" in app:
        pass
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            return True
        except Exception as e:
            print(f"Failed to close app '{app}': {e}")
            return False

# Asynchronous function to translate and execute user commands.
async def TranslateAndExecute(commands: list[str]):
    funcs = []
    for command in commands:
        command_lower = command.lower().strip()
        if command_lower.startswith("open"):
            # Skip commands like "open it" or "open file"
            if "open it" in command_lower or command_lower == "open file":
                continue
            else:
                fun = asyncio.to_thread(OpenApp, command_lower.removeprefix("open").strip())
                funcs.append(fun)
        elif command_lower.startswith("close"):
            fun = asyncio.to_thread(CloseApp, command_lower.removeprefix("close").strip())
            funcs.append(fun)
        elif command_lower.startswith("content"):
            fun = asyncio.to_thread(Content, command_lower.removeprefix("content").strip())
            funcs.append(fun)
        elif command_lower.startswith("google search"):
            fun = asyncio.to_thread(GoogleSearch, command_lower.removeprefix("google search").strip())
            funcs.append(fun)
        elif command_lower.startswith("youtube search"):
            fun = asyncio.to_thread(YouTubeSearch, command_lower.removeprefix("youtube search").strip())
            funcs.append(fun)
        elif command_lower.startswith("system"):
            fun = asyncio.to_thread(System, command_lower.removeprefix("system").strip())
            funcs.append(fun)
        elif command_lower.startswith("play"):
            # Branch to handle play commands (e.g., "play afsana")
            fun = asyncio.to_thread(PlayYoutube, command_lower.removeprefix("play").strip())
            funcs.append(fun)
        else:
            print(f"No Function Found. For {command}")

    results = await asyncio.gather(*funcs, return_exceptions=True)
    for result in results:
        yield result  # Yield every result (not just strings)

# Asynchronous function to automate command execution.
async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):
        pass
    return True

if __name__ == "__main__":
    asyncio.run(Automation([
        "open google"
    ]))

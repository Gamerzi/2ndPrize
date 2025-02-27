import sys
import os
import subprocess
import threading
import json
from time import sleep
from asyncio import run

# Force Python to recognize the current folder (where Main.py is located).
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now the imports from Frontend should work:
from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)

# Import backend components
from Backend.Model import FirstLayerDMM
from Backend.RealTimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.Whatsup import send_whatsapp_message  # WhatsApp messaging function
from Backend.Call import send_call                    # Call feature function
from Backend.Calender import send_meet_link           # Meeting link sending function

# Import utility modules
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
Username = "Baqer Ali"
Assistantname = "Jarvis"

# Define default welcome message
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well. How may i help you?'''

# Initialize subprocesses and available functions list
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

def ShowDefaultChatIfNoChats():
    """Initialize chat with default message if no previous chat exists"""
    File = open(r'Data\ChatLog.json', "r", encoding='utf-8')
    if len(File.read()) < 5:
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write("")
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    """Read and return chat history from JSON file"""
    with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
    """Process and format chat log data"""
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"
    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    """Display chat history on the GUI"""
    File = open(TempDirectoryPath('Database.data'), "r", encoding='utf-8')
    Data = File.read()
    if len(str(Data)) > 0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        File.close()
        File = open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8')
        File.write(result)
        File.close()

def InitialExecution():
    """Initial setup for the application"""
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

def MainExecution():
    """Main execution logic for processing queries and generating responses"""
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""
    
    SetAssistantStatus("Listening ...")
    Query = SpeechRecognition()
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking ...")
    Decision = FirstLayerDMM(Query)
    
    print("")
    print(f"Decision : {Decision}")
    print("")
    
    # Check if the decision includes a WhatsApp command.
    for queries in Decision:
        if queries.lower().startswith("whatsapp"):
            SetAssistantStatus("Sending WhatsApp message ...")
            send_whatsapp_message()
            return True
    
    # Check if the decision includes a call command.
    for queries in Decision:
        if queries.lower().startswith("call"):
            SetAssistantStatus("Initiating call ...")
            send_call()
            return True
    
    # Check if the decision includes the keyword "schedule"
    # which will trigger sending the meet link.
    for queries in Decision:
        if "schedule" in queries.lower():
            SetAssistantStatus("Scheduling meet link ...")
            send_meet_link()
            return True

    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])
    
    Mearged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )
    
    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True
            
    for queries in Decision:
        if not TaskExecution:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True
                
    if ImageExecution:
        with open(r"Frontend\Files\ImageGeneratoion.data", "w") as file:
            file.write(f"{ImageGenerationQuery},True")
            
        try:
            p1 = subprocess.Popen(['python', r'Backend\ImageGeneration.py'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE, shell=False)
            subprocesses.append(p1)
        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")
            
    if (G and R) or R:
        SetAssistantStatus("Searching ...")
        Answer = RealtimeSearchEngine(QueryModifier(Mearged_query))
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering ...")
        TextToSpeech(Answer)
        return True
    else:
        for Queries in Decision:
            if "general" in Queries:
                SetAssistantStatus("Thinking ...")
                QueryFinal = Queries.replace("general ", "")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering ...")
                TextToSpeech(Answer)
                return True
            elif "realtime" in Queries:
                SetAssistantStatus("Searching ...")
                QueryFinal = Queries.replace("realtime ", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering ...")
                TextToSpeech(Answer)
                return True
            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering ...")
                TextToSpeech(Answer)
                SetAssistantStatus("Answering ...")
                os._exit(1)

def FirstThread():
    """Main thread for handling microphone input and execution"""
    while True:
        CurrentStatus = GetMicrophoneStatus()
        
        if CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()
            
            if "Available ..." in AIStatus:
                sleep(0.1)
            else:
                SetAssistantStatus("Available ...")

def SecondThread():
    """Secondary thread for GUI"""
    GraphicalUserInterface()

if __name__ == "__main__":
    # Start the main (microphone) thread
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    # Then run the GUI
    SecondThread()


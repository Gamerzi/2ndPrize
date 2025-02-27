import cohere
from rich import print
from dotenv import dotenv_values

env_vars = dotenv_values(".env")

CohereApiKey = ""
co = cohere.Client(api_key=CohereApiKey)

# Command list includes additional commands.
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search", "youtube search", "reminder", "whatsapp", "call", "schedule"
]

preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write an application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
-> Respond with 'general ( query )' if a query can be answered by a LLM model (conversational ai chatbot) and doesn't require any up to date information.
"""

ChatHistory = [
    {"role": "User", "message": "how are you?"},
    {"role": "Chatbot", "message": "general how are you?"},
    {"role": "User", "message": "do you like pizza?"},
    {"role": "Chatbot", "message": "general do you like pizza?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and by the way remind me that I have a dancing performance on 5th Aug at 11pm"},
    {"role": "Chatbot", "message": "general what is today's date, reminder 11:00pm 5th Aug dancing performance"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."}
]

def FirstLayerDMM(prompt: str = "test"):
    # Do nothing for empty input.
    if not prompt.strip():
        return []
    
    # If the query is for content and nothing follows, return a default letter.
    if prompt.lower().startswith("content"):
        content_body = prompt[len("content"):].strip()
        if not content_body:
            default_letter = (
                "Dear Sir/Madam,\n\n"
                "I am writing to inform you that I am not feeling well and kindly request sick leave for today.\n\n"
                "Sincerely,\nBaqer Ali"
            )
            return [f"content {default_letter}"]
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        stream = co.chat_stream(
            model="command-r-plus",
            message=prompt,
            temperature=0.7,
            chat_history=ChatHistory,
            prompt_truncation="OFF",
            connectors=[],
            preamble=preamble
        )
    except Exception as e:
        print("Error calling co.chat_stream:", e)
        return ["Error: API call failed."]
    
    response = ""
    for event in stream:
        if event.event_type == "text-generation":
            response += event.text

    response = response.replace("\n", "").split(",")
    response = [i.strip() for i in response if i.strip()]
    
    filtered = []
    for task in response:
        lower_task = task.lower()
        # If the response starts with "general meet", transform it to "schedule meet".
        if lower_task.startswith("general meet"):
            filtered.append("schedule meet")
        else:
            for func in funcs:
                if lower_task.startswith(func):
                    filtered.append(task)
                    break
    return filtered

if __name__ == "__main__":
    while True:
        user_input = input(">> ").strip()
        if not user_input:
            continue  # Skip empty input
        decision = FirstLayerDMM(user_input)
        if decision:
            print("Decision:", decision)

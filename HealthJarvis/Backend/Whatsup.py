import pywhatkit

def send_whatsapp_message():
    # Hard-coded phone number with country code.
    phone = "+917981659550"  
    message = "I need to get the hospital now"
    wait_time = 10  # Seconds to wait after opening WhatsApp Web
    tab_close = True  # Automatically close the tab after sending
    close_time = 3   # Time in seconds to wait before closing the tab

    try:
        pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=wait_time, tab_close=tab_close, close_time=close_time)
        print("Message sent!")
    except Exception as e:
        print("Error sending message:", e)

if __name__ == '__main__':
    send_whatsapp_message()

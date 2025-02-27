import webbrowser
import urllib.parse

def send_meet_link():
    receiver_email = "rrsed456@gmail.com"  # Recipient's email address
    subject = "Google Meet Link for Meeting"
    body = """To join the meeting on Google Meet, click this link:
https://meet.google.com/pim-hugd-twp

Or open Meet and enter this code: pim-hugd-twp

Meet is in 9pm
"""
    # Encode subject and body for a URL
    subject_encoded = urllib.parse.quote(subject)
    body_encoded = urllib.parse.quote(body)
    
    # Gmail compose URL with pre-filled fields.
    gmail_compose_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={receiver_email}&su={subject_encoded}&body={body_encoded}&tf=1"
    webbrowser.open(gmail_compose_url)

if __name__ == '__main__':
    send_meet_link()

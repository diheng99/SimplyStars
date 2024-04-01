from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import random, string, os, base64

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
filePathCred = 'C:\\Users\\Di heng\\Desktop\\SCSE Y2S2\\SC2006 Software Engineering\\Project\\credentials.json'
filePathToken = 'C:\\Users\\Di heng\\Desktop\\SCSE Y2S2\\SC2006 Software Engineering\\Project\\token.json'

# Function to send email using Gmail API
def send_email(receiver_email, otp):
    creds = None
    token_json_path = filePathToken

    # Load credentials from the token file
    if os.path.exists(token_json_path):
        creds = Credentials.from_authorized_user_file(token_json_path, SCOPES)

    if creds and creds.valid:
        service = build('gmail', 'v1', credentials=creds)

        # Create email message
        message = MIMEText(f"Your OTP is: {otp}")
        message['to'] = receiver_email
        message['from'] = 'diheng99@gmail.com'  # Replace with your email
        message['subject'] = 'Your OTP'

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        body = {'raw': raw_message}

        # Send the message
        try:
            service.users().messages().send(userId='me', body=body).execute()
        except Exception as e:
            print(f"An error occurred: {e}")
            # Handle the error appropriately in your application
    else:
        print("No valid credentials available.")
    
def main():
    creds = None
    token_json_path = 'token.json'
    redirect_uri = 'http://localhost:5000/home'
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    # Check if the token.json file exists and load it
    if os.path.exists(token_json_path):
        creds = Credentials.from_authorized_user_file(token_json_path, SCOPES)

    # If no credentials are available, or if they're invalid, start the authorization flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh the access token using the refresh token
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            flow.redirect_uri = redirect_uri
            # Request offline access and force re-consent to get a refresh token
            creds = flow.run_local_server(port=5000, access_type='offline', prompt='consent')

        # Save the credentials to token.json
        with open(token_json_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def check_credentials():
    
    token_json_path = filePathToken

    if os.path.exists(token_json_path):
        creds = Credentials.from_authorized_user_file(token_json_path, SCOPES)
        if creds and creds.valid:
            return creds
    return None

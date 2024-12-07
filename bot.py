import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import datetime
from dotenv import load_dotenv
load_dotenv()

# Initialize Slack app
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials/my-slack-project-442606-8beabae10df4.json'
SPREADSHEET_ID = '1FOsXQ6iTjv6Q02uf_iObFagMlrhiu9MmdbS6uSPezqI'

def get_google_sheets_service():
    """Initialize Google Sheets service"""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    return service.spreadsheets()

# Command to store data
@app.command("/store")
def store_data(ack, command, say):
    """Handle /store command"""
    ack()
    try:
        # Parse the command text
        text = command['text']
        user_id = command['user_id']
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare data for sheets
        values = [[timestamp, user_id, text]]
        
        # Get sheets service
        sheets = get_google_sheets_service()
        
        # Append data to sheet
        result = sheets.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:C',  # Adjust range as needed
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        
        say(f"Data stored successfully! Entry added to row {result.get('updates').get('updatedRows')}")
    
    except Exception as e:
        say(f"Error storing data: {str(e)}")

@app.event("message")
def handle_message(body, say):
    # Get the message text
    if "text" in body["event"]:
        message_text = body["event"]["text"].lower()
        
        # Basic responses
        if "hello" in message_text or "hi" in message_text:
            say("Hello! 👋 I'm your attendance bot. You can use these commands:\n"
                "• /checkin - Mark your attendance\n"
                "• /checkout - Record your checkout\n"
                "• /attendance-status - View today's attendance\n"
                "• /attendance-help - Show all commands")
        
        elif "help" in message_text:
            say("Here are the available commands:\n"
                "• /checkin - Mark your attendance\n"
                "• /checkout - Record your checkout\n"
                "• /attendance-status - View today's attendance\n"
                "• /attendance-help - Show all commands\n\n"
                "You can also chat with me directly for help!")
        
        else:
            say("I'm here to help with attendance! Try saying 'hello' or 'help' to see what I can do.")


# Command to retrieve data
@app.command("/retrieve")
def retrieve_data(ack, command, say):
    """Handle /retrieve command"""
    ack()
    try:
        # Get sheets service
        sheets = get_google_sheets_service()
        
        # Get last 5 entries
        result = sheets.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:C',
            majorDimension='ROWS'
        ).execute()
        
        values = result.get('values', [])[-5:]  # Get last 5 entries
        
        # Format response
        response = "*Last 5 entries:*\n"
        for row in values:
            response += f"• {row[0]} - User: {row[1]} - Data: {row[2]}\n"
        
        say(response)
    
    except Exception as e:
        say(f"Error retrieving data: {str(e)}")

# Help command
@app.command("/databot-help")
def help_command(ack, say):
    """Handle /databot-help command"""
    ack()
    help_text = """
*Available Commands:*
• `/store [data]` - Store data in Google Sheets
• `/retrieve` - Get last 5 entries from sheets
• `/databot-help` - Show this help message
    """
    say(help_text)

if __name__ == "__main__":
    # Start the app
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SERVICE_ACCOUNT_FILE = 'your-service-account.json'  # Replace with your actual filename
DELEGATED_ADMIN = 'admin@yourdomain.com'  # Replace with your admin email

SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.member.readonly',
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Authenticate and delegate
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
delegated_credentials = credentials.with_subject(DELEGATED_ADMIN)

# Build services
admin_service = build('admin', 'directory_v1', credentials=delegated_credentials)
sheets_service = build('sheets', 'v4', credentials=delegated_credentials)

# Get groups
groups = admin_service.groups().list(customer='my_customer').execute().get('groups', [])

# Get members and their names
group_data = []
for group in groups:
    group_email = group.get('email', '')
    group_name = group.get('name', '')
    try:
        members = admin_service.members().list(groupKey=group_email).execute().get('members', [])
        for member in members:
            member_email = member.get('email', '')
            member_role = member.get('role', '')
            member_type = member.get('type', '')
            member_name = 'Unknown'

            # Attempt to get full name if member is a user
            if member_type == 'USER' and member_email:
                try:
                    user_info = admin_service.users().get(userKey=member_email).execute()
                    member_name = user_info.get('name', {}).get('fullName', 'Unknown')
                except HttpError:
                    member_name = 'Unknown'

            group_data.append({
                'Group Name': group_name,
                'Group Email': group_email,
                'Member Name': member_name,
                'Member Email': member_email,
                'Role': member_role,
                'Type': member_type
            })
    except HttpError:
        pass  # Skip group if members cannot be retrieved

# Create DataFrame
df = pd.DataFrame(group_data)

# Create Google Sheet
spreadsheet = sheets_service.spreadsheets().create(body={
    'properties': {'title': 'Google Workspace Group Members'}
}, fields='spreadsheetId').execute()

spreadsheet_id = spreadsheet.get('spreadsheetId')

# Write to sheet
sheet_values = [df.columns.tolist()] + df.values.tolist()
sheets_service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range='Sheet1!A1',
    valueInputOption='RAW',
    body={'values': sheet_values}
).execute()

print(f"✅ Group members written to Google Sheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
# Google Workspace Group Membership Audit Using Admin SDK and Python

This guide walks you through auditing all Google Workspace groups and their members — including names, roles, and types — and exporting the results to Google Sheets using Python in Google Colab.

---

## ✅ Step 1: Enable Required APIs

### 1.1 Open Google Cloud Console
- Go to: [https://console.cloud.google.com/](https://console.cloud.google.com/)
- Sign in with your **Google Workspace admin** account.

### 1.2 Create or Select a Project
- Click the project dropdown at the top center.
- Click **"New Project"**
- Enter a name (e.g., `GroupAuditProject`) → Click **"Create"**
- Select the project from the dropdown.

### 1.3 Enable APIs
Navigate to **APIs & Services > Library** and enable the following:
- **Admin SDK API**
  - Search: `Admin SDK`
  - Click result → Click **Enable**
- **Google Sheets API**
  - Search: `Google Sheets API`
  - Click result → Click **Enable**
- **Google Workspace Directory API**
  - Search: `Google Workspace Directory API`
  - Click result → Click **Enable**

---

## ✅ Step 2: Create a Service Account

### 2.1 Navigate to Service Accounts
- Go to **IAM & Admin > Service Accounts**
- Click **"Create Service Account"**

### 2.2 Fill in Details
- **Name:** `group-reader`
- **Description:** `Reads group and member data`
- Click **"Create and Continue"**

### 2.3 Skip Role Assignment
- Click **"Continue"** without selecting a role
- Click **"Done"**

---

## ✅ Step 3: Create and Download JSON Key

### 3.1 Open the Service Account
- Click the name of the service account

### 3.2 Go to **Keys** Tab
- Click **"Keys"**
- Click **"Add Key" > "Create new key"**
- Choose **JSON** → Click **Create**
- Save the downloaded `.json` file securely

---

## ✅ Step 4: Delegate Domain-Wide Authority

### 4.1 Get Client ID
- In the service account page, copy the **Unique ID (Client ID)**

### 4.2 Enable Delegation
- Click **"Edit"** (top right)
- Check **"Enable G Suite Domain-wide Delegation"**
- Click **"Save"**

### 4.3 Authorize Scopes in Admin Console
- Go to: [https://admin.google.com/](https://admin.google.com/)
- Navigate to:
  - **Security > API Controls > Domain-wide Delegation > Manage Domain-wide Delegation**
- Click **"Add new"**
- Paste the **Client ID**
- Add these scopes (comma-separated):
  ```
  https://www.googleapis.com/auth/admin.directory.group.readonly,
  https://www.googleapis.com/auth/admin.directory.group.member.readonly,
  https://www.googleapis.com/auth/admin.directory.user.readonly,
  https://www.googleapis.com/auth/spreadsheets
  ```
- Click **"Authorize"**

---

## ✅ Step 5: Set Up Google Colab

### 5.1 Open Google Colab
- Go to: [https://colab.research.google.com/](https://colab.research.google.com/)
- Click **“New Notebook”**

### 5.2 Install Required Libraries
Paste and run the following in the first cell:
```python
!pip install --upgrade google-api-python-client google-auth google-auth-oauthlib gspread oauth2client pandas
```

### 5.3 Upload Your JSON Key File
- Open the left sidebar in Colab
- Click the **folder icon**
- Click the **upload icon**
- Select your `.json` key file (e.g., `your-service-account.json`)

> **Important:** Make sure the filename in the script matches your uploaded file.

---

## ✅ Step 6: Run the Audit Script

Paste and run the following Python script in a new code cell:

```python
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SERVICE_ACCOUNT_FILE = 'your-service-account.json'  # Replace with actual filename
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

# Get members and names
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

# Write to Sheet
sheet_values = [df.columns.tolist()] + df.values.tolist()
sheets_service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range='Sheet1!A1',
    valueInputOption='RAW',
    body={'values': sheet_values}
).execute()

print(f"✅ Group members written to Google Sheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
```

---

## ✅ Step 7: Access the Google Sheet
Click the link printed in the Colab output to view your audit results.

---

🎉 **Congratulations** — you’ve completed your group audit!

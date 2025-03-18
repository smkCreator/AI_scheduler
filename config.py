import os

# Email Configuration
EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.gmail.com',
    'SMTP_PORT': 587,
    'SENDER_EMAIL': '',  # Add your email here
    'SENDER_PASSWORD': '',  # Add your app password here
}

# Calendar Configuration
CALENDAR_CONFIG = {
    'CREDENTIALS_PATH': 'credentials.json',
    'TOKEN_PATH': 'token.json',
    'SCOPES': ['https://www.googleapis.com/auth/calendar']
}

def load_env_vars():
    """Load environment variables for email and calendar"""
    os.environ['EMAIL_SMTP_SERVER'] = EMAIL_CONFIG['SMTP_SERVER']
    os.environ['EMAIL_SMTP_PORT'] = str(EMAIL_CONFIG['SMTP_PORT'])
    os.environ['EMAIL_SENDER'] = EMAIL_CONFIG['SENDER_EMAIL']
    os.environ['EMAIL_PASSWORD'] = EMAIL_CONFIG['SENDER_PASSWORD']
    os.environ['CALENDAR_CREDENTIALS'] = CALENDAR_CONFIG['CREDENTIALS_PATH']

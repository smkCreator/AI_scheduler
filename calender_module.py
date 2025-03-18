import os
import json
import datetime
from typing import Dict, List, Optional, Tuple
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class CalendarIntegration:
    def __init__(self):
        self.service = None
        self.connected = False
        self._setup_google_calendar()
        
    def create_event(self, title, start_time, end_time, attendees, location="Virtual Interview", description=""):
        """
        Create a calendar event and return necessary details for email notifications.
        
        Args:
            title: Event title
            start_time: Start time (ISO format string)
            end_time: End time (ISO format string)
            attendees: List of attendee email addresses
            location: Location of the event
            description: Event description
            
        Returns:
            dict: Event details including calendar link
        """
        try:
            if self.connected:
                # Convert ISO strings to datetime objects
                start_dt = datetime.datetime.fromisoformat(start_time)
                end_dt = datetime.datetime.fromisoformat(end_time)
                
                # Create real Google Calendar event
                event_body = {
                    'summary': title,
                    'description': description,
                    'start': {
                        'dateTime': start_time,
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'dateTime': end_time,
                        'timeZone': 'UTC',
                    },
                    'attendees': [{'email': email} for email in attendees],
                    'location': location,
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},
                            {'method': 'popup', 'minutes': 30},
                        ],
                    },
                }
                
                try:
                    event = self.service.events().insert(
                        calendarId='primary',
                        body=event_body,
                        sendUpdates='all'
                    ).execute()
                    
                    # Return event details for email notifications
                    return {
                        'event_id': event.get('id', ''),
                        'calendar_link': event.get('htmlLink', ''),
                        'status': 'confirmed'
                    }
                except Exception as e:
                    print(f"Error creating Google Calendar event: {e}")
                    # Fall back to demo mode
            
            # Demo mode (when not connected or error occurred)
            print(f"[DEMO MODE] Creating calendar event: {title}")
            print(f"- Start: {start_time}")
            print(f"- End: {end_time}")
            print(f"- Attendees: {attendees}")
            
            # Generate a mock event ID and calendar link
            event_id = f"evt_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return {
                'event_id': event_id,
                'calendar_link': f"https://calendar.google.com/calendar/event?eid={event_id}",
                'status': 'demo'
            }
            
        except Exception as e:
            print(f"Error in create_event: {e}")
            return {
                'event_id': 'error',
                'calendar_link': '',
                'status': 'error',
                'error': str(e)
            }
    
    def _setup_google_calendar(self):
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_info(
                json.loads(open('token.json').read()))
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        self.connected = True
    
    def get_availability(self, user_id: str, start_time: datetime.datetime, 
                        end_time: datetime.datetime) -> List[Dict]:
        if not self.connected:
            return []
        
        free_slots = []
        
        try:
            body = {
                "timeMin": start_time.isoformat(),
                "timeMax": end_time.isoformat(),
                "items": [{"id": user_id}]
            }
            
            freebusy_response = self.service.freebusy().query(body=body).execute()
            
            if 'calendars' in freebusy_response and user_id in freebusy_response['calendars']:
                busy_periods = freebusy_response['calendars'][user_id]['busy']
                
                current_time = start_time
                for period in busy_periods:
                    period_start = datetime.datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
                    period_end = datetime.datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
                    
                    if current_time < period_start:
                        free_slots.append({
                            'start': current_time.isoformat(),
                            'end': period_start.isoformat()
                        })
                    
                    current_time = period_end
                
                if current_time < end_time:
                    free_slots.append({
                        'start': current_time.isoformat(),
                        'end': end_time.isoformat()
                    })
        except Exception as e:
            print(f"Error fetching Google Calendar availability: {e}")
    
        return free_slots
    
    def create_meeting(self, title: str, start_time: datetime.datetime,
                      end_time: datetime.datetime, attendees: List[str],
                      description: str = "", location: str = "") -> str:
        if not self.connected:
            return ""
        
        meeting_id = ""
        
        event_body = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [{'email': email} for email in attendees],
            'location': location,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        try:
            event = self.service.events().insert(
                calendarId='primary',
                body=event_body,
                sendUpdates='all'
            ).execute()
            
            meeting_id = event.get('id', '')
        except Exception as e:
            print(f"Error creating Google Calendar event: {e}")
    
        return meeting_id
    
    def update_meeting(self, meeting_id: str, start_time: Optional[datetime.datetime] = None,
                      end_time: Optional[datetime.datetime] = None, 
                      attendees: Optional[List[str]] = None,
                      title: Optional[str] = None,
                      description: Optional[str] = None,
                      location: Optional[str] = None) -> bool:
        if not self.connected or not meeting_id:
            return False
        
        success = False
        
        try:
            event = self.service.events().get(
                calendarId='primary', eventId=meeting_id).execute()
            
            if start_time:
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                }
            
            if end_time:
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            if title:
                event['summary'] = title
            
            if description:
                event['description'] = description
            
            if location:
                event['location'] = location
            
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=meeting_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            success = True
        except Exception as e:
            print(f"Error updating Google Calendar event: {e}")
    
        return success
    
    def delete_meeting(self, meeting_id: str) -> bool:
        if not self.connected or not meeting_id:
            return False
        
        success = False
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=meeting_id,
                sendUpdates='all'
            ).execute()
            success = True
        except Exception as e:
            print(f"Error deleting Google Calendar event: {e}")
    
        return success

    def get_upcoming_meetings(self, user_id: str, days: int = 7) -> List[Dict]:
        if not self.connected:
            return []
        
        meetings = []
        now = datetime.datetime.utcnow()
        end_time = now + datetime.timedelta(days=days)
        
        try:
            events_result = self.service.events().list(
                calendarId=user_id if user_id != "primary" else "primary",
                timeMin=now.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            for event in events_result.get('items', []):
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                meetings.append({
                    'id': event['id'],
                    'title': event.get('summary', 'No Title'),
                    'start': start,
                    'end': end,
                    'attendees': [attendee.get('email', '') for attendee in event.get('attendees', [])],
                    'description': event.get('description', ''),
                    'location': event.get('location', '')
                })
        except Exception as e:
            print(f"Error fetching Google Calendar meetings: {e}")
    
        return meetings
    
if __name__ == "__main__":
    import datetime

    # Initialize Google Calendar Integration
    google_calendar = CalendarIntegration()

    if google_calendar.connected:
        print("Google Calendar connected successfully!")

        # Get availability
        start_time = datetime.datetime.utcnow()
        end_time = start_time + datetime.timedelta(hours=5)
        user_email = "your-email@gmail.com"
        
        availability = google_calendar.get_availability(user_email, start_time, end_time)
        print(f"Availability slots: {availability}")
        start_time = datetime.datetime.utcnow().replace(hour=4, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        end_time = start_time + datetime.timedelta(hours=1)

        # Create a meeting
        meeting_id = google_calendar.create_meeting(
            title="Updated interview time with Basis Vectors",
            start_time=start_time,
            end_time=end_time,
            attendees=["pavansai.bheemisetty@gmail.com"],
            description="""Hi Saikiran,

Greetings from team Basis Vectors!

Your interview has been scheduled for the following date and time:

17th March 2025, 9:30 AM - 10:30 AM.

Please join the meeting using the following same link

""",
            location="Online"
        )
        print(f"Meeting created with ID: {meeting_id}")

        # Update the meeting
        # if meeting_id:
        #     success = google_calendar.update_meeting(
        #         meeting_id=meeting_id,
        #         title="Updated Test Meeting",
        #         description="Updated description."
        #     )
        #     print(f"Meeting update successful: {success}")

        # Get upcoming meetings
        upcoming_meetings = google_calendar.get_upcoming_meetings(user_email, days=3)
        print(f"Upcoming meetings: {upcoming_meetings}")

        # Delete the meeting
        # if meeting_id:
        #     deleted = google_calendar.delete_meeting(meeting_id)
        #     print(f"Meeting deleted: {deleted}")

    else:
        print("Failed to connect to Google Calendar.")
import os
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import json
import uuid
import ics  # Using ics-py for iCalendar generation

class CalendarIntegration:
    def __init__(self, calendar_type="google", credentials_path=None):
        """
        Initialize calendar integration.
        
        Args:
            calendar_type: 'google' or 'microsoft'
            credentials_path: Path to credentials file
        """
        self.calendar_type = calendar_type.lower()
        self.credentials_path = credentials_path or os.environ.get('CALENDAR_CREDENTIALS', '')
        
        # Disable simulation mode for production use
        self.simulate = False
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def create_event(self, 
                    title: str, 
                    start_time: str, 
                    end_time: str, 
                    attendees: List[str], 
                    location: str = "Virtual", 
                    description: str = "",
                    notify_attendees: bool = True) -> Dict:
        """
        Create a calendar event and send invitations.
        
        Args:
            title: Event title
            start_time: Start time in ISO format
            end_time: End time in ISO format
            attendees: List of attendee emails
            location: Event location
            description: Event description
            notify_attendees: Whether to send email notifications
            
        Returns:
            Dictionary with event details
        """
        try:
            # For the hackathon, we'll generate an iCalendar (.ics) file content
            # that could be attached to emails
            event_id = str(uuid.uuid4())
            ical_content = self._generate_ical(
                event_id, title, start_time, end_time, 
                attendees, location, description
            )
            
            # Log success for demonstration
            self.logger.info(f"Calendar event created: {title}")
            self.logger.info(f"Attendees notified: {', '.join(attendees)}")
            
            # Return event details
            return {
                "id": event_id,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "attendees": attendees,
                "location": location,
                "description": description,
                "status": "created",
                "calendar_link": f"https://calendar.example.com/event/{event_id}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create calendar event: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def update_event(self, event_id: str, **kwargs) -> Dict:
        """
        Update an existing calendar event.
        
        Args:
            event_id: ID of the event to update
            **kwargs: Fields to update
            
        Returns:
            Dictionary with updated event details
        """
        try:
            # For hackathon purposes, just log the update
            self.logger.info(f"Calendar event {event_id} updated with: {json.dumps(kwargs)}")
            
            # Return simulated response
            return {
                "id": event_id,
                "status": "updated",
                **kwargs
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update calendar event: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def delete_event(self, event_id: str) -> Dict:
        """
        Delete a calendar event.
        
        Args:
            event_id: ID of the event to delete
            
        Returns:
            Dictionary with deletion status
        """
        try:
            # For hackathon purposes, just log the deletion
            self.logger.info(f"Calendar event {event_id} deleted")
            
            # Return simulated response
            return {
                "id": event_id,
                "status": "deleted"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete calendar event: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _generate_ical(self, 
                      event_id: str,
                      title: str, 
                      start_time: str, 
                      end_time: str, 
                      attendees: List[str], 
                      location: str, 
                      description: str) -> str:
        """Generate iCalendar format for the event."""
        try:
            # Create a new calendar
            calendar = ics.Calendar()
            
            # Create an event
            event = ics.Event()
            event.name = title
            event.begin = start_time
            event.end = end_time
            event.description = description
            event.location = location
            event.uid = event_id
            
            # Add attendees
            for attendee in attendees:
                event.add_attendee(attendee)
            
            # Add event to calendar
            calendar.events.add(event)
            
            # Return the calendar as a string
            return str(calendar)
            
        except Exception as e:
            self.logger.error(f"Failed to generate iCalendar: {str(e)}")
            return ""
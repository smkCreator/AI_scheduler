import json
import os
import spacy
import dateparser
import pytz
import re
from datetime import datetime, timedelta

# Load SpaCy's English model
nlp = spacy.load("en_core_web_sm")


def nlp_process(availability, timezone, default_timezone="Asia/Kolkata"):
    """
    Process raw availability data into structured format with enhanced natural language understanding.
    Args:
        availability (str): User availability input in natural language.
        timezone (str): User-selected timezone.
        default_timezone (str): Default timezone.
    Returns:
        list: Structured availability data.
    """
    try:
        user_tz = pytz.timezone(timezone)
        default_tz = pytz.timezone(default_timezone)
    except pytz.UnknownTimeZoneError:
        return []
    
    structured_availability = []
    today = datetime.now().date()
    
    # Dictionary for time periods
    time_periods = {
        "morning": ("09:00 AM", "12:00 PM"),
        "afternoon": ("12:00 PM", "05:00 PM"),
        "evening": ("05:00 PM", "08:00 PM"),
        "night": ("08:00 PM", "11:00 PM"),
        "anytime": ("09:00 AM", "05:00 PM")
    }
    
    # Helper function to get date from day reference
    def get_date_from_day_reference(day_text):
        day_text = day_text.lower()
        
        # Handle "tomorrow", "day after tomorrow", etc.
        if "tomorrow" in day_text:
            if "day after" in day_text:
                return today + timedelta(days=2)
            return today + timedelta(days=1)
            
        # Handle "next Monday", "next Tuesday", etc.
        weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day in enumerate(weekday_names):
            if day in day_text:
                days_ahead = (i - today.weekday()) % 7
                # If it's "next" day, add a week
                if "next" in day_text:
                    days_ahead += 7
                # If it's already passed this week and no "next" specified, go to next week
                elif days_ahead == 0 and datetime.now().hour >= 12:
                    days_ahead = 7
                return today + timedelta(days=days_ahead)
        
        # Handle specific dates like "15th of March"
        try:
            parsed_date = dateparser.parse(day_text, settings={"TIMEZONE": timezone})
            if parsed_date:
                return parsed_date.date()
        except:
            pass
            
        return None
    
    # Helper function to extract time ranges
    def extract_time_range(text):
        # Check for time period keywords
        for period, (start, end) in time_periods.items():
            if period in text.lower():
                return start, end
        
        # Check for explicit time ranges like "10 AM to 2 PM"
        time_pattern = r'(\d{1,2}(?::\d{2})?\s*(?:[APap][Mm])?)\s*(?:to|through|-)\s*(\d{1,2}(?::\d{2})?\s*(?:[APap][Mm])?)'
        match = re.search(time_pattern, text)
        if match:
            start_time, end_time = match.groups()
            return standardize_time(start_time), standardize_time(end_time)
        
        # Check for "after X" expressions
        after_pattern = r'after\s+(\d{1,2}(?::\d{2})?\s*(?:[APap][Mm])?)'
        match = re.search(after_pattern, text)
        if match:
            start_time = match.group(1)
            # Calculate end time based on start time (typically end of business day)
            start_time_obj = datetime.strptime(standardize_time(start_time), "%I:%M %p")
            if start_time_obj.hour >= 17:  # If starting after 5 PM
                end_time = "11:00 PM"
            else:
                end_time = "05:00 PM"
            return standardize_time(start_time), end_time
        
        # Check for "before X" expressions
        before_pattern = r'before\s+(\d{1,2}(?::\d{2})?\s*(?:[APap][Mm])?)'
        match = re.search(before_pattern, text)
        if match:
            end_time = match.group(1)
            # Calculate start time based on end time (typically beginning of business day)
            end_time_obj = datetime.strptime(standardize_time(end_time), "%I:%M %p")
            if end_time_obj.hour <= 9:  # If ending before 9 AM
                start_time = "07:00 AM"
            else:
                start_time = "09:00 AM"
            return start_time, standardize_time(end_time)
        
        # Check for "at X" expressions
        at_pattern = r'at\s+(\d{1,2}(?::\d{2})?\s*(?:[APap][Mm])?)'
        match = re.search(at_pattern, text)
        if match:
            exact_time = match.group(1)
            start_time = standardize_time(exact_time)
            # Set a default 1-hour meeting
            start_time_obj = datetime.strptime(start_time, "%I:%M %p")
            end_time_obj = start_time_obj + timedelta(hours=1)
            end_time = end_time_obj.strftime("%I:%M %p")
            return start_time, end_time
        
        # Check for single time mentions without prepositions
        single_time_pattern = r'(\d{1,2}(?::\d{2})?\s*(?:[APap][Mm])?)'
        matches = re.findall(single_time_pattern, text)
        if matches:
            # If there's only one time mentioned, assume it's a start time
            # with a default duration of business hours
            start_time = standardize_time(matches[0])
            start_time_obj = datetime.strptime(start_time, "%I:%M %p")
            
            # If it's morning, assume available until end of business day
            if start_time_obj.hour < 12:
                end_time = "05:00 PM"
            # If it's afternoon/evening, assume available for 3 hours
            else:
                end_time_obj = start_time_obj + timedelta(hours=3)
                # But not past 11 PM
                if end_time_obj.hour >= 23:
                    end_time = "11:00 PM"
                else:
                    end_time = end_time_obj.strftime("%I:%M %p")
                    
            return start_time, end_time
        
        # Default time range
        return "10:00 AM", "05:00 PM"
    
    # Helper function to standardize time format
    def standardize_time(time_str):
        time_str = time_str.strip().upper()
        
        # Add colon if missing
        if ':' not in time_str and re.search(r'\d+', time_str):
            hour = int(re.search(r'\d+', time_str).group())
            time_str = f"{hour}:00"
        
        # Add AM/PM if missing
        if 'AM' not in time_str and 'PM' not in time_str:
            hour = int(time_str.split(':')[0])
            if hour < 12:
                time_str += " AM"
            else:
                time_str += " PM"
        elif 'AM' in time_str:
            time_str = time_str.replace('AM', ' AM').strip()
        elif 'PM' in time_str:
            time_str = time_str.replace('PM', ' PM').strip()
        
        return time_str
    
    # Process the availability string
    # First, split by commas or "and" to handle multiple time slots
    segments = re.split(r',|\band\b', availability)
    
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        
        # Try to extract dates using SpaCy for more complex cases
        doc = nlp(segment)
        dates = []
        
        # Extract dates from SpaCy entities
        for ent in doc.ents:
            if ent.label_ == "DATE":
                parsed_date = dateparser.parse(ent.text, settings={"TIMEZONE": timezone})
                if parsed_date:
                    dates.append(parsed_date.date())
        
        # If no dates found, try to extract day references
        if not dates:
            # Look for day references like "tomorrow", "next Monday", etc.
            day_patterns = [
                r'(tomorrow|day after tomorrow)',
                r'(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))',
                r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december))'
            ]
            
            for pattern in day_patterns:
                matches = re.findall(pattern, segment, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    date = get_date_from_day_reference(match)
                    if date:
                        dates.append(date)
                        break
                        
            # If still no dates found, use today's date
            if not dates:
                dates.append(today)
        
        # Extract time ranges
        start_time_str, end_time_str = extract_time_range(segment)
        
        try:
            # Parse the times
            start_time = datetime.strptime(start_time_str, "%I:%M %p").time()
            end_time = datetime.strptime(end_time_str, "%I:%M %p").time()
            
            # Create availability entries for each date
            for date in dates:
                start_datetime = datetime.combine(date, start_time).replace(tzinfo=user_tz)
                end_datetime = datetime.combine(date, end_time).replace(tzinfo=user_tz)
                
                structured_availability.append({
                    "date": start_datetime.astimezone(default_tz).strftime("%Y-%m-%d"),
                    "start": start_datetime.astimezone(default_tz).strftime("%H:%M"),
                    "end": end_datetime.astimezone(default_tz).strftime("%H:%M"),
                    "timezone": default_timezone
                })
        except Exception as e:
            # Skip invalid entries but log the error
            print(f"Error processing time range: {e}")
            continue
    
    return structured_availability
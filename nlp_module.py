import spacy
import dateparser
from datetime import datetime, timedelta
import re
from typing import List, Dict, Tuple, Optional

class AvailabilityParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

        self.time_patterns = {
            "morning": (9, 12),  
            "afternoon": (12, 17),  
            "evening": (17, 20),  
            "business hours": (9, 17),  
            "end of day": (16, 17), 
            "lunch": (12, 14),  
        }
        
        # Generate 30-minute time slots for each day
        self.day_slots = [(h, m) for h in range(8, 18) for m in (0, 30)]

    def extract_availability(self, text: str) -> List[Dict]:
        doc = self.nlp(text.lower())
        
        dates = self._extract_dates(text)
        time_ranges = self._extract_time_ranges(text)
        
        if dates and not time_ranges:
            time_ranges = [self.time_patterns.get("business hours", (9, 17))]
        
        availability = []
        for date in dates:
            for start_hour, end_hour in time_ranges:
                current_time = datetime(
                    date.year, date.month, date.day, start_hour, 0
                )
                end_time = datetime(
                    date.year, date.month, date.day, end_hour, 0
                )
                
                while current_time < end_time:
                    slot_end = current_time + timedelta(minutes=30)
                    if slot_end > end_time:
                        slot_end = end_time
                        
                    availability.append({
                        "start": current_time.isoformat(),
                        "end": slot_end.isoformat(),
                        "source_text": text
                    })
                    
                    current_time = slot_end
        
        return availability
    
    def _extract_dates(self, text: str) -> List[datetime]:
        """Extract dates from text."""
        dates = []

        date_patterns = [
            r"(\d{1,2}(?:st|nd|rd|th)? of [a-zA-Z]+)",
            r"([a-zA-Z]+ \d{1,2}(?:st|nd|rd|th)?)",
            r"(\d{1,2}/\d{1,2}/\d{2,4})",
            r"(\d{1,2}-\d{1,2}-\d{2,4})",
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                parsed_date = dateparser.parse(match)
                if parsed_date:
                    dates.append(parsed_date)

        relative_dates = [
            "today", "tomorrow", "day after tomorrow", 
            "next monday", "next tuesday", "next wednesday", 
            "next thursday", "next friday", "this week", 
            "next week"
        ]
        
        for date_expr in relative_dates:
            if date_expr in text.lower():
                parsed_date = dateparser.parse(date_expr)
                if parsed_date:
                    dates.append(parsed_date)
        
        if not dates:
            next_day = dateparser.parse("tomorrow")
            if next_day.weekday() >= 5:  
                next_day = next_day + timedelta(days=(7 - next_day.weekday()))
            dates.append(next_day)
            
        return dates
    
    def _extract_time_ranges(self, text: str) -> List[Tuple[int, int]]:
        time_ranges = []
        
        # Check for time pattern matches
        for pattern, hours in self.time_patterns.items():
            if pattern in text.lower():
                time_ranges.append(hours)
        
        # Extract specific times using regex
        time_pattern = r"(\d{1,2}(?::\d{2})?\s*(?:am|pm))"
        times = re.findall(time_pattern, text.lower())
        
        if len(times) >= 2:
            hours = []
            for time_str in times:
                parsed_time = dateparser.parse(time_str)
                if parsed_time:
                    hours.append(parsed_time.hour + parsed_time.minute / 60)

            if hours:
                hours.sort()
                for i in range(0, len(hours) - 1, 2):
                    start_hour = int(hours[i])
                    end_hour = int(hours[i + 1])
                    time_ranges.append((start_hour, end_hour))

        if not time_ranges:
            time_ranges.append(self.time_patterns["business hours"])
            
        return time_ranges


if __name__ == "__main__":
    parser = AvailabilityParser()

    test_inputs = [
        "I am available next Monday afternoon",
        "I can do interviews on Tuesday and Wednesday from 10 AM to 2 PM",
        "I'm free tomorrow morning and Friday evening",
        "I can meet anytime on the 15th of March"
    ]
    
    for input_text in test_inputs:
        availability = parser.extract_availability(input_text)
        print(f"Input: {input_text}")
        for slot in availability:
            print(f"  - {slot['start']} to {slot['end']}")
        print()
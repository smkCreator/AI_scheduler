import streamlit as st
import json
import os
import spacy
import dateparser
import pytz
import re
from datetime import datetime, timedelta

# File paths for JSON storage
CANDIDATES_FILE = "candidates.json"
INTERVIEWERS_FILE = "interviewers.json"

# Ensure JSON files exist
for file in [CANDIDATES_FILE, INTERVIEWERS_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)

# Function to load data from JSON safely
def load_data(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

# Function to save data to JSON safely
def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# Load SpaCy's English model
nlp = spacy.load("en_core_web_sm")

def nlp_process(availability, timezone, default_timezone="Asia/Kolkata"):
    """
    Process raw availability data into structured format.
    Args:
        availability (str): User availability input.
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

    # Parse input using SpaCy
    doc = nlp(availability)
    structured_availability = []

    # Extract dates using dateparser
    parsed_dates = [dateparser.parse(ent.text, settings={"TIMEZONE": timezone}) for ent in doc.ents if ent.label_ == "DATE"]
    
    if not parsed_dates:
        parsed_date = dateparser.parse(availability, settings={"TIMEZONE": timezone})
        if parsed_date:
            parsed_dates.append(parsed_date)

    # Extract times using regex (Handles 12-hour and 24-hour formats)
    time_matches = re.findall(r"\d{1,2}:\d{2}\s*[APap][Mm]|\d{1,2}\s*[APap][Mm]|\d{1,2}:\d{2}", availability)

    # Default time slots based on keywords
    time_keywords = {
        "morning": ("09:00 AM", "12:00 PM"),
        "afternoon": ("12:00 PM", "04:00 PM"),
        "evening": ("04:00 PM", "08:00 PM"),
        "night": ("08:00 PM", "11:59 PM")
    }

    start_time, end_time = "10:00 AM", "02:00 PM"  # Default
    for keyword, (start, end) in time_keywords.items():
        if keyword in availability.lower():
            start_time, end_time = start, end
            break

    if len(time_matches) >= 2:
        start_time, end_time = time_matches[0], time_matches[1]

    # Convert times to datetime objects
    start_time = datetime.strptime(start_time, "%I:%M %p").time()
    end_time = datetime.strptime(end_time, "%I:%M %p").time()

    for parsed_date in parsed_dates:
        if parsed_date:
            start_datetime = datetime.combine(parsed_date.date(), start_time).replace(tzinfo=user_tz)
            end_datetime = datetime.combine(parsed_date.date(), end_time).replace(tzinfo=user_tz)

            structured_availability.append({
                "date": start_datetime.astimezone(default_tz).strftime("%Y-%m-%d"),
                "start": start_datetime.astimezone(default_tz).strftime("%H:%M"),
                "end": end_datetime.astimezone(default_tz).strftime("%H:%M"),
                "timezone": default_timezone
            })

    return structured_availability

# Function to save candidate data
def save_candidate(name, email, role_type, experience_level, availability, timezone):
    candidates = load_data(CANDIDATES_FILE)
    candidates.append({
        "name": name,
        "email": email,
        "role_type": role_type,
        "experience_level": experience_level,
        "availability": availability,
        "timezone": timezone,
        "availability_structured": nlp_process(availability, timezone),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(CANDIDATES_FILE, candidates)
    st.success("Candidate data saved successfully!")

# Function to save interviewer data
def save_interviewer(name, interviewer_id, role_type, experience_level, workload, availability, timezone):
    interviewers = load_data(INTERVIEWERS_FILE)
    interviewers.append({
        "name": name,
        "interviewer_id": interviewer_id,
        "role_type": role_type,
        "experience_level": experience_level,
        "workload": workload,
        "availability": availability,
        "timezone": timezone,
        "availability_structured": nlp_process(availability, timezone),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(INTERVIEWERS_FILE, interviewers)
    st.success("Interviewer data saved successfully!")

# Function to display dashboard
def display_dashboard():
    st.sidebar.title("Dashboard")

    st.sidebar.write("### Candidates")
    for candidate in load_data(CANDIDATES_FILE):
        st.sidebar.write(f"**{candidate['name']}** - {candidate['email']}")

    st.sidebar.write("---")
    
    st.sidebar.write("### Interviewers")
    for interviewer in load_data(INTERVIEWERS_FILE):
        st.sidebar.write(f"**{interviewer['name']}** - ID: {interviewer['interviewer_id']}")

    st.sidebar.write("---")
    st.sidebar.write("### Total Turnaround Time")
    st.sidebar.write(f"{st.session_state.get('total_turnaround_time', 0)} seconds")

# Main function
def input():
    st.title("AI-Powered Scheduling Bot")

    user_type = st.radio("Are you a Candidate or Interviewer?", ["Candidate", "Interviewer"])

    timezone_options = [
        "UTC-5 (EST) - US Eastern",
        "UTC-8 (PST) - Pacific (Canada)",
        "UTC+5:30 (IST) - India",
        "UTC+8 (CST) - China",
        "UTC+0 (GMT) - UK",
        "UTC+1 (CET) - Central Europe",
        "UTC+2 (EET) - Eastern Europe"
    ]

    if user_type == "Candidate":
        st.header("Candidate Details")
        name = st.text_input("Name")
        email = st.text_input("Email")
        role_type = st.selectbox("Role Type", ["Technical", "Sales", "Management"])
        experience_level = st.selectbox("Experience Level", ["Entry-Level", "Mid-Level", "Senior"])
        availability = st.text_area("Availability for the next 3 days")
        timezone = st.selectbox("Timezone", timezone_options)

        if st.button("Submit Candidate Data"):
            if all([name, email, role_type, experience_level, availability, timezone]):
                save_candidate(name, email, role_type, experience_level, availability, timezone)
            else:
                st.error("Please fill all fields.")

    elif user_type == "Interviewer":
        st.header("Interviewer Details")
        name = st.text_input("Name")
        interviewer_id = st.text_input("Interviewer ID")
        role_type = st.selectbox("Role Type", ["Technical", "Sales", "Management"])
        experience_level = st.selectbox("Experience Level", ["Entry-Level", "Mid-Level", "Senior"])
        workload = st.number_input("Current Workload (Interviews per week)", min_value=0)
        availability = st.text_area("Availability for the next 3 days")
        timezone = st.selectbox("Timezone", timezone_options)

        if st.button("Submit Interviewer Data"):
            if all([name, interviewer_id, role_type, experience_level, availability, timezone]):
                save_interviewer(name, interviewer_id, role_type, experience_level, workload, availability, timezone)
            else:
                st.error("Please fill all fields.")

display_dashboard()


if __name__ == "__main__":
    input()

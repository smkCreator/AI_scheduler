import streamlit as st
import json
from datetime import datetime
import os
import spacy
import dateparser
from datetime import datetime, timedelta
import pytz
import re


# File paths for JSON storage
CANDIDATES_FILE = "candidates.json"
INTERVIEWERS_FILE = "interviewers.json"

# Initialize JSON files if they don't exist
if not os.path.exists(CANDIDATES_FILE):
    with open(CANDIDATES_FILE, "w") as f:
        json.dump([], f)

if not os.path.exists(INTERVIEWERS_FILE):
    with open(INTERVIEWERS_FILE, "w") as f:
        json.dump([], f)

# Function to load data from JSON
def load_data(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

# Function to save data to JSON
def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


# Load SpaCy's English model
nlp = spacy.load("en_core_web_sm")

def nlp_process(availability, timezone, default_timezone="Asia/Kolkata"):
    """
    Process raw availability data into a structured format.
    
    Args:
        availability (str): Raw availability input (e.g., "I am available next Monday afternoon").
        timezone (str): User-selected timezone (e.g., "UTC+5:30 (IST) - India").
        default_timezone (str): Default timezone for output (e.g., "Asia/Kolkata").
    
    Returns:
        list: Structured availability data.
    """
    # Define timezone objects
    user_timezone = pytz.timezone(timezone)
    default_tz = pytz.timezone(default_timezone)

    # Parse the input using SpaCy
    doc = nlp(availability)

    # Initialize structured availability list
    structured_availability = []

    # Extract dates using dateparser
    parsed_dates = []
    for ent in doc.ents:
        if ent.label_ == "DATE":
            parsed_date = dateparser.parse(ent.text, settings={"TIMEZONE": timezone, "RETURN_AS_TIMEZONE_AWARE": True})
            if parsed_date:
                parsed_dates.append(parsed_date.astimezone(user_timezone))

    # If no dates are found, assume the input contains relative terms (e.g., "tomorrow")
    if not parsed_dates:
        parsed_date = dateparser.parse(availability, settings={"TIMEZONE": timezone, "RETURN_AS_TIMEZONE_AWARE": True})
        if parsed_date:
            parsed_dates.append(parsed_date.astimezone(user_timezone))

    # Extract times using regex (Handles 12-hour and 24-hour formats)
    time_matches = re.findall(r"(\d{1,2}:\d{2}\s*[APap][Mm]|\d{1,2}\s*[APap][Mm]|\d{1,2}:\d{2})", availability)

    # Handle time keywords (e.g., "morning", "afternoon")
    time_keywords = ["morning", "afternoon", "evening", "night"]
    matched_keywords = [word for word in time_keywords if word in availability.lower()]

    # Define default time slots based on keywords
    if "morning" in matched_keywords:
        start_time, end_time = datetime.strptime("09:00 AM", "%I:%M %p").time(), datetime.strptime("12:00 PM", "%I:%M %p").time()
    elif "afternoon" in matched_keywords:
        start_time, end_time = datetime.strptime("12:00 PM", "%I:%M %p").time(), datetime.strptime("04:00 PM", "%I:%M %p").time()
    elif "evening" in matched_keywords:
        start_time, end_time = datetime.strptime("04:00 PM", "%I:%M %p").time(), datetime.strptime("08:00 PM", "%I:%M %p").time()
    elif "night" in matched_keywords:
        start_time, end_time = datetime.strptime("08:00 PM", "%I:%M %p").time(), datetime.strptime("11:59 PM", "%I:%M %p").time()
    else:
        # Default time slot if no specific time is provided
        start_time, end_time = datetime.strptime("10:00 AM", "%I:%M %p").time(), datetime.strptime("2:00 PM", "%I:%M %p").time()

    # If specific times are provided, override the default
    if len(time_matches) >= 2:
        start_time = datetime.strptime(time_matches[0], "%I:%M %p").time() if ":" in time_matches[0] else datetime.strptime(time_matches[0], "%I %p").time()
        end_time = datetime.strptime(time_matches[1], "%I:%M %p").time() if ":" in time_matches[1] else datetime.strptime(time_matches[1], "%I %p").time()

    # Combine parsed dates with extracted times
    for parsed_date in parsed_dates:
        start_datetime = datetime.combine(parsed_date.date(), start_time).replace(tzinfo=user_timezone)
        end_datetime = datetime.combine(parsed_date.date(), end_time).replace(tzinfo=user_timezone)

        # Convert to default timezone (IST)
        start_datetime_ist = start_datetime.astimezone(default_tz)
        end_datetime_ist = end_datetime.astimezone(default_tz)

        # Append structured data
        structured_availability.append({
            "date": start_datetime_ist.strftime("%Y-%m-%d"),
            "start": start_datetime_ist.strftime("%H:%M"),
            "end": end_datetime_ist.strftime("%H:%M"),
            "timezone": default_timezone
        })

    return structured_availability

# Function to save candidate data
def save_candidate(name, email, role_type, experience_level, availability,timezone):
    candidates = load_data(CANDIDATES_FILE)
    candidates.append({
        "name": name,
        "email": email,
        "role_type": role_type,
        "experience_level": experience_level,
        "availability": availability,
        "timezone": timezone,
        "availability_structured" : nlp_process(availability,timezone),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(CANDIDATES_FILE, candidates)
    st.success("Candidate data saved successfully!")

# Function to save interviewer data
def save_interviewer(name, interviewer_id, role_type, experience_level, workload, availability,timezone):
    interviewers = load_data(INTERVIEWERS_FILE)
    interviewers.append({
        "name": name,
        "interviewer_id": interviewer_id,
        "role_type": role_type,
        "experience_level": experience_level,
        "workload": workload,
        "availability": availability,
        "timezone": timezone,
        "availability_structured" : nlp_process(availability,timezone),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(INTERVIEWERS_FILE, interviewers)
    st.success("Interviewer data saved successfully!")

# Function to display dashboard
def display_dashboard():
    st.sidebar.title("Dashboard")
    st.sidebar.write("### Candidates")
    candidates = load_data(CANDIDATES_FILE)
    for candidate in candidates:
        st.sidebar.write(f"**Name:** {candidate['name']}, **Email:** {candidate['email']}")
        # st.sidebar.write(f"**Role Type:** {candidate['role_type']}, **Experience Level:** {candidate['experience_level']}")
        # st.sidebar.write(f"**Availability:** {candidate['availability']}")
        st.sidebar.write("---")
    
    st.sidebar.write("### Interviewers")
    interviewers = load_data(INTERVIEWERS_FILE)
    for interviewer in interviewers:
        st.sidebar.write(f"**Name:** {interviewer['name']}, **ID:** {interviewer['interviewer_id']}")
        # st.sidebar.write(f"**Role Type:** {interviewer['role_type']}, **Experience Level:** {interviewer['experience_level']}")
        # st.sidebar.write(f"**Workload:** {interviewer['workload']}")
        # st.sidebar.write(f"**Availability:** {interviewer['availability']}")
        st.sidebar.write("---")
    
    st.sidebar.write("### Total Turnaround Time")
    st.sidebar.write(f"{st.session_state.get('total_turnaround_time', 0)} seconds")

# Main function
def input():
    st.title("AI-Powered Scheduling Bot")

    # Option to choose between Candidate and Interviewer
    user_type = st.radio("Are you a Candidate or Interviewer?", ("Candidate", "Interviewer"))

    if user_type == "Candidate":
        st.header("Candidate Details")
        name = st.text_input("Name")
        email = st.text_input("Email")
        role_type = st.selectbox("Role Type", ["Technical", "Sales", "Management"])
        experience_level = st.selectbox("Experience Level", ["Entry-Level", "Mid-Level", "Senior"])
        availability = st.text_area("Availability for the next 3 days (e.g., Monday 10 AM - 2 PM, Tuesday 11 AM - 12 PM, Wednesday 3 PM - 6 PM)")
        timezone = st.selectbox("Timezone", [
    "UTC-5 (EST) -US (Eastern)",  # Eastern Standard Time
    "UTC-8 (PST) - Pacific (Canada)",  # Pacific Standard Time (Canada)
    "UTC+5:30 (IST) - India",  # Indian Standard Time
    "UTC+8 (CST) - China",  # China Standard Time
    "UTC+0 (GMT) - UK",  # Greenwich Mean Time (UK)
    "UTC+1 (CET) - Central Europe",  # Central European Time
    "UTC+2 (EET) - Eastern Europe",  # Eastern European Time
])
        
        if st.button("Submit Candidate Data"):
            if name and email and role_type and experience_level and availability and timezone:
                save_candidate(name, email, role_type, experience_level, availability,timezone)
            else:
                st.error("Please fill all fields.")

    elif user_type == "Interviewer":
        st.header("Interviewer Details")
        name = st.text_input("Name")
        interviewer_id = st.text_input("Interviewer ID")
        role_type = st.selectbox("Role Type", ["Technical", "Sales", "Management"])
        experience_level = st.selectbox("Experience Level", ["Entry-Level", "Mid-Level", "Senior"])
        workload = st.selectbox("Workload", ["High", "Medium", "Low"])
        availability = st.text_area("Availability for the next 3 days (e.g., Monday 9 AM - 5 PM, Tuesday 11 AM - 12 PM, Wednesday 1 PM - 7 PM)")
        timezone = st.selectbox("Timezone", [
    "UTC-5 (EST) - US (Eastern)",  # Eastern Standard Time
    "UTC-8 (PST) - Canada (Pacific)",  # Pacific Standard Time (Canada)
    "UTC+5:30 (IST) - India",  # Indian Standard Time
    "UTC+8 (CST) - China",  # China Standard Time
    "UTC+0 (GMT) - UK",  # Greenwich Mean Time (UK)
    "UTC+1 (CET) - Central Europe",  # Central European Time
    "UTC+2 (EET) - Eastern Europe",  # Eastern European Time
])
        
        if st.button("Submit Interviewer Data"):
            if name and interviewer_id and role_type and experience_level and workload and availability and timezone:
                save_interviewer(name, interviewer_id, role_type, experience_level, workload, availability,timezone)
            else:
                st.error("Please fill all fields.")

    # Display dashboard
    display_dashboard()

if __name__ == "__main__":
    input()
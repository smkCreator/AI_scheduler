import streamlit as st
import json
import os
import spacy
import dateparser
import pytz
import re
from datetime import datetime, timedelta
from nlp import nlp_process

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

    timezone_mapping = {
    "UTC-5 (EST) - US Eastern": "America/New_York",
    "UTC-8 (PST) - Pacific (Canada)": "America/Los_Angeles",
    "UTC+5:30 (IST) - India": "Asia/Kolkata",
    "UTC+8 (CST) - China": "Asia/Shanghai",
    "UTC+0 (GMT) - UK": "Europe/London",
    "UTC+1 (CET) - Central Europe": "Europe/Berlin",
    "UTC+2 (EET) - Eastern Europe": "Europe/Bucharest",
}


    if user_type == "Candidate":
        st.header("Candidate Details")
        name = st.text_input("Name")
        email = st.text_input("Email")
        role_type = st.selectbox("Role Type", ["Technical", "Sales", "Management"])
        experience_level = st.selectbox("Experience Level", ["Entry-Level", "Mid-Level", "Senior"])
        availability = st.text_area("Availability for the next 3 days")
        selected_timezone = st.selectbox("Timezone", list(timezone_mapping.keys()))
        timezone = timezone_mapping[selected_timezone]  # Get the correct pytz-compatible timezone


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
        workload = st.selectbox("Workload", ["High", "Medium", "Low"])
        availability = st.text_area("Availability for the next 3 days")
        selected_timezone = st.selectbox("Timezone", list(timezone_mapping.keys()))
        timezone = timezone_mapping[selected_timezone] 

        if st.button("Submit Interviewer Data"):
            if all([name, interviewer_id, role_type, experience_level, availability, timezone]):
                save_interviewer(name, interviewer_id, role_type, experience_level, workload, availability, timezone)
            else:
                st.error("Please fill all fields.")

display_dashboard()


if __name__ == "__main__":
    input()

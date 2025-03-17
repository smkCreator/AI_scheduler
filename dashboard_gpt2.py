import streamlit as st
import pandas as pd

st.title("Dashboard")

# Dummy data for now
candidates = pd.DataFrame([
    {"Name": "Alice", "Email": "alice@example.com", "Availability": "Monday 10 AM - 2 PM"},
    {"Name": "Bob", "Email": "bob@example.com", "Availability": "Wednesday 3 PM - 6 PM"},
])

recruiters = pd.DataFrame([
    {"Name": "Charlie", "Recruiter ID": "R123", "Availability": "Monday 9 AM - 5 PM"},
    {"Name": "David", "Recruiter ID": "R456", "Availability": "Wednesday 1 PM - 7 PM"},
])

st.sidebar.header("Dashboard")
st.sidebar.write("### Candidates")
st.sidebar.dataframe(candidates)
st.sidebar.write("### Recruiters")
st.sidebar.dataframe(recruiters)

st.sidebar.write("### Total Interviews Scheduled: 5")
st.sidebar.write("### Total Turnaround Time: 120 minutes")

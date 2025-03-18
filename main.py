from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import datetime, timedelta
import json
import logging

# Import our modules
from nlp_module import AvailabilityParser
from ml_module import SmartScheduler
from calender_module import CalendarIntegration as CalendarService
from database_models import SimpleDatabase, format_availability_for_scheduler
from email_module import EmailNotification

# Initialize FastAPI
app = FastAPI(title="AI Scheduling Bot", description="An AI-powered scheduling bot for interviews")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
nlp_parser = AvailabilityParser()
scheduler = SmartScheduler()
db = SimpleDatabase()
calendar_service = CalendarService()

# Pydantic models for request/response validation
class UserCreate(BaseModel):
    name: str
    email: str
    user_type: str
    priority: Optional[str] = "medium"

class AvailabilityInput(BaseModel):
    user_id: int
    text: str

class ManualAvailability(BaseModel):
    user_id: int
    slots: List[Dict[str, str]]

class ScheduleRequest(BaseModel):
    candidate_id: int
    recruiter_id: int
    duration_minutes: int = 60

class EmailScheduleRequest(BaseModel):
    candidate_email: str
    recruiter_email: str
    date: str
    time: str
    duration_minutes: int = 60

class AutoScheduleRequest(BaseModel):
    candidate_email: str
    recruiter_email: str
    duration_minutes: int = 60

class Interview(BaseModel):
    id: int
    candidate_id: int
    recruiter_id: int
    start_time: str
    end_time: str
    status: str
    location: Optional[str] = None

# Dependency for database connection
def get_db():
    try:
        yield db
    finally:
        pass  # We'll keep the connection open for the app lifecycle

# Helper function to send calendar invites
async def send_calendar_invites(interview_id: int):
    try:
        interview = db.get_interview(interview_id)
        if not interview:
            return
        
        candidate = db.get_user(interview['candidate_id'])
        recruiter = db.get_user(interview['recruiter_id'])
        
        # Format interview times
        start_time = datetime.fromisoformat(interview['start_time'])
        end_time = datetime.fromisoformat(interview['end_time'])
        duration = int((end_time - start_time).total_seconds() / 60)
        
        # Create calendar event
        event_details = calendar_service.create_event(
            title=f"Interview: {candidate['name']} with {recruiter['name']}",
            start_time=interview['start_time'],
            end_time=interview['end_time'],
            attendees=[candidate['email'], recruiter['email']],
            location=interview['location'] or "Virtual Interview",
            description="Interview scheduled by AI Scheduling Bot"
        )
        
        # Send email notifications
        email_service = EmailNotification()
        
        # Prepare interview details for email
        interview_details = {
            'candidate': candidate['name'],
            'recruiter': recruiter['name'],
            'start_time': interview['start_time'],
            'end_time': interview['end_time'],
            'meeting_link': event_details.get('calendar_link', ''),
            'location': interview['location'] or "Virtual Interview"
        }
        
        # Send emails to both parties
        email_service.send_interview_invitation(
            candidate_email=candidate['email'],
            recruiter_email=recruiter['email'],
            interview_details=interview_details
        )
        
        # Update interview status
        db.update_interview_status(interview_id, "confirmed")
        
    except Exception as e:
        logging.error(f"Failed to send calendar invites: {str(e)}")
        db.update_interview_status(interview_id, "pending")

# Routes
@app.get("/")
def read_root():
    return {"status": "active", "message": "AI Scheduling Bot is running"}

@app.post("/users/", response_model=dict)
def create_user(user: UserCreate, db=Depends(get_db)):
    user_id = db.add_user(user.name, user.email, user.user_type, user.priority)
    return {"id": user_id, **user.dict()}

@app.get("/users/{user_id}", response_model=dict)
def get_user(user_id: int, db=Depends(get_db)):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=List[dict])
def get_users_by_type(user_type: str, db=Depends(get_db)):
    return db.get_users_by_type(user_type)

@app.post("/availability/parse", response_model=List[dict])
def parse_availability(input_data: AvailabilityInput, db=Depends(get_db)):
    # Use NLP to parse the text input
    availability_slots = nlp_parser.extract_availability(input_data.text)
    
    # Clear existing availability
    db.clear_user_availability(input_data.user_id)
    
    # Store the parsed availability
    for slot in availability_slots:
        db.add_availability(
            input_data.user_id,
            slot['start'],
            slot['end'],
            input_data.text
        )
    
    return availability_slots

@app.post("/availability/manual", response_model=dict)
def add_manual_availability(input_data: ManualAvailability, db=Depends(get_db)):
    # Clear existing availability
    db.clear_user_availability(input_data.user_id)
    
    # Add each availability slot
    added_slots = []
    for slot in input_data.slots:
        slot_id = db.add_availability(
            input_data.user_id,
            slot['start'],
            slot['end'],
            "Manually added"
        )
        added_slots.append(slot_id)
    
    return {"user_id": input_data.user_id, "added_slots": added_slots}

@app.get("/availability/{user_id}", response_model=List[dict])
def get_user_availability(user_id: int, db=Depends(get_db)):
    return db.get_user_availability(user_id)

@app.post("/schedule", response_model=dict)
async def schedule_interview(
    request: ScheduleRequest, 
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    # Get candidate and recruiter info
    candidate = db.get_user(request.candidate_id)
    recruiter = db.get_user(request.recruiter_id)
    
    if not candidate or not recruiter:
        raise HTTPException(status_code=404, detail="Candidate or recruiter not found")
    
    # Get availability
    candidate_avail = db.get_user_availability(request.candidate_id)
    recruiter_avail = db.get_user_availability(request.recruiter_id)
    
    if not candidate_avail or not recruiter_avail:
        raise HTTPException(status_code=400, detail="Missing availability data")
    
    # Format availability for scheduler
    candidate_slots = format_availability_for_scheduler(candidate_avail)
    recruiter_slots = format_availability_for_scheduler(recruiter_avail)
    
    # Get recent interviews for learning patterns
    recent_interviews = db.get_user_interviews(request.recruiter_id)
    
    # Find optimal slots
    optimal_slots = scheduler.find_optimal_slots(
        candidate_slots,
        recruiter_slots,
        {"id": candidate["id"], "priority": candidate["priority"]},
        recent_interviews
    )
    
    if not optimal_slots:
        raise HTTPException(status_code=404, detail="No matching availability found")
    
    # Take the best slot
    best_slot = optimal_slots[0]
    
    # Calculate end time based on requested duration
    start_time = datetime.fromisoformat(best_slot['start'])
    end_time = start_time + timedelta(minutes=request.duration_minutes)
    
    # Generate a simple meeting link (would be replaced with actual meeting generation)
    meeting_link = f"https://meet.company.com/{hash(start_time) % 1000000:06d}"
    
    # Schedule the interview
    interview_id = db.schedule_interview(
        request.candidate_id,
        request.recruiter_id,
        best_slot['start'],
        end_time.isoformat(),
        meeting_link
    )
    
    # Send calendar invites asynchronously
    background_tasks.add_task(send_calendar_invites, interview_id)
    
    return {
        "interview_id": interview_id,
        "candidate": candidate["name"],
        "recruiter": recruiter["name"],
        "start_time": best_slot['start'],
        "end_time": end_time.isoformat(),
        "score": best_slot['score'],
        "meeting_link": meeting_link
    }

@app.post("/schedule_by_email", response_model=dict)
def schedule_interview_by_email(request: EmailScheduleRequest, db=Depends(get_db)):
    # Lookup candidate and recruiter by their email
    candidate = db.get_user_by_email(request.candidate_email)
    recruiter = db.get_user_by_email(request.recruiter_email)
    if not candidate or not recruiter:
        raise HTTPException(status_code=404, detail="Candidate or Recruiter not found")
    
    try:
        interview_start = datetime.fromisoformat(f"{request.date}T{request.time}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")
    
    interview_end = interview_start + timedelta(minutes=request.duration_minutes)
    meeting_link = f"https://meet.company.com/{hash(interview_start) % 1000000:06d}"
    
    # Schedule the interview
    interview_id = db.schedule_interview(candidate['id'], recruiter['id'], interview_start.isoformat(), interview_end.isoformat(), meeting_link)
    
    # Activate background task to send calendar invites
    import asyncio
    asyncio.create_task(send_calendar_invites(interview_id))
    
    return {"interview_id": interview_id, "message": "Interview scheduled successfully"}

@app.post("/auto_schedule_by_email", response_model=dict)
async def auto_schedule_by_email(request: AutoScheduleRequest, background_tasks: BackgroundTasks, db=Depends(get_db)):
    """
    Automatically find the optimal time and schedule an interview based on candidate and recruiter emails.
    This endpoint handles the complete automation flow:
    1. Look up the candidate and recruiter by email
    2. Get their availability
    3. Find the optimal time slot
    4. Schedule the interview
    5. Send email notifications and calendar invites
    """
    # Lookup candidate and recruiter by their email
    candidate = db.get_user_by_email(request.candidate_email)
    recruiter = db.get_user_by_email(request.recruiter_email)
    
    if not candidate or not recruiter:
        raise HTTPException(status_code=404, detail="Candidate or Recruiter not found")
    
    # Get availability for both users
    candidate_avail = db.get_user_availability(candidate['id'])
    recruiter_avail = db.get_user_availability(recruiter['id'])
    
    if not candidate_avail or not recruiter_avail:
        raise HTTPException(status_code=400, 
                           detail="Missing availability data. Please ensure both participants have shared their availability.")
    
    # Format availability for scheduler
    candidate_slots = format_availability_for_scheduler(candidate_avail)
    recruiter_slots = format_availability_for_scheduler(recruiter_avail)
    
    # Get recent interviews for learning patterns
    recent_interviews = db.get_user_interviews(recruiter['id'])
    
    # Find optimal slots using the AI scheduler
    optimal_slots = scheduler.find_optimal_slots(
        candidate_slots,
        recruiter_slots,
        {"id": candidate["id"], "priority": candidate.get("priority", "medium")},
        recent_interviews
    )
    
    if not optimal_slots:
        raise HTTPException(status_code=404, 
                           detail="No matching availability found. Please ask participants to provide more availability options.")
    
    # Take the best slot
    best_slot = optimal_slots[0]
    
    # Calculate end time based on requested duration
    start_time = datetime.fromisoformat(best_slot['start'])
    end_time = start_time + timedelta(minutes=request.duration_minutes)
    
    # Generate a meeting link
    meeting_link = f"https://meet.company.com/{hash(start_time) % 1000000:06d}"
    
    # Schedule the interview
    interview_id = db.schedule_interview(
        candidate['id'],
        recruiter['id'],
        start_time.isoformat(),
        end_time.isoformat(),
        meeting_link
    )
    
    # Schedule calendar invites and email notifications as a background task
    background_tasks.add_task(send_calendar_invites, interview_id)
    
    # Return success response with optimal time details
    return {
        "interview_id": interview_id,
        "candidate": candidate['name'],
        "candidate_id": candidate['id'],
        "recruiter": recruiter['name'],
        "recruiter_id": recruiter['id'],
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "meeting_link": meeting_link,
        "score": best_slot.get('score', 0.95),
        "status": "scheduled",
        "message": "Interview automatically scheduled at optimal time. Notifications sent."
    }

@app.get("/interviews/{user_id}", response_model=List[dict])
def get_interviews(user_id: int, db=Depends(get_db)):
    return db.get_user_interviews(user_id)

@app.put("/interviews/{interview_id}", response_model=dict)
def update_interview_status(interview_id: int, status: str, db=Depends(get_db)):
    if status not in ["scheduled", "completed", "cancelled", "rescheduled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    success = db.update_interview_status(interview_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return {"id": interview_id, "status": status}

@app.post("/demo/init", response_model=dict)
def initialize_demo_data(db=Depends(get_db)):
    return db.load_demo_data()

# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
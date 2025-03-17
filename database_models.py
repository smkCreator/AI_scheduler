# simple_database.py
from datetime import datetime, timedelta
import json
import sqlite3
from typing import List, Dict, Any

class SimpleDatabase:
    """
    A simple database implementation using SQLite for the scheduling bot.
    Focuses only on essential tables needed for demonstration.
    """
    
    def __init__(self, db_path="scheduler.db"):
        """Initialize database connection"""
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Create the minimal tables needed for the scheduler"""
        # Create users table (combined candidates and recruiters)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            user_type TEXT NOT NULL,  -- 'candidate' or 'recruiter'
            priority TEXT DEFAULT 'medium',  -- for candidates: low, medium, high
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create availability table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            source_text TEXT,  -- Original text from NLP parsing
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create interviews table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            recruiter_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'scheduled',  -- scheduled, completed, cancelled
            location TEXT,  -- URL or physical location
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES users (id),
            FOREIGN KEY (recruiter_id) REFERENCES users (id)
        )
        ''')
        
        self.conn.commit()
    
    # User operations
    def add_user(self, name: str, email: str, user_type: str, priority: str = 'medium') -> int:
        """Add a new user and return their ID"""
        self.cursor.execute(
            "INSERT INTO users (name, email, user_type, priority) VALUES (?, ?, ?, ?)",
            (name, email, user_type, priority)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_user(self, user_id: int) -> Dict:
        """Get user by ID"""
        self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return dict(self.cursor.fetchone() or {})
    
    def get_users_by_type(self, user_type: str) -> List[Dict]:
        """Get all users of a specific type"""
        self.cursor.execute("SELECT * FROM users WHERE user_type = ?", (user_type,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # Availability operations
    def add_availability(self, user_id: int, start_time: str, end_time: str, source_text: str = None) -> int:
        """Add availability for a user"""
        self.cursor.execute(
            "INSERT INTO availability (user_id, start_time, end_time, source_text) VALUES (?, ?, ?, ?)",
            (user_id, start_time, end_time, source_text)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_user_availability(self, user_id: int) -> List[Dict]:
        """Get all availability for a user"""
        self.cursor.execute("SELECT * FROM availability WHERE user_id = ?", (user_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def clear_user_availability(self, user_id: int):
        """Clear all availability for a user"""
        self.cursor.execute("DELETE FROM availability WHERE user_id = ?", (user_id,))
        self.conn.commit()
    
    # Interview operations
    def schedule_interview(self, candidate_id: int, recruiter_id: int, 
                           start_time: str, end_time: str, location: str = None) -> int:
        """Schedule a new interview"""
        self.cursor.execute(
            """INSERT INTO interviews 
               (candidate_id, recruiter_id, start_time, end_time, location) 
               VALUES (?, ?, ?, ?, ?)""",
            (candidate_id, recruiter_id, start_time, end_time, location)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_interview(self, interview_id: int) -> Dict:
        """Get interview by ID"""
        self.cursor.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
        return dict(self.cursor.fetchone() or {})
    
    def get_user_interviews(self, user_id: int) -> List[Dict]:
        """Get all interviews for a user (as candidate or recruiter)"""
        self.cursor.execute(
            """SELECT * FROM interviews 
               WHERE candidate_id = ? OR recruiter_id = ?
               ORDER BY start_time""", 
            (user_id, user_id)
        )
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_interview_status(self, interview_id: int, status: str) -> bool:
        """Update the status of an interview"""
        self.cursor.execute(
            "UPDATE interviews SET status = ? WHERE id = ?",
            (status, interview_id)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    # Utility functions for demo purposes
    def load_demo_data(self):
        """Load some demo data for testing/presentation purposes"""
        # Add sample users
        candidate1 = self.add_user("John Doe", "john@example.com", "candidate", "high")
        candidate2 = self.add_user("Jane Smith", "jane@example.com", "candidate", "medium")
        recruiter1 = self.add_user("HR Manager", "hr@company.com", "recruiter")
        recruiter2 = self.add_user("Tech Lead", "tech@company.com", "recruiter")
        
        # Add sample availability
        # Current timestamp for demo purposes
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Candidate availability
        self.add_availability(
            candidate1, 
            f"{today} 10:00:00", 
            f"{today} 12:00:00", 
            "I'm available from 10 AM to noon today"
        )
        self.add_availability(
            candidate1, 
            f"{tomorrow} 14:00:00", 
            f"{tomorrow} 17:00:00", 
            "I can also do tomorrow afternoon"
        )
        self.add_availability(
            candidate2, 
            f"{today} 13:00:00", 
            f"{today} 16:00:00", 
            "I'm free this afternoon from 1-4 PM"
        )
        
        # Recruiter availability
        self.add_availability(
            recruiter1, 
            f"{today} 09:00:00", 
            f"{today} 17:00:00", 
            "I work standard hours"
        )
        self.add_availability(
            recruiter2, 
            f"{today} 11:00:00", 
            f"{today} 15:00:00", 
            "Available for interviews from 11 AM to 3 PM"
        )
        
        # Add a sample interview
        self.schedule_interview(
            candidate1,
            recruiter1,
            f"{today} 11:00:00",
            f"{today} 12:00:00",
            "https://meet.google.com/abc-defg-hij"
        )
        
        return {
            "candidates": [candidate1, candidate2],
            "recruiters": [recruiter1, recruiter2]
        }
    
    def close(self):
        """Close the database connection"""
        self.conn.close()


# Helper function to convert database rows to the format expected by the scheduling algorithm
def format_availability_for_scheduler(db_availabilities: List[Dict]) -> List[Dict]:
    """Convert database availability format to scheduler format"""
    formatted = []
    for avail in db_availabilities:
        formatted.append({
            'start': avail['start_time'],
            'end': avail['end_time'],
            'user_id': avail['user_id']
        })
    return formatted


# Example usage
if __name__ == "__main__":
    db = SimpleDatabase(":memory:")  # In-memory database for testing
    
    # Load demo data
    demo_data = db.load_demo_data()
    
    # Examples of retrieving data
    candidate_id = demo_data["candidates"][0]
    recruiter_id = demo_data["recruiters"][0]
    
    candidate_avail = db.get_user_availability(candidate_id)
    print(f"Candidate availability: {candidate_avail}")
    
    scheduled_interviews = db.get_user_interviews(candidate_id)
    print(f"Scheduled interviews: {scheduled_interviews}")
    
    db.close()
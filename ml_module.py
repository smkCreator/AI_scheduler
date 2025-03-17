import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder

class SmartScheduler:
    def __init__(self):
        self.model = None
        self.feature_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        self.candidate_priority_weights = {
            "high": 3.0, 
            "medium": 2.0, 
            "low": 1.0  
        }
        
    def train_model(self, historical_data: List[Dict]):
        if not historical_data or len(historical_data) < 10:
            return False
            
        features = []
        outcomes = []
        
        for entry in historical_data:
            day_of_week = datetime.fromisoformat(entry['slot_start']).weekday()
            hour_of_day = datetime.fromisoformat(entry['slot_start']).hour
            interviewer_id = entry['interviewer_id']
            candidate_level = entry['candidate_level']
            
            features.append([day_of_week, hour_of_day, interviewer_id, candidate_level])
            outcomes.append(1 if entry['completed_successfully'] else 0)

        feature_df = pd.DataFrame(features, columns=['day_of_week', 'hour_of_day', 
                                                    'interviewer_id', 'candidate_level'])

        categorical_cols = ['interviewer_id', 'candidate_level']
        feature_df_encoded = pd.get_dummies(feature_df, columns=categorical_cols)

        self.model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        self.model.fit(feature_df_encoded, outcomes)
        
        return True
    
    def find_optimal_slots(self, 
                          candidate_availability: List[Dict],
                          recruiter_availability: List[Dict],
                          candidate_info: Dict,
                          recent_schedules: Optional[List[Dict]] = None) -> List[Dict]:

        overlapping_slots = self._find_overlapping_slots(candidate_availability, recruiter_availability)
        
        if not overlapping_slots:
            return []

        scored_slots = self._score_slots(overlapping_slots, candidate_info, recent_schedules)

        return sorted(scored_slots, key=lambda x: x['score'], reverse=True)
    
    def _find_overlapping_slots(self, 
                               candidate_slots: List[Dict],
                               recruiter_slots: List[Dict]) -> List[Dict]:
        overlapping = []
        
        for c_slot in candidate_slots:
            c_start = datetime.fromisoformat(c_slot['start'])
            c_end = datetime.fromisoformat(c_slot['end'])
            
            for r_slot in recruiter_slots:
                r_start = datetime.fromisoformat(r_slot['start'])
                r_end = datetime.fromisoformat(r_slot['end'])
                
                overlap_start = max(c_start, r_start)
                overlap_end = min(c_end, r_end)
                
                if overlap_start < overlap_end:
                    duration = (overlap_end - overlap_start).total_seconds() / 60  

                    if duration >= 30:
                        overlapping.append({
                            'start': overlap_start.isoformat(),
                            'end': overlap_end.isoformat(),
                            'duration_minutes': duration,
                            'candidate_id': c_slot.get('candidate_id'),
                            'recruiter_id': r_slot.get('recruiter_id')
                        })
        
        return overlapping
    
    def _score_slots(self, 
                    slots: List[Dict],
                    candidate_info: Dict,
                    recent_schedules: Optional[List[Dict]] = None) -> List[Dict]:

        scored_slots = []
        
        for slot in slots:
            score = 0
            slot_datetime = datetime.fromisoformat(slot['start'])
            
            hour = slot_datetime.hour
            if 10 <= hour <= 11 or 14 <= hour <= 16:  
                score += 30
            elif 9 <= hour <= 17: 
                score += 20
            else:  
                score += 10

            day_of_week = slot_datetime.weekday()
            if 0 <= day_of_week <= 4: 
                score += 20
                if 1 <= day_of_week <= 3:
                    score += 5

            candidate_priority = candidate_info.get('priority', 'medium')
            priority_weight = self.candidate_priority_weights.get(candidate_priority, 1.0)
            score *= priority_weight

            if recent_schedules and len(recent_schedules) > 0:
                historical_bonus = self._calculate_historical_bonus(slot, recent_schedules)
                score += historical_bonus
            
            if self.model is not None:
                ml_score = self._predict_slot_score(slot, candidate_info)
                score = 0.3 * score + 0.7 * (ml_score * 100)
            
            slot_with_score = slot.copy()
            slot_with_score['score'] = score
            scored_slots.append(slot_with_score)
        
        return scored_slots
    
    def _calculate_historical_bonus(self, slot: Dict, recent_schedules: List[Dict]) -> float:
        bonus = 0
        slot_time = datetime.fromisoformat(slot['start'])
        slot_hour = slot_time.hour
        slot_day = slot_time.weekday()

        for schedule in recent_schedules:
            schedule_time = datetime.fromisoformat(schedule['start'])
            
            if abs(schedule_time.hour - slot_hour) <= 1:
                bonus += 5
                
            if schedule_time.weekday() == slot_day:
                bonus += 3
                
            if schedule.get('completed_successfully', False):
                bonus += 2
        
        return min(bonus, 25) 
        
    def _predict_slot_score(self, slot: Dict, candidate_info: Dict) -> float:
        if self.model is None:
            return 0.5  

        slot_time = datetime.fromisoformat(slot['start'])
        day_of_week = slot_time.weekday()
        hour_of_day = slot_time.hour
        interviewer_id = slot.get('recruiter_id', 'unknown')
        candidate_level = candidate_info.get('level', 'mid')
        
        feature_vector = pd.DataFrame({
            'day_of_week': [day_of_week],
            'hour_of_day': [hour_of_day],
            'interviewer_id': [interviewer_id],
            'candidate_level': [candidate_level]
        })
        
        feature_vector_encoded = pd.get_dummies(feature_vector, 
                                              columns=['interviewer_id', 'candidate_level'])
        
        missing_cols = set(self.model.feature_names_in_) - set(feature_vector_encoded.columns)
        for col in missing_cols:
            feature_vector_encoded[col] = 0
        
        feature_vector_encoded = feature_vector_encoded[self.model.feature_names_in_]
        
        probabilities = self.model.predict_proba(feature_vector_encoded)
        return probabilities[0][1]

if __name__ == "__main__":
    scheduler = SmartScheduler()

    candidate_availability = [
        {
            'start': '2025-03-17T09:00:00',
            'end': '2025-03-17T12:00:00',
            'candidate_id': 'C001'
        },
        {
            'start': '2025-03-18T14:00:00',
            'end': '2025-03-18T17:00:00',
            'candidate_id': 'C001'
        }
    ]
    
    recruiter_availability = [
        {
            'start': '2025-03-17T10:00:00',
            'end': '2025-03-17T15:00:00',
            'recruiter_id': 'R001'
        },
        {
            'start': '2025-03-18T09:00:00',
            'end': '2025-03-18T16:00:00',
            'recruiter_id': 'R001'
        }
    ]
    
    candidate_info = {
        'id': 'C001',
        'name': 'John Doe',
        'level': 'senior',
        'priority': 'high',
        'position': 'AI Engineer'
    }
    
    optimal_slots = scheduler.find_optimal_slots(
        candidate_availability,
        recruiter_availability,
        candidate_info
    )
    
    print("Optimal interview slots:")
    for slot in optimal_slots:
        print(f"- {slot['start']} to {slot['end']} (Score: {slot['score']:.2f})")
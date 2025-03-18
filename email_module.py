import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

class EmailNotification:
    def __init__(self, smtp_server=None, smtp_port=None, sender_email=None, sender_password=None):
        """
        Initialize the email notification service.
        If credentials are not provided, will try to use environment variables:
        - EMAIL_SMTP_SERVER
        - EMAIL_SMTP_PORT
        - EMAIL_SENDER
        - EMAIL_PASSWORD
        """
        self.smtp_server = smtp_server or os.environ.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.environ.get('EMAIL_SMTP_PORT', 587))
        self.sender_email = sender_email or os.environ.get('EMAIL_SENDER', '')
        self.sender_password = sender_password or os.environ.get('EMAIL_PASSWORD', '')
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def send_interview_invitation(self, 
                                 candidate_email: str, 
                                 recruiter_email: str,
                                 interview_details: Dict,
                                 additional_recipients: List[str] = None) -> bool:
        """
        Send interview invitation emails to both candidate and recruiter.
        
        Args:
            candidate_email: Email address of the candidate
            recruiter_email: Email address of the recruiter
            interview_details: Dictionary containing interview details
            additional_recipients: List of additional email addresses to include
            
        Returns:
            bool: True if emails were sent successfully, False otherwise
        """
        try:
            # Format the interview details
            start_time = datetime.fromisoformat(interview_details['start_time'])
            end_time = datetime.fromisoformat(interview_details['end_time'])
            
            formatted_start = start_time.strftime("%A, %B %d, %Y at %I:%M %p")
            formatted_end = end_time.strftime("%I:%M %p")
            duration = int((end_time - start_time).total_seconds() / 60)
            
            # Create message for candidate
            candidate_subject = f"Interview Scheduled: {formatted_start}"
            candidate_body = self._generate_candidate_email(
                interview_details['candidate'],
                interview_details['recruiter'],
                formatted_start,
                formatted_end,
                duration,
                interview_details.get('meeting_link', 'Details to follow'),
                interview_details.get('location', 'Virtual')
            )
            
            # Create message for recruiter
            recruiter_subject = f"Interview Scheduled with {interview_details['candidate']}: {formatted_start}"
            recruiter_body = self._generate_recruiter_email(
                interview_details['candidate'],
                interview_details['recruiter'],
                formatted_start,
                formatted_end,
                duration,
                interview_details.get('meeting_link', 'Details to follow'),
                interview_details.get('location', 'Virtual')
            )
            
            # Send emails
            self._send_email(candidate_email, candidate_subject, candidate_body)
            self._send_email(recruiter_email, recruiter_subject, recruiter_body)
            
            # Send to additional recipients if provided
            if additional_recipients:
                for email in additional_recipients:
                    self._send_email(email, recruiter_subject, recruiter_body)
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send interview invitation: {str(e)}")
            return False
    
    def send_rescheduling_notification(self, 
                                      recipient_email: str,
                                      interview_details: Dict,
                                      reason: str = None) -> bool:
        """
        Send notification about rescheduled interview.
        
        Args:
            recipient_email: Email address of the recipient
            interview_details: Dictionary containing interview details
            reason: Reason for rescheduling (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Format the interview details
            start_time = datetime.fromisoformat(interview_details['start_time'])
            formatted_start = start_time.strftime("%A, %B %d, %Y at %I:%M %p")
            
            subject = f"Interview Rescheduled: {formatted_start}"
            body = self._generate_reschedule_email(
                interview_details['candidate'],
                interview_details['recruiter'],
                formatted_start,
                reason or "A scheduling conflict has occurred."
            )
            
            return self._send_email(recipient_email, subject, body)
            
        except Exception as e:
            self.logger.error(f"Failed to send rescheduling notification: {str(e)}")
            return False
    
    def send_reminder(self, 
                     recipient_email: str,
                     interview_details: Dict,
                     hours_before: int = 24) -> bool:
        """
        Send reminder about upcoming interview.
        
        Args:
            recipient_email: Email address of the recipient
            interview_details: Dictionary containing interview details
            hours_before: How many hours before the interview to mention in the reminder
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Format the interview details
            start_time = datetime.fromisoformat(interview_details['start_time'])
            formatted_start = start_time.strftime("%A, %B %d, %Y at %I:%M %p")
            
            subject = f"Interview Reminder: {formatted_start}"
            
            # Determine if this is for candidate or recruiter
            is_candidate = recipient_email == interview_details.get('candidate_email')
            
            body = self._generate_reminder_email(
                interview_details['candidate'],
                interview_details['recruiter'],
                formatted_start,
                interview_details.get('meeting_link', 'Check calendar invite'),
                is_candidate,
                hours_before
            )
            
            return self._send_email(recipient_email, subject, body)
            
        except Exception as e:
            self.logger.error(f"Failed to send reminder: {str(e)}")
            return False
    
    def _send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send an email using the configured SMTP server."""
        if not self.sender_email or not self.sender_password:
            self.logger.error("Email sender credentials not configured")
            return False
            
        try:
            # Create message
            message = MIMEMultipart()
            message['From'] = self.sender_email
            message['To'] = recipient
            message['Subject'] = subject
            
            # Add body to email
            message.attach(MIMEText(body, 'html'))
            
            # Connect to server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure the connection
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                
            self.logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _generate_candidate_email(self, 
                                 candidate_name: str,
                                 recruiter_name: str,
                                 start_time: str,
                                 end_time: str,
                                 duration: int,
                                 meeting_link: str,
                                 location: str) -> str:
        """Generate HTML email content for candidate."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Interview Confirmation</h2>
                <p>Hello {candidate_name},</p>
                <p>Your interview has been scheduled with {recruiter_name}.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Date and Time:</strong> {start_time} - {end_time}</p>
                    <p><strong>Duration:</strong> {duration} minutes</p>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Meeting Link:</strong> <a href="{meeting_link}">{meeting_link}</a></p>
                </div>
                
                <p>Please review the calendar invitation that has been sent to your email.</p>
                <p>If you need to reschedule, please reply to this email as soon as possible.</p>
                
                <p>Best regards,<br>
                AI Scheduling Bot</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_recruiter_email(self,
                                 candidate_name: str,
                                 recruiter_name: str,
                                 start_time: str,
                                 end_time: str,
                                 duration: int,
                                 meeting_link: str,
                                 location: str) -> str:
        """Generate HTML email content for recruiter."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Interview Scheduled</h2>
                <p>Hello {recruiter_name},</p>
                <p>An interview has been scheduled with candidate {candidate_name}.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Date and Time:</strong> {start_time} - {end_time}</p>
                    <p><strong>Duration:</strong> {duration} minutes</p>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Meeting Link:</strong> <a href="{meeting_link}">{meeting_link}</a></p>
                </div>
                
                <p>The candidate has been notified and a calendar invitation has been sent to both of you.</p>
                <p>If you need to reschedule, please use the scheduling system to find a new time.</p>
                
                <p>Best regards,<br>
                AI Scheduling Bot</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_reschedule_email(self,
                                  candidate_name: str,
                                  recruiter_name: str,
                                  new_time: str,
                                  reason: str) -> str:
        """Generate HTML email content for rescheduling notification."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Interview Rescheduled</h2>
                <p>The interview between {candidate_name} and {recruiter_name} has been rescheduled.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>New Date and Time:</strong> {new_time}</p>
                    <p><strong>Reason:</strong> {reason}</p>
                </div>
                
                <p>An updated calendar invitation has been sent to your email.</p>
                
                <p>Best regards,<br>
                AI Scheduling Bot</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_reminder_email(self,
                                candidate_name: str,
                                recruiter_name: str,
                                interview_time: str,
                                meeting_link: str,
                                is_candidate: bool,
                                hours_before: int) -> str:
        """Generate HTML email content for reminder."""
        recipient = "candidate" if is_candidate else "recruiter"
        recipient_name = candidate_name if is_candidate else recruiter_name
        other_person = recruiter_name if is_candidate else candidate_name
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Interview Reminder</h2>
                <p>Hello {recipient_name},</p>
                <p>This is a reminder that you have an interview {'with' if is_candidate else 'for'} {other_person} scheduled for {interview_time} ({hours_before} hours from now).</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Meeting Link:</strong> <a href="{meeting_link}">{meeting_link}</a></p>
                </div>
                
                <p>Please ensure you are prepared and available at the scheduled time.</p>
                
                <p>Best regards,<br>
                AI Scheduling Bot</p>
            </div>
        </body>
        </html>
        """
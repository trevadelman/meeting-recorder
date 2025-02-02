import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from pathlib import Path
from datetime import datetime
from .audio import TranscriptSegment
from typing import List

class EmailService:
    def __init__(self):
        from config.config import EMAIL_CONFIG
        self.smtp_server = EMAIL_CONFIG['SMTP_SERVER']
        self.smtp_port = EMAIL_CONFIG['SMTP_PORT']
        self.sender_email = EMAIL_CONFIG['EMAIL_USER']
        self.password = EMAIL_CONFIG['EMAIL_PASSWORD']
        self.base_url = EMAIL_CONFIG['BASE_URL']
        
        if not self.sender_email or not self.password:
            raise ValueError("Email credentials not found in configuration")
            
        # Initialize database manager
        from .db import DatabaseManager
        self.db = DatabaseManager()

    def _create_meeting_html(
        self,
        meeting_id: str,
        title: str,
        date: datetime,
        duration: float,
        summary: str,
        transcript: List[TranscriptSegment]
    ) -> str:
        """Create HTML content for meeting email"""
        # Format duration
        minutes, seconds = divmod(int(duration), 60)
        hours, minutes = divmod(minutes, 60)
        duration_str = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

        meeting_url = f"{self.base_url}/meeting/{meeting_id}"

        # Get notes from meeting
        meeting = self.db.get_meeting(meeting_id)
        notes = meeting.notes if meeting else None

        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Meeting Summary: {title}</h2>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Date:</strong> {date.strftime('%B %d, %Y %I:%M %p')}</p>
                    <p><strong>Duration:</strong> {duration_str}</p>
                </div>
                
                <h3 style="color: #2c3e50;">Summary</h3>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="white-space: pre-line;">{summary}</p>
                </div>

                {f'''
                <h3 style="color: #2c3e50;">Notes</h3>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="white-space: pre-line;">{notes}</p>
                </div>
                ''' if notes else ''}
                
                <div style="margin: 30px 0;">
                    <a href="{meeting_url}" 
                       style="background-color: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px;">
                        View Full Meeting Details
                    </a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #6c757d; font-size: 0.9em;">
                    This is an automated message from the Meeting Recorder system.
                </p>
            </body>
        </html>
        """

    def send_meeting_email(
        self,
        recipient_email: str,
        meeting_id: str,
        title: str,
        date: datetime,
        duration: float,
        summary: str,
        transcript: List[TranscriptSegment]
    ) -> bool:
        """Send meeting summary email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Meeting Summary: {title}"
            msg['From'] = self.sender_email
            msg['To'] = recipient_email

            html_content = self._create_meeting_html(
                meeting_id=meeting_id,
                title=title,
                date=date,
                duration=duration,
                summary=summary,
                transcript=transcript
            )
            
            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

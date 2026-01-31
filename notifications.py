"""
Video Content Management System - Email Notification Module
Handles automated email reminders and notifications
"""

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
import os

DATA_DIR = Path(__file__).parent / "data"


class EmailNotifier:
    def __init__(self, smtp_server=None, smtp_port=None, email=None, password=None):
        """Initialize email notifier with SMTP settings"""
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", 587))
        self.email = email or os.getenv("SMTP_EMAIL")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.admin_name = os.getenv("ADMIN_NAME", "Content Manager")
        self.social_media_tech_email = os.getenv("SOCIAL_MEDIA_TECH_EMAIL")
    
    def load_notification_log(self):
        """Load notification history"""
        try:
            with open(DATA_DIR / "notifications.json", "r") as f:
                return json.load(f)
        except:
            return {"notifications": [], "email_log": []}
    
    def save_notification_log(self, log_data):
        """Save notification history"""
        with open(DATA_DIR / "notifications.json", "w") as f:
            json.dump(log_data, f, indent=4, default=str)
    
    def log_email(self, to_email, subject, status, error=None):
        """Log email send attempt"""
        log = self.load_notification_log()
        log["email_log"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "to": to_email,
            "subject": subject,
            "status": status,
            "error": error
        })
        self.save_notification_log(log)
    
    def get_assignment_template(self, team_name, deadline, deadline_day):
        """Email template for new assignment notification"""
        subject = f"📹 Video Submission Assignment - Due {deadline_day}"
        
        body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .deadline-box {{ background: white; border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .deadline-date {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 New Video Assignment</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{team_name}</strong>!</p>
            
            <p>You have been assigned to submit a video for our social media content this week.</p>
            
            <div class="deadline-box">
                <p style="margin: 0; color: #666;">Submission Deadline:</p>
                <p class="deadline-date" style="margin: 5px 0;">{deadline_day}, {deadline}</p>
                <p style="margin: 0; color: #666;">by 6:00 PM</p>
            </div>
            
            <h3>📋 Submission Guidelines:</h3>
            <ul>
                <li>Video should be optimized for social media (vertical or square format preferred)</li>
                <li>Maximum duration: 60 seconds for Reels/Shorts, 3 minutes for regular posts</li>
                <li>Include any captions or hashtag suggestions</li>
                <li>Submit via the content management dashboard</li>
            </ul>
            
            <p>Please ensure timely submission to maintain our publishing schedule.</p>
            
            <p>Best regards,<br><strong>{self.admin_name}</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated notification from the Video Content Management System</p>
        </div>
    </div>
</body>
</html>
"""
        return subject, body
    
    def get_reminder_template(self, team_name, deadline, deadline_day, days_remaining):
        """Email template for reminder notifications"""
        urgency = "⚠️ URGENT" if days_remaining <= 1 else "🔔"
        
        subject = f"{urgency} Reminder: Video Due in {days_remaining} Day{'s' if days_remaining > 1 else ''} - {team_name}"
        
        urgency_color = "#dc3545" if days_remaining <= 1 else "#ffc107" if days_remaining <= 3 else "#17a2b8"
        
        body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {urgency_color}; color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .countdown {{ font-size: 48px; font-weight: bold; text-align: center; color: {urgency_color}; margin: 20px 0; }}
        .deadline-box {{ background: white; border: 2px solid {urgency_color}; padding: 20px; margin: 20px 0; border-radius: 10px; text-align: center; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{urgency} Submission Reminder</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{team_name}</strong>!</p>
            
            <p>This is a friendly reminder that your video submission is due soon.</p>
            
            <div class="countdown">{days_remaining} Day{'s' if days_remaining > 1 else ''} Left</div>
            
            <div class="deadline-box">
                <p style="margin: 0; color: #666;">Deadline:</p>
                <p style="font-size: 20px; font-weight: bold; margin: 5px 0;">{deadline_day}, {deadline}</p>
                <p style="margin: 0; color: #666;">6:00 PM</p>
            </div>
            
            {"<p style='color: #dc3545; font-weight: bold;'>⚠️ Please submit your video as soon as possible to avoid missing the deadline!</p>" if days_remaining <= 1 else ""}
            
            <p>If you have any questions or need an extension, please contact us immediately.</p>
            
            <p>Best regards,<br><strong>{self.admin_name}</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated reminder from the Video Content Management System</p>
        </div>
    </div>
</body>
</html>
"""
        return subject, body
    
    def get_overdue_template(self, team_name, deadline, days_overdue):
        """Email template for overdue notifications"""
        subject = f"🚨 OVERDUE: Video Submission Required Immediately - {team_name}"
        
        body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #dc3545; color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .overdue-box {{ background: #fff5f5; border: 2px solid #dc3545; padding: 20px; margin: 20px 0; border-radius: 10px; text-align: center; }}
        .overdue-days {{ font-size: 36px; font-weight: bold; color: #dc3545; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Submission Overdue</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{team_name}</strong>,</p>
            
            <p>Your video submission deadline has passed. Please submit your video immediately.</p>
            
            <div class="overdue-box">
                <p style="margin: 0; color: #666;">Original Deadline:</p>
                <p style="font-size: 18px; margin: 5px 0;"><s>{deadline}</s></p>
                <p class="overdue-days">{days_overdue} Day{'s' if days_overdue > 1 else ''} Overdue</p>
            </div>
            
            <p style="color: #dc3545; font-weight: bold;">Please submit your video immediately or contact us if you're experiencing difficulties.</p>
            
            <p>Missing deadlines affects our content publishing schedule and impacts the entire team.</p>
            
            <p>Best regards,<br><strong>{self.admin_name}</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated notification from the Video Content Management System</p>
        </div>
    </div>
</body>
</html>
"""
        return subject, body
    
    def get_confirmation_template(self, team_name):
        """Email template for submission confirmation"""
        subject = f"✅ Video Submission Received - Thank You, {team_name}!"
        
        body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .success-icon {{ font-size: 64px; text-align: center; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Submission Received!</h1>
        </div>
        <div class="content">
            <div class="success-icon">🎉</div>
            
            <p>Hello <strong>{team_name}</strong>!</p>
            
            <p>Thank you for submitting your video on time! Your submission has been received and will be reviewed for publishing.</p>
            
            <p>We appreciate your timely contribution to our content calendar.</p>
            
            <p>Best regards,<br><strong>{self.admin_name}</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated notification from the Video Content Management System</p>
        </div>
    </div>
</body>
</html>
"""
        return subject, body
    
    def send_email(self, to_email, subject, html_body):
        """Send an email using SMTP"""
        if not self.email or not self.password:
            error = "Email credentials not configured. Please set SMTP_EMAIL and SMTP_PASSWORD."
            self.log_email(to_email, subject, "failed", error)
            return False, error
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.admin_name} <{self.email}>"
            msg["To"] = to_email
            
            # Create plain text version
            plain_text = f"This email requires HTML support. Subject: {subject}"
            
            part1 = MIMEText(plain_text, "plain")
            part2 = MIMEText(html_body, "html")
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.sendmail(self.email, to_email, msg.as_string())
            
            self.log_email(to_email, subject, "sent")
            return True, "Email sent successfully"
            
        except Exception as e:
            error = str(e)
            self.log_email(to_email, subject, "failed", error)
            return False, error
    
    def send_assignment_notification(self, team_name, team_email, deadline, deadline_day):
        """Send assignment notification to a team"""
        subject, body = self.get_assignment_template(team_name, deadline, deadline_day)
        return self.send_email(team_email, subject, body)
    
    def send_reminder(self, team_name, team_email, deadline, deadline_day, days_remaining):
        """Send reminder notification to a team"""
        subject, body = self.get_reminder_template(team_name, deadline, deadline_day, days_remaining)
        return self.send_email(team_email, subject, body)
    
    def send_overdue_notice(self, team_name, team_email, deadline, days_overdue):
        """Send overdue notification to a team"""
        subject, body = self.get_overdue_template(team_name, deadline, days_overdue)
        return self.send_email(team_email, subject, body)
    
    def get_submission_alert_template(self, team_name, submission_url, deadline):
        """Email template for social media tech alert"""
        subject = f"🚀 New Video Submission Ready - {team_name}"
        
        body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .submission-box {{ background: white; border-left: 4px solid #10b981; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .url-box {{ background: #e8f5e9; padding: 15px; border-radius: 5px; word-break: break-all; margin: 15px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 New Submission</h1>
        </div>
        <div class="content">
            <p>Hello Social Media Tech Team,</p>
            
            <p><strong>{team_name}</strong> has just submitted their video for the upcoming schedule.</p>
            
            <div class="submission-box">
                <p style="margin: 0; color: #666;">Scheduled Deadline:</p>
                <p style="font-size: 18px; font-weight: bold; margin: 5px 0;">{deadline}</p>
            </div>
            
            <p>Here is the Drive link for the video:</p>
            
            <div class="url-box">
                <a href="{submission_url}" style="color: #059669; font-weight: bold; text-decoration: none;">{submission_url}</a>
            </div>
            
            <p>Please review and upload as per the schedule.</p>
            
            <p>Best regards,<br><strong>{self.admin_name}</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated notification from the Video Content Management System</p>
        </div>
    </div>
</body>
</html>
"""
        return subject, body

    def send_confirmation(self, team_name, team_email):
        """Send submission confirmation to a team"""
        subject, body = self.get_confirmation_template(team_name)
        return self.send_email(team_email, subject, body)
    
    def send_submission_alert(self, team_name, submission_url, deadline):
        """Send alert to social media tech"""
        if not self.social_media_tech_email:
            return False, "Social Media Tech email not configured"
            
        subject, body = self.get_submission_alert_template(team_name, submission_url, deadline)
        return self.send_email(self.social_media_tech_email, subject, body)


def process_scheduled_notifications():
    """Process and send all scheduled notifications based on current date"""
    from scheduler import load_schedule, save_schedule
    
    notifier = EmailNotifier()
    schedule_data = load_schedule()
    schedule = schedule_data.get("schedule", [])
    
    now = datetime.now()
    results = []
    
    for entry in schedule:
        if entry["status"] != "pending":
            continue
        
        deadline = datetime.strptime(entry["deadline"], "%Y-%m-%d %H:%M")
        days_until = (deadline - now).days
        
        team_name = entry["team_name"]
        team_email = entry["team_email"]
        deadline_str = deadline.strftime("%B %d, %Y")
        deadline_day = entry["deadline_day"]
        
        # Check which notifications to send
        if days_until == 7 and not entry["reminders_sent"]["7_day"]:
            success, msg = notifier.send_assignment_notification(team_name, team_email, deadline_str, deadline_day)
            entry["reminders_sent"]["7_day"] = True
            results.append({"team": team_name, "type": "7_day", "success": success, "message": msg})
        
        elif days_until == 3 and not entry["reminders_sent"]["3_day"]:
            success, msg = notifier.send_reminder(team_name, team_email, deadline_str, deadline_day, 3)
            entry["reminders_sent"]["3_day"] = True
            results.append({"team": team_name, "type": "3_day", "success": success, "message": msg})
        
        elif days_until == 1 and not entry["reminders_sent"]["1_day"]:
            success, msg = notifier.send_reminder(team_name, team_email, deadline_str, deadline_day, 1)
            entry["reminders_sent"]["1_day"] = True
            results.append({"team": team_name, "type": "1_day", "success": success, "message": msg})
        
        elif days_until == 0 and not entry["reminders_sent"]["due_day"]:
            success, msg = notifier.send_reminder(team_name, team_email, deadline_str, deadline_day, 0)
            entry["reminders_sent"]["due_day"] = True
            results.append({"team": team_name, "type": "due_day", "success": success, "message": msg})
        
        elif days_until < 0 and not entry["reminders_sent"]["overdue"]:
            days_overdue = abs(days_until)
            success, msg = notifier.send_overdue_notice(team_name, team_email, deadline_str, days_overdue)
            entry["reminders_sent"]["overdue"] = True
            entry["status"] = "overdue"
            results.append({"team": team_name, "type": "overdue", "success": success, "message": msg})
    
    # Save updated schedule
    save_schedule(schedule_data)
    
    return results


if __name__ == "__main__":
    # Test email templates
    notifier = EmailNotifier()
    subject, body = notifier.get_assignment_template("Team Alpha", "January 25, 2026", "Friday")
    print(f"Subject: {subject}")
    print("Template generated successfully!")

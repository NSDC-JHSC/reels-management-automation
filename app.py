"""
Video Content Management System - Main Flask Application
Complete dashboard for managing video submissions from 8 teams
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_apscheduler import APScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from scheduler import (
    generate_schedule, load_schedule, save_schedule, load_teams,
    get_upcoming_deadlines, get_overdue_submissions, mark_submitted,
    get_team_stats, get_calendar_data
)
from notifications import EmailNotifier, process_scheduled_notifications

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "video-content-manager-secret-key-2026")

# Initialize scheduler for automated tasks
scheduler = APScheduler()

DATA_DIR = Path(__file__).parent / "data"


# ============================================
# SCHEDULED JOBS
# ============================================

@scheduler.task('cron', id='daily_notifications', hour=9, minute=0)
def scheduled_notification_check():
    """Run daily at 9 AM to send scheduled notifications"""
    with app.app_context():
        results = process_scheduled_notifications()
        print(f"[{datetime.now()}] Processed {len(results)} notifications")


# ============================================
# MAIN ROUTES
# ============================================

@app.route('/')
def dashboard():
    """Main dashboard view"""
    schedule_data = load_schedule()
    teams = load_teams()
    
    # Get upcoming deadlines (next 7 days)
    upcoming = get_upcoming_deadlines(days=7)
    
    # Get overdue submissions
    overdue = get_overdue_submissions()
    
    # Get team statistics
    team_stats = get_team_stats()
    
    # Get schedule summary
    schedule = schedule_data.get("schedule", [])
    total_scheduled = len(schedule)
    total_submitted = sum(1 for s in schedule if s["status"] == "submitted")
    total_pending = sum(1 for s in schedule if s["status"] == "pending")
    total_overdue = len(overdue)
    
    return render_template('dashboard.html',
        teams=teams,
        upcoming=upcoming,
        overdue=overdue,
        team_stats=team_stats,
        total_scheduled=total_scheduled,
        total_submitted=total_submitted,
        total_pending=total_pending,
        total_overdue=total_overdue,
        schedule_generated=schedule_data.get("last_generated"),
        current_date=datetime.now().strftime("%B %d, %Y")
    )


@app.route('/calendar')
def calendar_view():
    """Calendar view of schedule"""
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    # Get calendar events
    events = get_calendar_data(year, month)
    
    # Generate calendar structure
    import calendar
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    month_days = cal.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Previous and next month navigation
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    return render_template('calendar.html',
        events=events,
        month_days=month_days,
        month_name=month_name,
        year=year,
        month=month,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        today=datetime.now().day if datetime.now().month == month and datetime.now().year == year else None
    )


@app.route('/teams')
def teams_view():
    """Team management view"""
    teams = load_teams()
    team_stats = get_team_stats()
    
    # Merge stats with team data
    for team in teams:
        if team["id"] in team_stats:
            team["stats"] = team_stats[team["id"]]
        else:
            team["stats"] = {"total_assigned": 0, "submitted": 0, "pending": 0, "overdue": 0, "on_time_rate": 0}
    
    return render_template('teams.html', teams=teams)


@app.route('/schedule')
def schedule_view():
    """Full schedule view"""
    schedule_data = load_schedule()
    schedule = schedule_data.get("schedule", [])
    
    # Group by week
    weeks = {}
    for entry in schedule:
        week_num = entry["week"]
        if week_num not in weeks:
            weeks[week_num] = []
        weeks[week_num].append(entry)
    
    return render_template('schedule.html',
        weeks=weeks,
        schedule_info=schedule_data,
        total_entries=len(schedule)
    )


@app.route('/notifications')
def notifications_view():
    """Notification history and management"""
    try:
        with open(DATA_DIR / "notifications.json", "r") as f:
            notification_data = json.load(f)
    except:
        notification_data = {"notifications": [], "email_log": []}
    
    email_log = notification_data.get("email_log", [])[-50:]  # Last 50 emails
    email_log.reverse()  # Most recent first
    
    return render_template('notifications.html', email_log=email_log)


# ============================================
# API ROUTES
# ============================================

@app.route('/api/generate-schedule', methods=['POST'])
def api_generate_schedule():
    """Generate a new schedule"""
    weeks = request.json.get('weeks', 12)
    start_date = request.json.get('start_date')
    
    try:
        schedule_data = generate_schedule(weeks=weeks, start_date=start_date)
        return jsonify({
            "success": True,
            "message": f"Generated schedule for {weeks} weeks",
            "entries": len(schedule_data["schedule"])
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/mark-submitted/<int:schedule_id>', methods=['POST'])
def api_mark_submitted(schedule_id):
    """Mark a submission as received"""
    submission_url = request.json.get('submission_url', '')
    
    try:
        mark_submitted(schedule_id, submission_url)
        
        # Send confirmation email
        schedule_data = load_schedule()
        for entry in schedule_data["schedule"]:
            if entry["id"] == schedule_id:
                notifier = EmailNotifier()
                
                # 1. Send confirmation to the team
                notifier.send_confirmation(entry["team_name"], entry["team_email"])
                
                # 2. Send alert to Social Media Tech (if URL is provided)
                if submission_url:
                    notifier.send_submission_alert(
                        entry["team_name"], 
                        submission_url,
                        entry["deadline"]
                    )
                break
        
        return jsonify({"success": True, "message": "Submission marked as received"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/send-reminder/<int:schedule_id>', methods=['POST'])
def api_send_reminder(schedule_id):
    """Manually send a reminder for a specific entry"""
    schedule_data = load_schedule()
    
    for entry in schedule_data["schedule"]:
        if entry["id"] == schedule_id:
            notifier = EmailNotifier()
            deadline = datetime.strptime(entry["deadline"], "%Y-%m-%d %H:%M")
            days_until = (deadline - datetime.now()).days
            
            if days_until < 0:
                success, msg = notifier.send_overdue_notice(
                    entry["team_name"],
                    entry["team_email"],
                    deadline.strftime("%B %d, %Y"),
                    abs(days_until)
                )
            else:
                success, msg = notifier.send_reminder(
                    entry["team_name"],
                    entry["team_email"],
                    deadline.strftime("%B %d, %Y"),
                    entry["deadline_day"],
                    days_until
                )
            
            return jsonify({"success": success, "message": msg})
    
    return jsonify({"success": False, "error": "Schedule entry not found"}), 404


@app.route('/api/update-team/<int:team_id>', methods=['POST'])
def api_update_team(team_id):
    """Update team information"""
    try:
        with open(DATA_DIR / "teams.json", "r") as f:
            teams_data = json.load(f)
        
        for team in teams_data["teams"]:
            if team["id"] == team_id:
                team["name"] = request.json.get("name", team["name"])
                team["email"] = request.json.get("email", team["email"])
                team["contact_person"] = request.json.get("contact_person", team["contact_person"])
                break
        
        with open(DATA_DIR / "teams.json", "w") as f:
            json.dump(teams_data, f, indent=4)
        
        return jsonify({"success": True, "message": "Team updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/process-notifications', methods=['POST'])
def api_process_notifications():
    """Manually trigger notification processing"""
    try:
        results = process_scheduled_notifications()
        return jsonify({
            "success": True,
            "message": f"Processed {len(results)} notifications",
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/test-email', methods=['POST'])
def api_test_email():
    """Send a test email to verify configuration"""
    to_email = request.json.get('email')
    
    if not to_email:
        return jsonify({"success": False, "error": "Email address required"}), 400
    
    notifier = EmailNotifier()
    subject = "🧪 Test Email - Video Content Management System"
    body = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1 style="color: #667eea;">✅ Email Configuration Working!</h1>
        <p>This is a test email from your Video Content Management System.</p>
        <p>If you received this, your email notifications are properly configured.</p>
    </body>
    </html>
    """
    
    success, msg = notifier.send_email(to_email, subject, body)
    return jsonify({"success": success, "message": msg})


@app.route('/api/stats')
def api_stats():
    """Get dashboard statistics"""
    schedule_data = load_schedule()
    schedule = schedule_data.get("schedule", [])
    team_stats = get_team_stats()
    
    return jsonify({
        "total_scheduled": len(schedule),
        "total_submitted": sum(1 for s in schedule if s["status"] == "submitted"),
        "total_pending": sum(1 for s in schedule if s["status"] == "pending"),
        "total_overdue": len(get_overdue_submissions()),
        "team_stats": team_stats
    })


# ============================================
# TEMPLATE FILTERS
# ============================================

@app.template_filter('datetime')
def format_datetime(value, format='%B %d, %Y %I:%M %p'):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M")
        except:
            try:
                value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except:
                return value
    return value.strftime(format)


@app.template_filter('date')
def format_date(value, format='%B %d, %Y'):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M")
        except:
            try:
                value = datetime.strptime(value, "%Y-%m-%d")
            except:
                return value
    return value.strftime(format)


# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    # Initialize scheduler
    scheduler.init_app(app)
    scheduler.start()
    
    # Check if schedule exists, if not generate one
    schedule_data = load_schedule()
    if not schedule_data.get("schedule"):
        print("No schedule found. Generating initial 12-week schedule...")
        generate_schedule(weeks=12)
        print("Schedule generated!")
    
    print("\n" + "="*50)
    print("🎬 Video Content Management System")
    print("="*50)
    print("➡️  Dashboard: http://127.0.0.1:5000")
    print("➡️  Calendar:  http://127.0.0.1:5000/calendar")
    print("➡️  Teams:     http://127.0.0.1:5000/teams")
    print("➡️  Schedule:  http://127.0.0.1:5000/schedule")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

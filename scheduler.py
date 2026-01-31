"""
Video Content Management System - Scheduler Module
Handles fair rotation scheduling for 8 teams with 3 videos per week
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def load_teams():
    """Load teams from JSON file"""
    with open(DATA_DIR / "teams.json", "r") as f:
        return json.load(f)["teams"]


def load_schedule():
    """Load existing schedule from JSON file"""
    with open(DATA_DIR / "schedule.json", "r") as f:
        return json.load(f)


def save_schedule(schedule_data):
    """Save schedule to JSON file"""
    with open(DATA_DIR / "schedule.json", "w") as f:
        json.dump(schedule_data, f, indent=4, default=str)


def get_next_monday(from_date=None):
    """Get the next Monday from a given date"""
    if from_date is None:
        from_date = datetime.now()
    days_ahead = 0 - from_date.weekday()  # Monday is 0
    if days_ahead <= 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def generate_schedule(weeks=12, start_date=None):
    """
    Generate a fair rotation schedule for all teams
    
    Algorithm:
    - 8 teams, 3 slots per week (Monday, Wednesday, Friday)
    - Each team gets approximately equal opportunities
    - Rotation ensures no team is consecutively scheduled
    
    Returns schedule with staggered deadlines
    """
    teams = load_teams()
    num_teams = len(teams)
    
    if start_date is None:
        start_date = get_next_monday()
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    # Days for video submissions: Monday (0), Wednesday (2), Friday (4)
    submission_days = [0, 2, 4]  # Monday, Wednesday, Friday
    
    schedule = []
    team_index = 0
    
    for week in range(weeks):
        week_start = start_date + timedelta(weeks=week)
        
        for day_offset in submission_days:
            submission_date = week_start + timedelta(days=day_offset)
            
            # Deadline is 6 PM on submission day
            deadline = submission_date.replace(hour=18, minute=0, second=0)
            
            # Assignment notification (7 days before)
            notify_date = deadline - timedelta(days=7)
            
            # Get current team in rotation
            current_team = teams[team_index % num_teams]
            
            schedule_entry = {
                "id": len(schedule) + 1,
                "week": week + 1,
                "team_id": current_team["id"],
                "team_name": current_team["name"],
                "team_email": current_team["email"],
                "team_color": current_team["color"],
                "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
                "deadline_day": deadline.strftime("%A"),
                "notify_date": notify_date.strftime("%Y-%m-%d"),
                "status": "pending",  # pending, submitted, overdue
                "submission_url": None,
                "submitted_at": None,
                "reminders_sent": {
                    "7_day": False,
                    "3_day": False,
                    "1_day": False,
                    "due_day": False,
                    "overdue": False
                }
            }
            
            schedule.append(schedule_entry)
            team_index += 1
    
    # Save the generated schedule
    schedule_data = {
        "schedule": schedule,
        "last_generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "weeks_generated": weeks,
        "start_date": start_date.strftime("%Y-%m-%d")
    }
    
    save_schedule(schedule_data)
    
    return schedule_data


def get_upcoming_deadlines(days=7):
    """Get all deadlines within the next N days"""
    schedule_data = load_schedule()
    schedule = schedule_data.get("schedule", [])
    
    today = datetime.now()
    cutoff = today + timedelta(days=days)
    
    upcoming = []
    for entry in schedule:
        deadline = datetime.strptime(entry["deadline"], "%Y-%m-%d %H:%M")
        if today <= deadline <= cutoff and entry["status"] == "pending":
            entry["days_until"] = (deadline - today).days
            upcoming.append(entry)
    
    return sorted(upcoming, key=lambda x: x["deadline"])


def get_overdue_submissions():
    """Get all overdue submissions"""
    schedule_data = load_schedule()
    schedule = schedule_data.get("schedule", [])
    
    now = datetime.now()
    overdue = []
    
    for entry in schedule:
        deadline = datetime.strptime(entry["deadline"], "%Y-%m-%d %H:%M")
        if deadline < now and entry["status"] == "pending":
            entry["days_overdue"] = (now - deadline).days
            overdue.append(entry)
    
    return overdue


def mark_submitted(schedule_id, submission_url=None):
    """Mark a schedule entry as submitted"""
    schedule_data = load_schedule()
    
    for entry in schedule_data["schedule"]:
        if entry["id"] == schedule_id:
            entry["status"] = "submitted"
            entry["submitted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry["submission_url"] = submission_url
            break
    
    save_schedule(schedule_data)
    return True


def get_team_stats():
    """Get submission statistics for each team"""
    schedule_data = load_schedule()
    schedule = schedule_data.get("schedule", [])
    teams = load_teams()
    
    stats = {}
    for team in teams:
        stats[team["id"]] = {
            "team_name": team["name"],
            "team_color": team["color"],
            "total_assigned": 0,
            "submitted": 0,
            "pending": 0,
            "overdue": 0,
            "on_time_rate": 0
        }
    
    now = datetime.now()
    
    for entry in schedule:
        team_id = entry["team_id"]
        if team_id in stats:
            stats[team_id]["total_assigned"] += 1
            
            if entry["status"] == "submitted":
                stats[team_id]["submitted"] += 1
            elif entry["status"] == "pending":
                deadline = datetime.strptime(entry["deadline"], "%Y-%m-%d %H:%M")
                if deadline < now:
                    stats[team_id]["overdue"] += 1
                else:
                    stats[team_id]["pending"] += 1
    
    # Calculate on-time rates
    for team_id in stats:
        total = stats[team_id]["total_assigned"]
        if total > 0:
            submitted = stats[team_id]["submitted"]
            stats[team_id]["on_time_rate"] = round((submitted / total) * 100, 1)
    
    return stats


def get_calendar_data(year=None, month=None):
    """Get schedule data formatted for calendar view"""
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    schedule_data = load_schedule()
    schedule = schedule_data.get("schedule", [])
    
    calendar_events = []
    for entry in schedule:
        deadline = datetime.strptime(entry["deadline"], "%Y-%m-%d %H:%M")
        if deadline.year == year and deadline.month == month:
            calendar_events.append({
                "id": entry["id"],
                "title": entry["team_name"],
                "date": deadline.strftime("%Y-%m-%d"),
                "time": deadline.strftime("%H:%M"),
                "color": entry["team_color"],
                "status": entry["status"],
                "day": deadline.day
            })
    
    return calendar_events


if __name__ == "__main__":
    # Test schedule generation
    print("Generating 12-week schedule...")
    schedule = generate_schedule(weeks=12)
    print(f"Generated {len(schedule['schedule'])} entries")
    print(f"Start date: {schedule['start_date']}")
    print("\nFirst 6 entries:")
    for entry in schedule['schedule'][:6]:
        print(f"  Week {entry['week']}: {entry['team_name']} - {entry['deadline']} ({entry['deadline_day']})")

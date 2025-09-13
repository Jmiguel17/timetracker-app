import sys
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from src import database as db
from pathlib import Path
from datetime import date, datetime, timedelta
import csv
import io

app = FastAPI(title="Time Tracker API")

# Base directory
BASE_DIR = Path(__file__).resolve().parent

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main HTML page."""
    html_file_path = BASE_DIR.parent / "templates" / "index.html"
    try:
        with open(html_file_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)

@app.get("/api/data")
async def get_all_data():
    """Provides all tracking data in a single JSON response."""
    conn = db.get_db_connection()
    
    projects = conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY start_time DESC").fetchall()
    # Limit activities for performance in the initial dashboard
    activities = conn.execute("SELECT * FROM activities ORDER BY start_time DESC LIMIT 100").fetchall()
    
    conn.close()
    
    # Convert sqlite3.Row objects to dicts for JSON serialization
    return {
        "projects": [dict(p) for p in projects],
        "tasks": [dict(t) for t in tasks],
        "activities": [dict(a) for a in activities]
    }

@app.get("/api/activities_by_date")
async def get_activities_by_date(selected_date: date = Query(default=date.today())):
    """Provides all activities for a specific date, ordered chronologically."""
    conn = db.get_db_connection()
    
    # Fetch activities for the selected date
    # SQLite stores dates as TEXT, so we compare string representations
    date_str = selected_date.isoformat() + "%"
    activities = conn.execute(
        "SELECT * FROM activities WHERE start_time LIKE ? ORDER BY start_time ASC", 
        (date_str,)
    ).fetchall()

    # Also fetch related projects and tasks for context
    projects = conn.execute("SELECT * FROM projects").fetchall()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    
    conn.close()

    return {
        "activities": [dict(a) for a in activities],
        "projects": [dict(p) for p in projects],
        "tasks": [dict(t) for t in tasks]
    }

def calculate_duration(start_time_str, end_time_str):
    """Calculates the duration in seconds between two ISO formatted time strings."""
    start_time = datetime.fromisoformat(start_time_str)
    end_time = datetime.fromisoformat(end_time_str) if end_time_str else datetime.now()
    return (end_time - start_time).total_seconds()

@app.get("/api/summary/daily")
async def get_daily_summary(selected_date: date = Query(default=date.today())):
    """Provides a daily summary of time spent per project and task."""
    conn = db.get_db_connection()
    
    date_str = selected_date.isoformat() + "%"
    query = """
        SELECT
            p.name AS project_name,
            t.name AS task_name,
            a.start_time,
            a.end_time
        FROM activities a
        JOIN tasks t ON a.task_id = t.id
        JOIN projects p ON t.project_id = p.id
        WHERE a.start_time LIKE ?
        ORDER BY a.start_time ASC
    """
    activities = conn.execute(query, (date_str,)).fetchall()
    conn.close()

    summary = {}
    for activity in activities:
        duration = calculate_duration(activity['start_time'], activity['end_time'])
        project_name = activity['project_name']
        task_name = activity['task_name']

        if project_name not in summary:
            summary[project_name] = {'total_duration': 0, 'tasks': {}}
        
        summary[project_name]['total_duration'] += duration

        if task_name not in summary[project_name]['tasks']:
            summary[project_name]['tasks'][task_name] = 0
        summary[project_name]['tasks'][task_name] += duration

    return summary

@app.get("/api/summary/weekly")
async def get_weekly_summary(selected_date: date = Query(default=date.today())):
    """Provides a weekly summary of time spent per project and task."""
    conn = db.get_db_connection()
    
    # Calculate the start and end of the week (Monday to Sunday)
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    query = """
        SELECT
            p.name AS project_name,
            t.name AS task_name,
            a.start_time,
            a.end_time
        FROM activities a
        JOIN tasks t ON a.task_id = t.id
        JOIN projects p ON t.project_id = p.id
        WHERE substr(a.start_time, 1, 10) BETWEEN ? AND ?
        ORDER BY a.start_time ASC
    """
    activities = conn.execute(query, (start_of_week.isoformat(), end_of_week.isoformat())).fetchall()
    conn.close()

    summary = {}
    for activity in activities:
        duration = calculate_duration(activity['start_time'], activity['end_time'])
        project_name = activity['project_name']
        task_name = activity['task_name']

        if project_name not in summary:
            summary[project_name] = {'total_duration': 0, 'tasks': {}}
        
        summary[project_name]['total_duration'] += duration

        if task_name not in summary[project_name]['tasks']:
            summary[project_name]['tasks'][task_name] = 0
        summary[project_name]['tasks'][task_name] += duration

    return summary

@app.get("/api/summary/monthly")
async def get_monthly_summary(selected_date: date = Query(default=date.today())):
    """Provides a monthly summary of time spent per project and task."""
    conn = db.get_db_connection()
    
    # Calculate the start and end of the month
    start_of_month = selected_date.replace(day=1)
    # Get the last day of the month
    if selected_date.month == 12:
        end_of_month = selected_date.replace(year=selected_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = selected_date.replace(month=selected_date.month + 1, day=1) - timedelta(days=1)

    query = """
        SELECT
            p.name AS project_name,
            t.name AS task_name,
            a.start_time,
            a.end_time
        FROM activities a
        JOIN tasks t ON a.task_id = t.id
        JOIN projects p ON t.project_id = p.id
        WHERE substr(a.start_time, 1, 10) BETWEEN ? AND ?
        ORDER BY a.start_time ASC
    """
    activities = conn.execute(query, (start_of_month.isoformat(), end_of_month.isoformat())).fetchall()
    conn.close()

    summary = {}
    for activity in activities:
        duration = calculate_duration(activity['start_time'], activity['end_time'])
        project_name = activity['project_name']
        task_name = activity['task_name']

        if project_name not in summary:
            summary[project_name] = {'total_duration': 0, 'tasks': {}}
        
        summary[project_name]['total_duration'] += duration

        if task_name not in summary[project_name]['tasks']:
            summary[project_name]['tasks'][task_name] = 0
        summary[project_name]['tasks'][task_name] += duration

    return summary

async def get_summary_data(summary_type: str, selected_date: date):
    if summary_type == "daily":
        return await get_daily_summary(selected_date)
    elif summary_type == "weekly":
        return await get_weekly_summary(selected_date)
    elif summary_type == "monthly":
        return await get_monthly_summary(selected_date)
    else:
        raise HTTPException(status_code=400, detail="Invalid summary_type. Must be 'daily', 'weekly', or 'monthly'.")

@app.get("/api/reports/summary")
async def export_summary_report(
    summary_type: str = Query(..., description="Type of summary: 'daily', 'weekly', or 'monthly'"),
    selected_date: date = Query(default=date.today(), description="Date for the summary"),
    format: str = Query("json", description="Output format: 'json' or 'csv'")
):
    """Exports summary data in JSON or CSV format."""
    summary_data = await get_summary_data(summary_type, selected_date)

    if format == "json":
        return JSONResponse(content=summary_data)
    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([f"Project ({summary_type.capitalize()} Summary)", "Task", "Hours"])

        # Write data
        for project_name, project_info in summary_data.items():
            total_project_hours = project_info['total_duration'] / 3600
            writer.writerow([project_name, "", f"{total_project_hours:.2f}"])
            for task_name, task_duration in project_info['tasks'].items():
                task_hours = task_duration / 3600
                writer.writerow(["", task_name, f"{task_hours:.2f}"])
        
        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={summary_type}_summary_{selected_date.isoformat()}.csv"
        return response
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Must be 'json' or 'csv'.")

if __name__ == "__main__":
    import uvicorn
    print("Starting web server...")
    print("View the dashboard at http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
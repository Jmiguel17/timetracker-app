import sqlite3
from contextlib import closing
import os
from datetime import datetime

# Define the path for the database in the project root
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "timetracker.db")

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(overwrite=False):
    """Creates the database tables. If overwrite is True, existing tables are dropped."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()

        if overwrite:
            cursor.execute("DROP TABLE IF EXISTS activities")
            cursor.execute("DROP TABLE IF EXISTS tasks")
            cursor.execute("DROP TABLE IF EXISTS rules")
            cursor.execute("DROP TABLE IF EXISTS projects")

        # Projects table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """)

        # Tasks table (new)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        """)

        # Activities table (modified)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            app_name TEXT NOT NULL,
            window_title TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
        """)

        # Rules table (new)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT NOT NULL,
            project_id INTEGER NOT NULL,
            task_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
        """)

        conn.commit()

def reset_database():
    """Removes the database file and recreates tables."""
    print("Re-initializing database with new schema...")
    try:
        os.remove(DB_FILE)
        print("Removed old database file.")
    except OSError:
        pass # File didn't exist
    create_tables(overwrite=True)
    print("Database and tables created successfully.")

# --- Helper Functions ---

def get_projects():
    """Retrieves all projects."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY name")
        return cursor.fetchall()

def get_or_create_project(name):
    """Gets a project by name, creating it if it doesn't exist."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM projects WHERE name = ?", (name,))
        project = cursor.fetchone()
        if project:
            return project['id']
        else:
            cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid

def get_active_tasks_for_project(project_id):
    """Gets all tasks for a project that have not ended."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE project_id = ? AND end_time IS NULL ORDER BY start_time DESC", (project_id,))
        return cursor.fetchall()

def create_task(project_id, name):
    """Creates a new task and returns its ID."""
    now_iso = datetime.now().isoformat()
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (project_id, name, start_time) VALUES (?, ?, ?)",
            (project_id, name, now_iso)
        )
        conn.commit()
        return cursor.lastrowid

def end_task(task_id):
    """Sets the end time for a specific task."""
    now_iso = datetime.now().isoformat()
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET end_time = ? WHERE id = ?", (now_iso, task_id))
        conn.commit()

def add_activity(task_id, app_name, window_title, start_time, end_time):
    """Adds a raw activity record linked to a task."""
    print(f"Activity logged: App='{app_name}', Window='{window_title}' for Task ID {task_id}")
    if not app_name or not app_name.strip():
        return
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activities (task_id, app_name, window_title, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
            (task_id, app_name, window_title, start_time.isoformat(), end_time.isoformat())
        )
        conn.commit()

def add_rule(pattern, project_id, task_id=None):
    """Adds a new rule to automatically categorize activities."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rules (pattern, project_id, task_id) VALUES (?, ?, ?)",
            (pattern, project_id, task_id)
        )
        conn.commit()
        return cursor.lastrowid

def get_project_name_by_id(project_id):
    """Retrieves the name of a project by its ID."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        result = cursor.fetchone()
        return result['name'] if result else "Unknown Project"

def get_task_name_by_id(task_id):
    """Retrieves the name of a task by its ID."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        return result['name'] if result else "Unknown Task"

def get_rules():
    """Retrieves all defined rules."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT r.id, r.pattern, r.project_id, p.name as project_name, r.task_id, t.name as task_name FROM rules r JOIN projects p ON r.project_id = p.id LEFT JOIN tasks t ON r.task_id = t.id")
        return cursor.fetchall()

if __name__ == "__main__":
    reset_database()

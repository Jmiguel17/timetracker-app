import time
import pygetwindow as gw
from pynput import mouse, keyboard
from datetime import datetime
import threading
import os
import database as db

# --- Configuration ---
TEST_MODE = False # Temporary flag for automated testing
AFK_TIMEOUT = 60  # seconds
TICK_INTERVAL = 5  # seconds
CHECKIN_INTERVAL = 1800 # seconds (30 minutes)

# --- Global State ---
last_input_time = time.time()
last_checkin_time = time.time()
is_afk = False
prompt_needed = threading.Event()
tracking_active = threading.Event() # Use an Event for cleaner signaling
menu_prompt_requested = threading.Event() # New: Event to signal menu prompt

current_project_id = None
current_task_id = None
current_activity = None
test_project_call_count = 0 # For TEST_MODE
test_task_call_count = 0 # For TEST_MODE

# --- User Interaction ---
def prompt_for_project():
    """Lists projects and asks the user to select or create one."""
    global test_project_call_count
    if TEST_MODE:
        test_project_call_count += 1
        if test_project_call_count == 1:
            return db.get_or_create_project("Test Project 1")
        elif test_project_call_count == 2:
            return db.get_or_create_project("Test Project 2")
        else:
            return db.get_or_create_project("Test Project Default") # Fallback for more calls

    while True:
        print("\n--- Projects ---")
        projects = db.get_projects()
        
        if not projects:
            print("No projects found. Please type a new project name:")
            choice = input("> ")
            return db.get_or_create_project(choice)
        else:
            for i, project in enumerate(projects):
                print(f"{i + 1}. {project['name']}")
            
            print("\nEnter project number to select, or type a new project name:")
            choice = input("> ")
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(projects):
                    return projects[choice_num - 1]['id']
                else:
                    print("Invalid number. Please try again.")
            except ValueError:
                # If it's not a number, treat it as a new project name
                return db.get_or_create_project(choice)

def manage_tasks(project_id):
    """Handles the task management menu for completing and reopening tasks."""
    while True:
        project_name = db.get_project_name_by_id(project_id)
        print(f"\n--- Manage Tasks for '{project_name}' ---")
        print("1. Complete an active task")
        print("2. Reopen a completed task")
        print("3. Back to task selection")
        choice = input("> ")

        if choice == '1':
            tasks = db.get_active_tasks_for_project(project_id)
            if not tasks:
                print("No active tasks to complete.")
                continue
            print("\nSelect a task to complete:")
            for i, task in enumerate(tasks):
                print(f"{i + 1}. {task['name']}")
            task_choice = input("> ")
            try:
                task_to_complete = tasks[int(task_choice) - 1]
                db.complete_task(task_to_complete['id'])
                print(f"Task '{task_to_complete['name']}' marked as completed.")
            except (ValueError, IndexError):
                print("Invalid selection.")
        
        elif choice == '2':
            tasks = db.get_completed_tasks_for_project(project_id)
            if not tasks:
                print("No completed tasks to reopen.")
                continue
            print("\nSelect a task to reopen:")
            for i, task in enumerate(tasks):
                print(f"{i + 1}. {task['name']}")
            task_choice = input("> ")
            try:
                task_to_reopen = tasks[int(task_choice) - 1]
                db.reopen_task(task_to_reopen['id'])
                print(f"Task '{task_to_reopen['name']}' has been reopened.")
            except (ValueError, IndexError):
                print("Invalid selection.")

        elif choice == '3':
            return None # Go back to the previous menu
        else:
            print("Invalid choice.")

def prompt_for_task(project_id):
    """Asks the user to select or create a task for the given project."""
    global test_task_call_count
    if TEST_MODE:
        test_task_call_count += 1
        if test_task_call_count == 1:
            return db.create_task(project_id, "Test Task 1")
        elif test_task_call_count == 2:
            return db.create_task(project_id, "Test Task 2")
        else:
            return db.create_task(project_id, "Test Task Default") # Fallback for more calls

    while True:
        print("\n--- Active Tasks for this Project ---")
        tasks = db.get_active_tasks_for_project(project_id)
        if not tasks:
            print("No active tasks.")
        else:
            for i, task in enumerate(tasks):
                print(f"{i + 1}. {task['name']}")
        
        print("\nEnter task number to select, type a new task name, or 'm' to manage tasks:")
        choice = input("> ")

        if choice.lower() == 'm':
            manage_tasks(project_id)
            continue # After managing tasks, show the task list again

        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(tasks):
                return tasks[choice_num - 1]['id']
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            if choice.strip(): # Ensure it's not an empty string
                return db.create_task(project_id, choice)
            else:
                print("Invalid input.")

def handle_user_prompt(reason):
    """Guides the user through selecting their current work."""
    global current_project_id, current_task_id, current_activity
    print(f"\n🔔 {reason} Let's log your work.")

    new_project_id = current_project_id
    new_task_id = current_task_id

    while True:
        if new_project_id and new_task_id:
            project_name = db.get_project_name_by_id(new_project_id)
            task_name = db.get_task_name_by_id(new_task_id)
            print(f"Currently tracking Project: {project_name}, Task: {task_name}")
            print("1. Continue with current project/task")
            print("2. Change Project")
            print("3. Change Task")
            choice = input("> ")

            if choice == '1':
                break
            elif choice == '2':
                new_project_id = prompt_for_project()
                new_task_id = prompt_for_task(new_project_id)
                break
            elif choice == '3':
                new_task_id = prompt_for_task(new_project_id)
                break
            else:
                print("Invalid choice. Please try again.")
        else:
            new_project_id = prompt_for_project()
            new_task_id = prompt_for_task(new_project_id)
            break

    # Log current activity if the task or project has changed
    if (new_task_id != current_task_id or new_project_id != current_project_id):
        if current_activity:
            db.add_activity(
                current_task_id,
                current_activity['app_name'],
                current_activity['window_title'],
                current_activity['start_time'],
                datetime.now()
            )
            current_activity = None # Reset activity

    current_project_id = new_project_id
    current_task_id = new_task_id
    project_name = db.get_project_name_by_id(current_project_id)
    task_name = db.get_task_name_by_id(current_task_id)
    print(f"✅ Great! Now tracking for Project: {project_name}, Task: {task_name}.")

# --- Rule Management ---
def manage_rules():
    """Allows the user to view and add rules for automatic categorization."""
    while True:
        print("\n--- Rule Management ---")
        print("1. View existing rules")
        print("2. Add a new rule")
        print("3. Back to main menu")
        choice = input("> ")

        if choice == '1':
            rules = db.get_rules()
            if not rules:
                print("No rules defined.")
            else:
                for rule in rules:
                    task_info = f", Task: {rule['task_name']}" if rule['task_name'] else ""
                    print(f"ID: {rule['id']}, Pattern: '{rule['pattern']}', Project: {rule['project_name']}{task_info}")
        elif choice == '2':
            pattern = input("Enter pattern (e.g., 'VS Code'): ")
            
            print("Select a project for this rule:")
            projects = db.get_projects()
            for i, project in enumerate(projects):
                print(f"{i + 1}. {project['name']}")
            project_choice = input("> ")
            try:
                project_id = projects[int(project_choice) - 1]['id']
            except (ValueError, IndexError):
                print("Invalid project choice.")
                continue

            task_id = None
            task_choice = input("Assign to a specific task? (Enter task number or leave blank for project only): ")
            if task_choice:
                tasks = db.get_active_tasks_for_project(project_id)
                for i, task in enumerate(tasks):
                    print(f"{i + 1}. {task['name']}")
                try:
                    task_id = tasks[int(task_choice) - 1]['id']
                except (ValueError, IndexError):
                    print("Invalid task choice. Rule will be project-only.")
            
            db.add_rule(pattern, project_id, task_id)
            print("Rule added successfully!")
        elif choice == '3':
            break
        else:
            print("Invalid choice.")

# --- Input Monitoring ---
def on_input_event():
    """Callback for any mouse/keyboard activity."""
    global last_input_time, is_afk
    last_input_time = time.time()
    if is_afk:
        print("\nUser is back.")
        is_afk = False
        prompt_needed.set() # Signal that a prompt is needed

def on_press_key(key):
    """Callback for keyboard press events."""
    on_input_event() # Call the general input event to reset AFK timer
    try:
        if key == keyboard.Key.f1:
            print("\nF1 pressed. Requesting menu prompt...")
            menu_prompt_requested.set()
    except AttributeError:
        # Handle special keys or other non-char keys if necessary
        pass

def start_listeners():
    global mouse_listener, keyboard_listener
    mouse_listener = mouse.Listener(on_move=lambda x,y: on_input_event(), on_click=lambda x,y,b,p: on_input_event(), on_scroll=lambda x,y,dx,dy: on_input_event())
    keyboard_listener = keyboard.Listener(on_press=on_press_key)
    mouse_listener.start()
    keyboard_listener.start()
    print("Input listeners started.")


# --- Main Tracking Logic ---
def start_tracking():
    """The main loop to track window activity and handle prompts."""
    global is_afk, current_activity, last_checkin_time, current_project_id, current_task_id

    tracking_active.set() # Set the event to start tracking

    # Initial prompt on startup
    handle_user_prompt("Welcome!")
    last_checkin_time = time.time()

    while tracking_active.is_set():
        time.sleep(TICK_INTERVAL)

        if prompt_needed.is_set():
            handle_user_prompt("Welcome back!")
            last_checkin_time = time.time()
            prompt_needed.clear()

        if menu_prompt_requested.is_set():
            handle_user_prompt("Menu requested!")
            last_checkin_time = time.time()
            menu_prompt_requested.clear()

        # AFK Check
        if not is_afk and (time.time() - last_input_time) > AFK_TIMEOUT:
            print("\nUser is now AFK.")
            is_afk = True
            if current_activity:
                db.add_activity(
                    current_task_id,
                    current_activity['app_name'],
                    current_activity['window_title'],
                    current_activity['start_time'],
                    datetime.now()
                )
                current_activity = None
        
        if is_afk:
            continue

        # Periodic Check-in
        if (time.time() - last_checkin_time) > CHECKIN_INTERVAL:
            handle_user_prompt("Time for a check-in!")
            last_checkin_time = time.time()

        # Get active window
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                app_name = active_window.title()
                window_title = active_window.title()
            else:
                app_name, window_title = "No Active Window", ""
        except Exception:
            app_name, window_title = "No Active Window", ""

        # Apply rules for automatic categorization
        rules = db.get_rules()
        rule_applied = False
        for rule in rules:
            if rule['pattern'].lower() in window_title.lower():
                if current_project_id != rule['project_id'] or current_task_id != rule['task_id']:
                    task_info = f", Task: {rule['task_name']}" if rule['task_name'] else ""
                    print(f"\n✨ Rule matched: '{rule['pattern']}' -> Project: {rule['project_name']}{task_info}.")
                    current_project_id = rule['project_id']
                    current_task_id = rule['task_id']
                    prompt_needed.clear() # No need to prompt if rule applied
                rule_applied = True
                break
        
        if rule_applied and current_activity:
            # If a rule was applied and the task changed, end the previous activity
            if current_activity['app_name'] != app_name or current_activity['window_title'] != window_title:
                db.add_activity(
                    current_task_id,
                    current_activity['app_name'],
                    current_activity['window_title'],
                    current_activity['start_time'],
                    datetime.now()
                )
                current_activity = None

        now = datetime.now()

        if current_activity is None:
            current_activity = {'app_name': app_name, 'window_title': window_title, 'start_time': now}
        elif current_activity['app_name'] != app_name or current_activity['window_title'] != window_title:
            db.add_activity(
                current_task_id,
                current_activity['app_name'],
                current_activity['window_title'],
                current_activity['start_time'],
                now
            )
            current_activity = {'app_name': app_name, 'window_title': window_title, 'start_time': now}

    # Graceful shutdown logic
    print("\nStopping tracker...")
    if current_activity and not is_afk:
        db.add_activity(
            current_task_id,
            current_activity['app_name'],
            current_activity['window_title'],
            current_activity['start_time'],
            datetime.now()
        )
    print("Tracker stopped.")

def stop_tracking():
    """Signals the tracking loop to stop gracefully."""
    global tracking_active
    tracking_active.clear()

def main_menu():
    """Presents the main menu to the user."""
    # Removed tracking_thread and listeners_started from here,
    # as start_tracking will now run in the main thread.

    while True:
        print("\n--- Time Tracker Menu ---")
        print("1. Start Tracking")
        print("2. Manage Rules")
        print("3. Exit")
        choice = input("> ")

        if choice == '1':
            print("Starting tracking... (Press Ctrl+C to stop tracking and return to menu)")
            # Start listeners here, as they are part of the tracking process
            start_listeners()
            try:
                start_tracking() # Run in main thread, blocks main_menu
            except KeyboardInterrupt:
                print("\nTracking interrupted by user. Returning to main menu.")
            # After start_tracking returns (e.g., due to Ctrl+C),
            # ensure tracking_active is cleared and any pending activities are logged.
            stop_tracking() # Ensure graceful shutdown
        elif choice == '2':
            manage_rules()
        elif choice == '3':
            print("Exiting Time Tracker. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    db.create_tables()
    main_menu()

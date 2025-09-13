# Time Tracker Application

The Time Tracker is a dual-component application designed to help you monitor and visualize your work activities. It consists of a console-based tracker that records your active applications and window titles, and a web-based dashboard that provides a comprehensive overview and summary of your tracked time.

## Features

*   **Automatic Activity Tracking:** Monitors keyboard/mouse input and active window titles.
*   **Project and Task Management:** Organize your work into projects and specific tasks.
*   **AFK Detection:** Automatically pauses tracking when you are away from your computer.
*   **Rule-Based Categorization:** Define rules to automatically assign activities to projects and tasks based on window titles.
*   **Interactive Console Prompts:** Guides you to select or create projects/tasks when needed.
*   **Web Dashboard:** Visualize your projects, tasks, and activities through a user-friendly web interface.
*   **Daily, Weekly, and Monthly Summaries:** Get insights into your time distribution with charts and detailed breakdowns.
*   **Data Export:** Export summary reports in JSON or CSV format.
*   **SQLite Database:** All data is stored locally in a `timetracker.db` file.

## Components

1.  **Console Tracker (`src/tracker.py`):**
    *   Runs in your terminal.
    *   Monitors your activity and records data into the `timetracker.db` file.
    *   Provides a command-line interface for managing projects, tasks, and rules.

2.  **Web Dashboard (`src/main.py`):**
    *   A FastAPI application that serves a web interface.
    *   Provides API endpoints to access and summarize the tracked data.
    *   The frontend (`templates/index.html`) displays an interactive dashboard with charts and lists.

## Installation

Follow these steps to set up and run the Time Tracker application:

1.  **Clone the Repository:**
    Clone the repository to your local machine:
    ```bash
    git clone https://github.com/Jmiguel17/timetracker-app.git
    cd timetracker-app
    ```

2.  **Create a Python Virtual Environment:**
    It's highly recommended to use a virtual environment to manage dependencies.
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    *   **Windows (Command Prompt):**
        ```bash
        venv\Scripts\activate.bat
        ```
    *   **Windows (PowerShell):**
        ```bash
        venv\Scripts\Activate.ps1
        ```

4.  **Install Dependencies:**
    Install all required Python packages using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Initialize the Database:**
    The database (`timetracker.db`) will be automatically created and tables initialized when you first run the `tracker.py` script. If you ever need to reset the database (e.g., for development or to start fresh), you can run:
    ```bash
    python src/database.py
    ```
    This will delete the existing `timetracker.db` and create new, empty tables.

## Usage

The application has two main parts that can be run independently or concurrently.

### 1. Running the Console Tracker

This component monitors your activity and records data.

```bash
# Make sure your virtual environment is activated
python src/tracker.py
```

Upon running, you will be presented with a menu:

```
--- Time Tracker Menu ---
1. Start Tracking
2. Stop Tracking (Not available while tracking is active in this mode)
3. Manage Rules
4. Exit
>
```

*   **Start Tracking:** Begins monitoring your activity. You will be prompted to select or create a project and task.
    *   **AFK Detection:** If you are inactive for `60` seconds, the tracker will mark you as AFK. When you return, it will prompt you to confirm your current task.
    *   **Periodic Check-in:** Every `30` minutes, the tracker will prompt you to confirm your current task.
    *   **Manual Prompt:** Press `F1` at any time to manually bring up the project/task selection menu.
    *   **Stopping Tracking:** To stop tracking and return to the main menu, press `Ctrl+C` in the terminal where `tracker.py` is running.
*   **Manage Rules:** Allows you to define rules to automatically assign activities to projects/tasks based on window titles. For example, you could create a rule that assigns any activity with "VS Code" in its window title to your "Development" project.
*   **Exit:** Closes the console tracker.

### 2. Running the Web Dashboard

This component provides a visual dashboard for your tracked data.

```bash
# Make sure your virtual environment is activated
uvicorn src.main:app --reload
```

Once the server starts, open your web browser and navigate to:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

The dashboard will display:

*   Lists of your projects, recent tasks, and recent activities.
*   Interactive bar charts for daily, weekly, and monthly summaries of time spent per project.
*   A daily timeline view of your activities.
*   Buttons to export summary data as JSON or CSV.

**Note:** For the dashboard to show meaningful data, you need to have run the console tracker (`src/tracker.py`) to record some activities first.

## Configuration

*   **Database Location:** The `timetracker.db` file is created in the root directory of the project.
*   **AFK Timeout:** You can adjust the `AFK_TIMEOUT` (in seconds) in `src/tracker.py` to change how long before you're considered AFK.
*   **Check-in Interval:** The `CHECKIN_INTERVAL` (in seconds) in `src/tracker.py` determines how often the tracker prompts you for a task update.

## Project Structure

```
timetracker/
├───pyproject.toml
├───README.md
├───requirements.txt
├───timetracker.db         # SQLite database file (generated)
├───src/
│   ├───__init__.py
│   ├───database.py        # Handles database connection and schema
│   ├───main.py            # FastAPI web application and API endpoints
│   └───tracker.py         # Console-based activity tracker
└───templates/
    └───index.html         # Web dashboard frontend
```

## Future Implementations

This section outlines potential features to enhance the Time Tracker application. These ideas are drawn from common features in popular time tracking software and can be used as a roadmap for future development.

### 1. Enhanced Time Tracking & Flexibility

*   **Manual Time Entry:**
    *   **Description:** Allow users to manually add or edit time blocks for activities not captured by the automatic tracker (e.g., meetings, phone calls, or work done away from the computer).
    *   **Implementation Ideas:**
        *   **Backend (`src/main.py`):** Create a new FastAPI endpoint (e.g., `/api/activities/manual`) that accepts POST requests with start time, end time, project ID, and task ID.
        *   **Frontend (`templates/index.html`):** Add a form to the web dashboard where users can input the details for a manual time entry.
        *   **Database (`src/database.py`):** Create a new function to insert the manually entered activity into the `activities` table.

*   **Enhanced Idle Time Detection:**
    *   **Description:** Improve the current AFK feature by providing users with options upon their return. For example, the application could ask whether to discard the idle time, allocate it to the last active task, or create a new entry.
    *   **Implementation Ideas:**
        *   **Tracker (`src/tracker.py`):** In the `on_input_event` function, when a user returns from being AFK, trigger a console prompt that presents the user with the different options for handling the idle time.

### 2. Goal Setting and Productivity

*   **Daily and Weekly Goals:**
    *   **Description:** Enable users to set time-based goals for projects (e.g., "spend 10 hours on Project X this week"). The dashboard could then visualize progress towards these goals.
    *   **Implementation Ideas:**
        *   **Database (`src/database.py`):** Add a `goals` table to store goal information (e.g., `project_id`, `start_date`, `end_date`, `target_hours`).
        *   **Backend (`src/main.py`):** Create API endpoints for creating, retrieving, and updating goals. Add logic to calculate goal progress.
        *   **Frontend (`templates/index.html`):** Add a new section to the dashboard to display goal progress bars or charts.

*   **Productivity Reports:**
    *   **Description:** Allow users to classify applications and websites as "productive" or "unproductive." This would enable the generation of reports that provide insights into how time is spent.
    *   **Implementation Ideas:**
        *   **Database (`src/database.py`):** Create an `app_classifications` table to store application names and their productivity status (`productive`, `neutral`, `unproductive`).
        *   **Frontend (`templates/index.html`):** Add a settings page where users can manage these classifications.
        *   **Backend (`src/main.py`):** Update the summary/reporting endpoints to include productivity breakdowns.

### 3. Advanced Reporting and Analytics

*   **Client and Billable Hours Tracking:**
    *   **Description:** For freelancers and agencies, add the ability to associate projects with clients and mark time entries as "billable." This would facilitate invoicing and client-specific reporting.
    *   **Implementation Ideas:**
        *   **Database (`src/database.py`):** Add a `clients` table and a `client_id` foreign key to the `projects` table. Add a `billable` flag (boolean) to the `activities` or `tasks` table.
        *   **Backend (`src/main.py`):** Update API endpoints to allow filtering by client and to calculate billable vs. non-billable hours.
        *   **Frontend (`templates/index.html`):** Update the dashboard to display client information and billable hour summaries.

*   **Custom Date Range Reports:**
    *   **Description:** Extend the reporting feature to allow users to select a custom date range for generating summaries and reports, instead of being limited to predefined daily, weekly, or monthly views.
    *   **Implementation Ideas:**
        *   **Frontend (`templates/index.html`):** Add two date input fields (`start_date`, `end_date`) to the reporting section of the dashboard.
        *   **Backend (`src/main.py`):** Modify the reporting endpoints (e.g., `/api/summary/custom`) to accept `start_date` and `end_date` query parameters.

### 4. Integrations

*   **Calendar Integration (e.g., Google Calendar, Outlook):**
    *   **Description:** Connect to external calendar services to automatically import events and suggest them as time entries. This would streamline the process of logging meetings and scheduled appointments.
    *   **Implementation Ideas:**
        *   This is a more complex feature that would require using external APIs (e.g., Google Calendar API).
        *   **Backend (`src/main.py`):** Implement OAuth 2.0 for user authorization. Create a service to fetch calendar events and a new API endpoint to serve them to the frontend.
        *   **Frontend (`templates/index.html`):** Add a "Connect Calendar" button and a view to display imported events and convert them into time entries.

*   **Project Management Tool Integration (e.g., Jira, Trello):**
    *   **Description:** Sync projects and tasks from popular project management tools to avoid manual duplication and keep the time tracker aligned with existing workflows.
    *   **Implementation Ideas:**
        *   Similar to calendar integration, this would involve using the APIs of tools like Jira or Trello.
        *   **Backend (`src/main.py`):** Implement API key-based authentication or OAuth. Create services to sync projects and tasks.

### Where to Get Ideas

For further inspiration, it is helpful to study the feature sets of established time tracking applications. Good places to look include:

*   **Open Source Projects on GitHub:** Search for "time tracking" or "tui time tracker" to find projects like `watson`, `Timewarrior`, and others. Reviewing their features and code can provide valuable implementation insights.
*   **Commercial Applications:** Analyze the features offered by popular commercial tools such as Toggl, Clockify, and Harvest. While their code is not public, their feature lists, documentation, and blog posts can be a great source of ideas for improving user experience and functionality.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

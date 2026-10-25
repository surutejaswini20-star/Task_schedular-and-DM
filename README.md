# 🚀 Task Scheduler and Deadline Manager

A smart, responsive web application designed to help users organize tasks, manage study schedules, track deadlines, and receive timely email reminders.

🌐 **Live Website:** [Task Scheduler and Deadline Manager](https://task-scheduling-and-deadline-manager.onrender.com/)

---

## 📌 Overview

Task Scheduler and Deadline Manager is a productivity application that helps users plan their tasks, organize study schedules, and stay on top of deadlines. It combines task management, automated scheduling, background processing, and email notifications in one platform.

The application includes a responsive interface with dark and light themes, mobile-friendly navigation, authentication, and deadline validation.

## ✨ Features

- **User Authentication:** Registration, email verification, login, and logout.
- **Task Management:** Create, manage, complete, and delete tasks.
- **Study Scheduling:** Organize study activities and deadlines.
- **Automated Reminders:** Schedule reminders for upcoming tasks.
- **Email Notifications:** Send verification emails and task reminders through Brevo.
- **Background Processing:** Use Celery workers to process scheduled tasks.
- **Periodic Scheduling:** Use Celery Beat to trigger recurring reminder jobs.
- **PostgreSQL Database:** Store application data using Neon PostgreSQL.
- **Responsive UI:** Adapt layouts for desktop, tablet, and mobile screens.
- **Dark and Light Themes:** Switch between themes with browser preference persistence.
- **Mobile Navigation:** Access the sidebar through a mobile navigation drawer.
- **Input Validation:** Validate time formats, deadlines, and reminder schedules.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | PostgreSQL, Neon |
| Task Queue | Celery |
| Message Broker | Redis, Upstash |
| Email Service | Brevo API |
| Production Server | Gunicorn |
| Deployment | Render |
| Testing | Pytest |

## 🏗️ System Architecture

1. **User Interface:** Users register, log in, and manage tasks through the web application.
2. **Flask Backend:** Handles authentication, task operations, validation, and application requests.
3. **PostgreSQL Database:** Stores users, tasks, reminders, and related application records.
4. **Redis Broker:** Transfers background task messages between the application and Celery.
5. **Celery Worker:** Processes reminder and email-related background tasks.
6. **Celery Beat:** Schedules periodic jobs, including recurring reminder checks.
7. **Brevo API:** Delivers transactional emails and reminders.
8. **Render:** Hosts the web application and background services.

## 🌐 Live Demo

Visit the deployed application:

**[Open Task Scheduler and Deadline Manager →](https://task-scheduling-and-deadline-manager.onrender.com/)**

The application may take some time to respond if the hosting service is waking up after inactivity.

## 📂 Project Structure

```text
Task-Scheduler-and-Deadline-Manager/
├── app.py
├── tasks.py
├── scheduler.py
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example
├── templates/
├── static/
├── tests/
└── README.md
```

*This is an illustrative structure. Adjust it to match the actual files and folders in your repository.*

## ⚙️ Local Installation and Setup

### Prerequisites

- Python 3.11 recommended
- Redis server
- Git
- PostgreSQL for production or SQLite for local development

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd YOUR_PROJECT_FOLDER
```

Replace the placeholders with your actual GitHub repository URL and folder name.

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
venv\Scripts\Activate.ps1
```

**Linux, macOS, or WSL:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**Linux, macOS, or WSL:**

```bash
cp .env.example .env
```

Edit `.env` and configure the required values:

```env
SECRET_KEY=your_generated_secret
FLASK_DEBUG=false
COOKIE_SECURE=false
TRUST_PROXY=false
PORT=5000

DATABASE_URL=sqlite:///study_scheduler.db
REDIS_URL=redis://localhost:6379/0

BREVO_API_KEY=
EMAIL_FROM=
EMAIL_FROM_NAME=TaskScheduler and DeadlineManager
```

Generate a secret key using:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Use a secure, unique key. Never commit your real `.env` file to GitHub.

For local development, the SQLite database is used by default. Configure a suitable PostgreSQL connection string when using Neon.

### 5. Start Redis

Ensure that your Redis server is running and reachable at the address specified by `REDIS_URL`.

Test a local Redis server with:

```bash
redis-cli ping
```

Expected response:

```text
PONG
```

### 6. Run the application

Open separate terminals from the project root.

**Terminal 1 — Flask application**

```bash
python app.py
```

**Terminal 2 — Celery worker**

```bash
celery -A tasks.celery worker --loglevel=INFO --pool=solo
```

**Terminal 3 — Celery Beat scheduler**

```bash
celery -A tasks.celery beat --loglevel=INFO
```

On Windows, `--pool=solo` is generally a convenient option for local Celery worker development.

Open the local URL printed by Flask, usually:

`http://127.0.0.1:5000`

## ☁️ Production Deployment

The project is configured for deployment with Render, Neon PostgreSQL, Upstash Redis, and Brevo.

### Recommended services

| Service | Purpose |
|---|---|
| Render | Hosts the application and background processes |
| Neon PostgreSQL | Persistent relational database |
| Upstash Redis | Celery message broker |
| Brevo | Transactional email delivery |

### Deployment steps

1. Push the project to a GitHub repository.
2. Create a PostgreSQL database on Neon.
3. Create a TLS-enabled Redis database on Upstash.
4. Configure Brevo and verify the sender email address.
5. Open the Render dashboard and choose **New → Blueprint**.
6. Connect the repository containing `render.yaml`.
7. Configure the required environment variables for the web, worker, and Beat services.
8. Deploy the services and inspect their logs.

### Required production environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Session signing and OTP hashing |
| `DATABASE_URL` | Neon PostgreSQL connection |
| `REDIS_URL` | Redis broker and result backend |
| `BREVO_API_KEY` | Brevo email API authentication |
| `EMAIL_FROM` | Verified sender email address |
| `COOKIE_SECURE` | Enable secure cookies over HTTPS |
| `TRUST_PROXY` | Configure proxy-aware behavior |
| `FLASK_DEBUG` | Keep debugging disabled in production |

Use `COOKIE_SECURE=true`, `TRUST_PROXY=true`, and `FLASK_DEBUG=false` for the production configuration described by this project.

Keep database credentials, API keys, and secret keys private. Do not commit them to source control.

The web application, Celery worker, and Celery Beat scheduler must all start successfully for the complete reminder workflow to operate.

**Hosting note:** Free hosting services may sleep or restart, potentially delaying scheduled reminders. Check the current service limits and pricing when choosing a production plan.

## 🧪 Testing

Run the available tests using:

```bash
python -m pytest -q
```

After deployment, manually test:

- User registration and email verification
- Login and logout
- Task creation and updates
- Task completion and deletion
- Reminder creation and validation
- Email reminder delivery
- Periodic scheduling through Celery Beat

Email delivery requires valid Brevo configuration, while scheduled reminders require a functioning Redis broker and active Celery processes.

## 📱 UI and Accessibility

- Responsive layouts for desktop and mobile devices.
- Dark and light theme switching.
- Mobile sidebar navigation.
- Accessible time-entry behavior.
- Validation for malformed times and invalid deadline/reminder combinations.
- Browser-local theme preference persistence.

Enter time values in 24-hour `HH:MM` format, such as `09:30` or `18:45`.

If theme changes do not appear immediately, try a hard refresh using `Ctrl + F5`.

## 🔒 Security and Configuration

- Keep `.env` and other credential files out of GitHub.
- Use unique, strong secret keys.
- Use TLS-enabled database and Redis connections in production.
- Keep Flask debug mode disabled in production.
- Use verified sender addresses for transactional email.
- Use database migrations for future schema changes rather than relying only on automatic table creation.

## 🚀 Future Enhancements

- Calendar integration
- Task priority analytics
- Personalized study recommendations
- Productivity statistics and progress reports
- Additional scheduling and notification options

## 👩‍💻 Author

Developed as a task management and study productivity project.

**Live Application:** [Task Scheduler and Deadline Manager](https://task-scheduling-and-deadline-manager.onrender.com/)

---

*Plan your tasks. Manage your deadlines. Stay productive.*

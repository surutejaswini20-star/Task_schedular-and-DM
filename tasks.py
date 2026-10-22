"""Celery worker and durable reminder dispatch. Email uses Brevo HTTPS API, not SMTP."""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from celery import Celery
from dotenv import load_dotenv


# Ensure the project root is importable when Celery starts
# from a different working directory.
PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from the project root.
load_dotenv(PROJECT_ROOT / ".env")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "study_scheduler",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery.conf.update(
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "dispatch-due-reminders-every-minute": {
            "task": "tasks.dispatch_due_reminders",
            "schedule": 60.0,
        }
    },
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
)


def _app_and_models():
    """Create the Flask application and return its database models."""
    from app import (
        create_app,
        db,
        User,
        StudyTask,
        Reminder,
        DailyReminderLog,
    )

    return (
        create_app(),
        db,
        User,
        StudyTask,
        Reminder,
        DailyReminderLog,
    )


def reminder_user_name(db, User, user_id):
    """Return the account name for a reminder greeting, if the account exists."""
    user = db.session.get(User, user_id)
    return user.name if user else ""


def _send_email(recipient, subject, html):
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    sender_email = os.getenv("EMAIL_FROM", "").strip()
    sender_name = os.getenv(
        "EMAIL_FROM_NAME",
        "TaskScheduler and DeadlineManager",
    ).strip()

    if not api_key or not sender_email:
        raise RuntimeError(
            "Set BREVO_API_KEY and EMAIL_FROM. "
            "Verify the sender in Brevo before production sending."
        )

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        json={
            "sender": {
                "name": sender_name,
                "email": sender_email,
            },
            "to": [{"email": recipient}],
            "subject": subject,
            "htmlContent": html,
        },
        timeout=20,
    )

    if response.status_code not in (200, 201, 202):
        raise RuntimeError(
            f"Brevo API returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    return response.json() if response.content else {}


@celery.task(
    name="tasks.send_reminder",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=4,
)
def send_reminder(self, reminder_id):
    app, db, User, StudyTask, Reminder, DailyReminderLog = (
        _app_and_models()
    )

    with app.app_context():
        reminder = db.session.get(Reminder, reminder_id)

        if not reminder or reminder.status == "sent":
            return "Reminder no longer needs sending."

        task = db.session.get(StudyTask, reminder.task_id)

        if not task:
            reminder.status = "cancelled"
            db.session.commit()
            return "Task deleted; reminder cancelled."

        if task.status == "Completed":
            reminder.status = "cancelled"
            reminder.last_error = None
            db.session.commit()
            return "Task completed; reminder cancelled without sending."

        if reminder.status in {"sent", "cancelled"}:
            return "Reminder no longer needs sending."

        due = (
            f"{task.due_date:%d %b %Y} "
            f"at {task.due_time:%H:%M}"
        )

        subject = f"Study reminder: {task.title}"

        from flask import render_template

        html = render_template(
            "emails/deadline_reminder.html",
            user_name=reminder_user_name(db, User, reminder.user_id),
            task_title=task.title,
            subject=task.subject,
            deadline=due,
            priority=task.priority,
            duration=task.duration,
            notes=task.notes or "",
        )

        try:
            app.logger.info(
                "Sending deadline reminder using templates/emails/deadline_reminder.html "
                "for reminder_id=%s",
                reminder_id,
            )
            _send_email(
                reminder.recipient,
                subject,
                html,
            )

            reminder.status = "sent"
            reminder.sent_at = datetime.utcnow()
            reminder.attempts += 1
            reminder.last_error = None
            db.session.commit()

            return f"Reminder {reminder_id} sent."

        except Exception as exc:
            reminder.status = (
                "queued"
                if self.request.retries < self.max_retries
                else "failed"
            )
            reminder.attempts += 1
            reminder.last_error = str(exc)[:1000]
            db.session.commit()
            raise


@celery.task(
    name="tasks.send_daily_digest",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_daily_digest(self, user_id, local_date):
    app, db, User, StudyTask, Reminder, DailyReminderLog = (
        _app_and_models()
    )

    with app.app_context():
        user = db.session.get(User, user_id)

        if not user or not user.daily_reminder_enabled:
            return "Daily reminders disabled."

        pending_tasks = (
            StudyTask.query
            .filter_by(user_id=user.id, status="Pending")
            .order_by(StudyTask.due_date, StudyTask.due_time)
            .all()
        )

        if not pending_tasks:
            return "No pending tasks; no email sent."

        tasks_for_email = pending_tasks[:30]

        from flask import render_template

        email_tasks = [
            {
                "title": task.title,
                "subject": task.subject,
                "due_label": (
                    f"{task.due_date:%d %b %Y} at "
                    f"{task.due_time:%H:%M}"
                ),
                "priority": task.priority,
                "duration": task.duration,
                "notes": task.notes or "",
            }
            for task in tasks_for_email
        ]

        due_today_count = sum(
            task.due_date.isoformat() == local_date
            for task in pending_tasks
        )
        total_minutes = sum(task.duration for task in pending_tasks)

        html = render_template(
            "emails/daily_reminder.html",
            user_name=user.name,
            total_tasks=len(pending_tasks),
            due_today_count=due_today_count,
            total_minutes=total_minutes,
            tasks=email_tasks,
        )

        app.logger.info(
            "Sending daily digest using templates/emails/daily_reminder.html "
            "for user_id=%s and local_date=%s",
            user.id,
            local_date,
        )
        _send_email(
            user.email,
            "Your daily TaskScheduler and DeadlineManager study plan",
            html,
        )

        return f"Daily digest sent to {user.email}."


@celery.task(name="tasks.dispatch_due_reminders")
def dispatch_due_reminders():
    """Create missing deadline reminders, cancel completed tasks,
    and dispatch reminders whose scheduled times have arrived.
    """
    app, db, User, StudyTask, Reminder, DailyReminderLog = (
        _app_and_models()
    )

    dispatched = 0
    auto_created = 0

    with app.app_context():
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

        # Create missing automatic deadline reminders.
        pending_tasks = StudyTask.query.filter_by(
            status="Pending"
        ).all()

        for study_task in pending_tasks:
            user = db.session.get(User, study_task.user_id)

            if not user or not user.email:
                continue

            try:
                user_tz = ZoneInfo(
                    user.timezone or "Asia/Kolkata"
                )
            except Exception:
                user_tz = ZoneInfo("UTC")

            deadline_local = datetime.combine(
                study_task.due_date,
                study_task.due_time,
            ).replace(tzinfo=user_tz)

            deadline_utc = (
                deadline_local
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )

            if deadline_utc <= now_utc:
                continue

            existing = Reminder.query.filter_by(
                task_id=study_task.id,
                scheduled_at=deadline_utc,
            ).first()

            if existing:
                continue

            db.session.add(
                Reminder(
                    user_id=user.id,
                    task_id=study_task.id,
                    recipient=user.email,
                    scheduled_at=deadline_utc,
                    status="scheduled",
                )
            )

            auto_created += 1

        if auto_created:
            db.session.commit()

        # Cancel unsent reminders for completed tasks.
        completed_ids = [
            row.id
            for row in StudyTask.query.filter_by(
                status="Completed"
            ).all()
        ]

        if completed_ids:
            (
                Reminder.query
                .filter(
                    Reminder.task_id.in_(completed_ids),
                    Reminder.status.in_(["scheduled", "queued"]),
                )
                .update(
                    {"status": "cancelled"},
                    synchronize_session=False,
                )
            )

            db.session.commit()

        # Dispatch reminders whose scheduled times have arrived.
        due_reminders = (
            Reminder.query
            .join(
                StudyTask,
                Reminder.task_id == StudyTask.id,
            )
            .filter(
                Reminder.status == "scheduled",
                Reminder.scheduled_at <= now_utc,
                StudyTask.status != "Completed",
            )
            .order_by(Reminder.scheduled_at)
            .limit(200)
            .all()
        )

        for reminder in due_reminders:
            reminder.status = "queued"
            db.session.commit()

            try:
                send_reminder.delay(reminder.id)
                dispatched += 1
            except Exception:
                reminder.status = "scheduled"
                db.session.commit()
                raise

        # Queue each user's daily digest once per local date.
        users = User.query.filter_by(
            daily_reminder_enabled=True
        ).all()

        utc_now = datetime.now(timezone.utc)

        for user in users:
            try:
                user_tz = ZoneInfo(
                    user.timezone or "Asia/Kolkata"
                )
            except Exception:
                user_tz = ZoneInfo("UTC")

            local_now = utc_now.astimezone(user_tz)
            daily_time = user.daily_reminder_time

            if not daily_time:
                continue

            if (
                local_now.hour,
                local_now.minute,
            ) != (
                daily_time.hour,
                daily_time.minute,
            ):
                continue

            day = local_now.date().isoformat()

            already_sent = DailyReminderLog.query.filter_by(
                user_id=user.id,
                local_date=day,
            ).first()

            if already_sent:
                continue

            db.session.add(
                DailyReminderLog(
                    user_id=user.id,
                    local_date=day,
                )
            )

            try:
                db.session.commit()
                send_daily_digest.delay(user.id, day)
                dispatched += 1

            except Exception:
                db.session.rollback()

                (
                    DailyReminderLog.query
                    .filter_by(user_id=user.id, local_date=day)
                    .delete(synchronize_session=False)
                )

                db.session.commit()
                raise

    return {
        "auto_created": auto_created,
        "dispatched": dispatched,
    }


def _escape(value):
    from html import escape
    return escape(str(value), quote=True)

# TaskScheduler and DeadlineManager — deployment-ready package

Flask application with PostgreSQL support, Celery reminders, and responsive HTML/CSS UI.

## Recommended hosting combination

- **Application + Celery worker + Celery Beat:** Render
- **Database:** Neon PostgreSQL
- **Redis/Celery broker:** Upstash Redis (TLS URL) or another managed Redis service
- **Transactional email:** Brevo API

This is the closest fit to the current code because it already includes a `render.yaml`, Gunicorn, Celery worker/Beat processes, PostgreSQL's `psycopg` driver, and Brevo email integration. Render's background workers are separate services and may incur charges; check the current plans before deploying. The database and Redis are external managed services, so app redeploys do not rely on local filesystem persistence.

## Before deploying

1. Create a Neon project and database.
2. In Neon, copy the **pooled** connection string for the application. It should use a PostgreSQL URL and require SSL. SQLAlchemy converts `postgres://` / `postgresql://` schemes to `postgresql+psycopg://` automatically. Keep the URL private.
3. Create a Redis database with TLS enabled. Copy its `rediss://...` URL. If the provider gives a `redis://` URL, use that only when the provider documents it as appropriate for your deployment.
4. Create/verify a sender in Brevo and obtain its API key. Email verification and reminder delivery will not work until `BREVO_API_KEY` and `EMAIL_FROM` are set.
5. Push this folder to a Git repository, excluding `.env`, virtual environments, caches, local databases, and generated Celery schedule files.
6. In Render, choose **New + → Blueprint** and connect the repository containing `render.yaml`.
7. Set the environment variables marked as manual inputs for the web, worker, and beat services:
   - `DATABASE_URL`: Neon connection string
   - `REDIS_URL`: managed Redis connection string
   - `BREVO_API_KEY`: Brevo API key
   - `EMAIL_FROM`: verified sender email
   The Blueprint generates a `SECRET_KEY` for the web service. Keep all secrets out of source control.
8. Deploy all three services. The web service has a `/health` health-check endpoint. Confirm that the web, Celery worker, and Celery Beat services all start successfully in Render logs.

### Required environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `SECRET_KEY` | Web | Session signing and OTP hashing |
| `DATABASE_URL` | Web, worker, beat | Neon PostgreSQL connection |
| `REDIS_URL` | Web, worker, beat | Celery broker and result backend |
| `BREVO_API_KEY` | Web, worker | Sends verification and reminder emails |
| `EMAIL_FROM` | Web, worker | Verified Brevo sender |
| `COOKIE_SECURE` | Web | Keep `true` on HTTPS deployment |
| `TRUST_PROXY` | Web | Set `true` behind Render's proxy |
| `FLASK_DEBUG` | Web | Keep `false` in production |

`EMAIL_FROM_NAME` and `DISPOSABLE_EMAIL_DOMAINS` are optional. The included `render.yaml` configures the production flags.

## Local development

Python 3.11 is recommended.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# Git Bash / macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with a strong local `SECRET_KEY`. For local use, SQLite is the default. A local Redis server is required for Celery reminder delivery. Run the processes in separate terminals:

```bash
python app.py
celery -A tasks.celery worker --loglevel=INFO --pool=solo
celery -A tasks.celery beat --loglevel=INFO
```

On Windows, `--pool=solo` is generally the simplest Celery worker pool for local development. In production, the Render worker uses the default process pool.

## Validation

```bash
python -m pytest -q
```

The included tests cover the scheduling algorithm. After deployment, manually verify registration/email OTP, login, task creation, completion/deletion, extra reminders, and daily digest delivery. Email functionality requires a working Brevo configuration and running Celery worker + Beat services.

## Notes

- Tables are created automatically at app startup. For future schema changes, use formal database migrations rather than relying on `create_all`.
- Neon connection strings and Redis URLs contain credentials; never commit them.
- The app intentionally does not use a local SQLite database in production when `DATABASE_URL` is set.


## UI enhancements included

- **Dark / light theme toggle:** use the theme button in the top bar. Your preference is saved in browser local storage and persists across pages.
- **Mobile left navigation drawer:** tap the hamburger button to open the left sidebar on phones and small screens. Tap the backdrop, choose a navigation item, or press Escape to close it.
- **Logout:** the existing sign-out action remains in the sidebar account section and uses the application's POST + CSRF flow.
- **Responsive layouts:** forms, task lists, navigation, and page spacing adapt to narrow screens.
- **Time input accessibility:** time fields use a normal text keyboard on mobile instead of forcing the numeric keypad. Enter 24-hour `HH:MM` values such as `09:30` or `18:45`. Values outside `00:00`–`23:59`, malformed values, past deadlines, reminders in the past, and reminders at/after a task deadline are rejected with a validation message.
- Existing authentication, email verification, task scheduling, reminders, and data model code are retained.

## Theme and mobile navigation troubleshooting

If the theme toggle does not appear to change after an update, hard-refresh the browser (`Ctrl+F5`). The theme preference is stored per browser. The mobile menu appears at viewport widths up to 850px.

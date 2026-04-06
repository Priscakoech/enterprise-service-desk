# Enterprise Service Desk

A full-stack enterprise ticketing and support management system built with Django REST Framework and React. This system enables organizations to manage support tickets, track SLA compliance, organize teams and departments, and provide real-time communication between requesters and support agents.

![Dashboard Overview](screenshots/dashboard.png)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Deploying to Railway](#deploying-to-railway)
  - [Step 1 — Push to GitHub](#step-1--push-to-github)
  - [Step 2 — Create Railway Project](#step-2--create-railway-project)
  - [Step 3 — Add PostgreSQL](#step-3--add-postgresql)
  - [Step 4 — Deploy the Backend](#step-4--deploy-the-backend)
  - [Step 5 — Deploy the Frontend](#step-5--deploy-the-frontend)
  - [Step 6 — First-Time Setup](#step-6--first-time-setup)
  - [Updating After Code Changes](#updating-after-code-changes)
- [User Roles and Permissions](#user-roles-and-permissions)
- [Onboarding Guide](#onboarding-guide)
- [Ticket Workflow](#ticket-workflow)
- [SLA Management](#sla-management)
- [API Reference](#api-reference)
- [Screenshots](#screenshots)

---

## Features

- **Multi-Role Support**: Admin, Manager, Agent, and Requester roles with granular permissions
- **Ticket Management**: Create, assign, track, and resolve support tickets
- **Real-Time Chat**: Live messaging between requesters and agents on tickets
- **SLA Engine**: Comprehensive SLA tracking with business hours support, multiple metrics, and breach notifications
- **Department & Team Organization**: Hierarchical organization structure with departments and teams
- **Auto-Assignment**: Intelligent ticket routing to least-busy agents
- **Analytics Dashboard**: Visual reports for ticket metrics, agent performance, and SLA compliance
- **Notification System**: In-app notifications for ticket updates, assignments, and SLA warnings
- **Dark Mode**: Full dark mode support across the application
- **Responsive Design**: Mobile-friendly interface

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python 3.12 | Runtime environment |
| Django 4.2+ | Web framework |
| Django REST Framework | API development |
| Django Channels | WebSocket support for real-time features |
| PostgreSQL | Production database |
| Gunicorn + Uvicorn | Production ASGI server |
| WhiteNoise | Static file serving without Nginx |
| Pillow | Image processing for attachments and profiles |

### Frontend
| Technology | Purpose |
|---|---|
| React 19 | UI framework |
| Vite 8 | Build tool and dev server |
| TailwindCSS 4 | Utility-first CSS framework |
| Axios | HTTP client for API requests |
| Recharts | Data visualization and charts |
| Lucide React | Icon library |
| React Router 7 | Client-side routing |

---

## Project Structure

```
enterprise-service-desk/
├── backend/                    # Django REST API
│   ├── manage.py              # Django management script
│   ├── .env                   # Environment variables (not committed)
│   ├── servicetrack/          # Django project configuration
│   │   ├── settings.py        # Main settings (prod-ready)
│   │   ├── urls.py            # Root URL routing
│   │   ├── asgi.py            # ASGI config (WebSocket + HTTP)
│   │   └── wsgi.py            # WSGI config
│   ├── accounts/              # User authentication & management
│   ├── servicedesk/           # Tickets, responses, SLA engine
│   ├── teams/                 # Departments & teams
│   ├── notifications/         # In-app notifications
│   └── analytics/             # Reports & metrics
├── frontend/                   # React SPA
│   ├── package.json           # Node.js dependencies
│   ├── vite.config.js         # Vite configuration
│   └── src/
│       ├── main.jsx           # Application entry point
│       ├── App.jsx            # Router & route definitions
│       ├── api/               # API client configuration
│       ├── contexts/          # React contexts (Auth, Theme)
│       ├── components/        # Reusable UI components
│       ├── pages/             # Page components
│       └── hooks/             # Custom React hooks
├── requirements.txt           # Python dependencies
├── Procfile                   # Railway backend start command
├── runtime.txt                # Python version pin
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
└── screenshots/               # Application screenshots
```

---

## Local Development

### Prerequisites

- **Python 3.10+**
- **Node.js 18+ and npm 9+**
- **Git**

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

4. **Create environment file:**

   Create `backend/.env`:
   ```env
   SECRET_KEY=your-secret-key-here-make-it-long-and-random
   DEBUG=True
   ```

   > With `DEBUG=True` and no `DATABASE_URL`, the app automatically uses SQLite for local development — no database setup needed.

5. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (admin account):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the backend server:**
   ```bash
   python manage.py runserver
   ```
   Backend API will be at `http://localhost:8000`

### Frontend Setup

1. **Open a new terminal and navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the dev server:**
   ```bash
   npm run dev
   ```
   Frontend will be at `http://localhost:5173`

> Vite's dev server automatically proxies `/api`, `/media`, and `/ws` requests to the Django backend at `localhost:8000`, so everything works out of the box locally.

---

## Deploying to Railway

Railway deploys directly from your GitHub repo. You'll create **3 services**: Backend, Frontend, and PostgreSQL.

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit — production ready"
git remote add origin https://github.com/YOUR_USERNAME/enterprise-service-desk.git
git push -u origin main
```

> ⚠️ Make sure `.env` files are **not** committed (the `.gitignore` handles this).

### Step 2 — Create Railway Project

1. Go to [railway.app](https://railway.app) and log in
2. Click **"New Project"**
3. Choose **"Empty Project"** (we'll add services one by one)

### Step 3 — Add PostgreSQL

1. Inside your Railway project, click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway will provision a Postgres instance
3. Click on it → go to **"Variables"** tab → note that `DATABASE_URL` is available
4. You'll reference this from your backend service

### Step 4 — Deploy the Backend

1. Click **"+ New"** → **"GitHub Repo"** → select your repo
2. Railway will detect a Python app from `requirements.txt`

3. **Configure the service:**
   - Click on the service → **Settings** tab
   - **Root Directory**: leave as `/` (project root)
   - Railway will auto-detect the `Procfile`

4. **Set environment variables** (go to **Variables** tab):

   | Variable | Value |
   |---|---|
   | `SECRET_KEY` | A long random string (use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
   | `DEBUG` | `False` |
   | `DATABASE_URL` | Click **"Add Reference"** → select your Postgres service → `DATABASE_URL` |
   | `ALLOWED_HOSTS` | Your backend domain, e.g. `your-backend.up.railway.app` |
   | `CORS_ALLOWED_ORIGINS` | `https://your-frontend.up.railway.app` |
   | `CSRF_TRUSTED_ORIGINS` | `https://your-frontend.up.railway.app` |
   | `CORS_ALLOW_ALL_ORIGINS` | `False` |
   | `ADMIN_USERNAME` | Your admin username (default: `admin`) |
   | `ADMIN_PASSWORD` | **Set a strong password!** (default: `admin`) |
   | `ADMIN_EMAIL` | Admin email (default: `admin@servicedesk.local`) |

   > 💡 Railway auto-provides `RAILWAY_PUBLIC_DOMAIN` which the settings.py already picks up for `ALLOWED_HOSTS`. But setting it explicitly is safer.

5. **Generate a domain:**
   - Go to **Settings** → **Networking** → click **"Generate Domain"**
   - You'll get something like `your-backend-xxxx.up.railway.app`
   - Use this domain in the CORS/ALLOWED_HOSTS vars above

6. **Deploy** — Railway will auto-deploy. On every deploy, the `Procfile` automatically:
   - Runs database migrations
   - Seeds the admin user (idempotent — won't create duplicates)
   - Collects static files
   - Starts Gunicorn + Uvicorn

### Step 5 — Deploy the Frontend

1. Click **"+ New"** → **"GitHub Repo"** → select the **same** repo again
2. This creates a second service from the same repo

3. **Configure the service:**
   - **Settings** tab → set **Root Directory** to `frontend`
   - Railway detects Node.js from `package.json`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npx serve dist -s -l $PORT`

   > You may need to add `serve` as a dependency: go to frontend and run `npm install serve` first, or add it in package.json before pushing. Alternatively use `npx serve`.

4. **Set environment variables:**

   | Variable | Value |
   |---|---|
   | `VITE_API_URL` | `https://your-backend-xxxx.up.railway.app/api` |

   > ⚠️ `VITE_` variables are baked into the build. After changing this, **trigger a redeploy**.

5. **Generate a domain:**
   - **Settings** → **Networking** → **"Generate Domain"**
   - This is your public-facing app URL

### Step 6 — First-Time Setup

The admin user is created **automatically** on the first deploy via the `seed_admin` management command.

1. After the backend deploys successfully, check the deploy logs — you should see:
   ```
   Created admin superuser: admin (password change required on first login)
   ```
2. Visit your frontend domain — the app is live!
3. Log in with the credentials you set in `ADMIN_USERNAME` / `ADMIN_PASSWORD` env vars
4. You'll be prompted to change the password on first login

> 💡 The `seed_admin` command is **idempotent** — it checks if the admin already exists before creating one. This means it's safe to run on every deploy without creating duplicates.

### Updating After Code Changes

```bash
git add .
git commit -m "Your changes"
git push
```

Railway auto-deploys on every push to `main`. Migrations and admin seeding run automatically on each deploy via the `Procfile`.

---

## Environment Variables Reference

### Backend (set in Railway dashboard)

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key | **Yes** |
| `DEBUG` | `True`/`False` — always `False` in prod | Yes |
| `DATABASE_URL` | PostgreSQL connection string (Railway auto-provides) | **Yes (prod)** |
| `ALLOWED_HOSTS` | Comma-separated hostnames | Yes |
| `CORS_ALLOWED_ORIGINS` | Frontend URL(s), comma-separated | Yes (prod) |
| `CSRF_TRUSTED_ORIGINS` | Frontend URL(s), comma-separated | Yes (prod) |
| `CORS_ALLOW_ALL_ORIGINS` | `True` for dev, `False` for prod | No |
| `ADMIN_USERNAME` | Admin username for auto-seeding (default: `admin`) | No |
| `ADMIN_PASSWORD` | Admin password for auto-seeding — **set a real one in prod!** | No |
| `ADMIN_EMAIL` | Admin email for auto-seeding (default: `admin@servicedesk.local`) | No |

### Frontend (set in Railway dashboard)

| Variable | Description | Required |
|---|---|---|
| `VITE_API_URL` | Backend API URL, e.g. `https://backend.up.railway.app/api` | **Yes (prod)** |

---

## User Roles and Permissions

The system supports four user roles with different access levels:

### Admin (System Administrator)
| Permission | Access |
|---|---|
| Manage users | Create, edit, blacklist, deactivate users |
| Manage departments | Create and edit departments |
| Manage teams | Create and edit teams |
| Configure SLA policies | Full SLA policy management |
| View analytics | Organization-wide analytics |
| Generate auth codes | Create signup codes for agents/managers |

### Manager
| Permission | Access |
|---|---|
| View tickets | Department tickets only |
| Assign agents | Can assign agents to tickets in their department |
| View analytics | Department-level analytics |
| Create tickets | Can create new tickets |

### Agent
| Permission | Access |
|---|---|
| Manage assigned tickets | Edit status, add responses to assigned tickets |
| View department tickets | Read-only access to department tickets |
| Create tickets | Can create new tickets |
| Respond to tickets | Can chat with requesters |

### Requester
| Permission | Access |
|---|---|
| Create tickets | Can create new support tickets |
| View own tickets | View tickets they created |
| Respond to tickets | Can chat with agents on their tickets |

---

## Onboarding Guide

### Creating Organizations (Departments & Teams)

Before users can be added to the system, an admin must set up the organizational structure.

#### Method 1: Using the Configuration File (Recommended for Initial Setup)

Edit `backend/org_config.py`:
```python
DEPARTMENTS = {
    "Human Resources": [
        "Recruitment",
        "Benefits",
        "Employee Relations",
    ],
    "IT": [
        "Help Desk",
        "Infrastructure",
        "Development",
    ],
}
```
Changes auto-sync to the database at runtime.

#### Method 2: Using the Admin UI

1. Log in as an admin
2. Navigate to **Departments** → **Add Department**
3. Fill in name, abbreviation, description
4. Navigate to **Teams** → **Add Team** → assign to a department

### Onboarding Managers & Agents

1. Admin generates an **auth code** (valid 10 minutes) from the sidebar
2. Manager/Agent registers at `/register` with the auth code, selecting their role and department

### Onboarding Requesters

Requesters self-register at `/register` — no auth code needed.

---

## Ticket Workflow

### Creating a Ticket

1. Log in → click **New Ticket**
2. Fill in title, team, priority, description
3. Click **Create Ticket**

### Ticket Reference ID Format

```
{DEPT_ABBREV}TKTREQ{SEQUENCE_NUMBER}{DDMMYY}
```
Example: `HRTKTREQ001150326` (HR ticket #1, created March 15, 2026)

### Status Flow

```
NEW → OPEN → PENDING / ON_HOLD → SOLVED → CLOSED
```

| Status | Description |
|---|---|
| **New** | Just created, not yet viewed by agent |
| **Open** | Agent is actively working on it |
| **Pending** | Waiting for requester response |
| **On Hold** | Paused (awaiting external action) |
| **Solved** | Resolved, awaiting requester confirmation |
| **Closed** | Fully resolved and closed |

---

## SLA Management

### Metrics Tracked

| Metric | Description |
|---|---|
| **First Reply Time** | Time until agent's first response |
| **Next Reply Time** | Time until next response after requester message |
| **Resolution Time** | Total time to resolve the ticket |
| **Requester Wait Time** | Total time requester waits |
| **Agent Work Time** | Time agent actively works (pauses on hold) |

### Policy Matching Priority

1. Team-specific policy
2. Department-specific policy
3. Conditions-based policy
4. System default policy (defined in `backend/org_config.py`)

Configure custom SLA policies from the admin sidebar under **SLA Policies**.

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/accounts/register/` | Register a new user |
| POST | `/api/accounts/login/` | Login and receive auth token |
| GET | `/api/accounts/profile/` | Get current user profile |
| PATCH | `/api/accounts/profile/` | Update current user profile |
| POST | `/api/accounts/change-password/` | Change password |

### Tickets

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/servicedesk/tickets/` | List tickets |
| POST | `/api/servicedesk/tickets/` | Create ticket |
| GET | `/api/servicedesk/tickets/{id}/` | Get ticket details |
| PATCH | `/api/servicedesk/tickets/{id}/` | Update ticket |
| GET | `/api/servicedesk/tickets/{id}/responses/` | Get ticket messages |
| POST | `/api/servicedesk/tickets/{id}/responses/` | Add message |
| POST | `/api/servicedesk/auto-assign/` | Auto-assign unassigned tickets |

### Departments & Teams

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/teams/departments/` | List departments |
| POST | `/api/teams/departments/` | Create department |
| GET | `/api/teams/` | List teams |
| POST | `/api/teams/` | Create team |

### Notifications

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/notifications/` | List notifications |
| POST | `/api/notifications/{id}/mark-read/` | Mark as read |
| POST | `/api/notifications/mark-all-read/` | Mark all as read |

### SLA

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/servicedesk/sla-policies/` | List SLA policies |
| POST | `/api/servicedesk/sla-policies/` | Create SLA policy |
| GET | `/api/servicedesk/sla-dashboard/` | SLA compliance statistics |

---

## Screenshots

### Authentication
![Login Page](screenshots/login.png)
![Registration Page](screenshots/register.png)

### Dashboard
![Admin Dashboard](screenshots/dashboard-admin.png)
![Agent Dashboard](screenshots/dashboard-agent.png)
![Requester Dashboard](screenshots/dashboard-requester.png)

### Ticket Management
![Ticket List](screenshots/ticket-list.png)
![Create Ticket](screenshots/create-ticket.png)
![Ticket Detail](screenshots/ticket-detail.png)

### Organization Management
![Departments](screenshots/departments.png)
![Teams](screenshots/teams.png)

### SLA & Analytics
![SLA Policies](screenshots/sla-policies.png)
![SLA Dashboard](screenshots/sla-dashboard.png)
![Analytics Overview](screenshots/analytics.png)

---

## Production Notes

### Media Files

Railway's filesystem is **ephemeral** — files uploaded during runtime are lost on each deploy. For production media (user avatars, ticket attachments), consider:
- **AWS S3** + `django-storages`
- **Cloudinary**
- **Railway Volume** (persistent disk)

### WebSockets

The app uses Django Channels for real-time ticket chat. Gunicorn + Uvicorn ASGI workers support WebSockets natively. The channel layer is currently using in-memory backend — for multi-worker setups, switch to **Redis**:

```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [config('REDIS_URL')],
        },
    },
}
```

Railway offers a managed Redis add-on for this.

### Custom Domain

In Railway: Service → **Settings** → **Networking** → **Custom Domain**. Update `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` accordingly.

---

## Troubleshooting

### "CORS error" in browser console
- Ensure `CORS_ALLOWED_ORIGINS` on the backend includes your exact frontend URL (with `https://`)
- Ensure `CSRF_TRUSTED_ORIGINS` matches too

### "DisallowedHost" error
- Add your domain to `ALLOWED_HOSTS` env var
- Railway auto-provides `RAILWAY_PUBLIC_DOMAIN` which settings.py picks up

### Frontend shows "Network Error"
- Check that `VITE_API_URL` is set correctly on the frontend service
- Must include `/api` at the end (e.g. `https://backend.up.railway.app/api`)
- After changing, trigger a **redeploy** (VITE_ vars are baked at build time)

### Migrations fail on deploy
- Check the deploy logs in Railway dashboard
- Ensure `DATABASE_URL` is referenced from the Postgres service

---

## License

This project is proprietary software. All rights reserved.

---

## Support

For issues and feature requests, please contact the development team.

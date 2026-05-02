# Helper.ai 🤖

Intelligent study assistant — AI-powered PPT, Reports, Smart Notes with real-time collaboration.

## Tech Stack
- **Backend**: Python · Flask · Flask-SocketIO · Flask-SQLAlchemy · Flask-Bcrypt
- **Content Engine**: Sanity + GROQ queries
- **Database**: SQLite (dev) — swap to PostgreSQL / Neon for production
- **API**: GROQ / Sanity for content queries
- **Real-time**: Socket.IO (WebSockets)
- **Frontend**: Vanilla JS · HTML · CSS (no framework needed)

## Project Structure
```
helperai/
├── app.py            ← Flask app, routes, Socket.IO events
├── db.py             ← SQLAlchemy models (User, Document, SharedDocument)
├── ai_engine.py      ← GROQ-powered generation helpers (PPT / Report / Notes)
├── groq_client.py    ← GROQ/Sanity query helper
├── requirements.txt
├── .env/             ← local environment variables (Vercel-style deploy config)
├── templates/
│   ├── index.html    ← Landing page
│   ├── login.html    ← Auth page (login + register tabs)
│   └── dashboard.html← Main app
└── static/
    ├── css/style.css ← Full stylesheet (dark mode included)
    └── js/app.js     ← All frontend logic + Socket.IO client
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure GROQ / Sanity credentials
```bash
# Linux / macOS
export GROQ_PROJECT_ID=your_project_id
export GROQ_DATASET=production
export GROQ_API_TOKEN=your_sanity_api_token

# Windows PowerShell
$env:GROQ_PROJECT_ID="your_project_id"
$env:GROQ_DATASET="production"
$env:GROQ_API_TOKEN="your_sanity_api_token"
```

Get your token from your Sanity project settings.

### 3. Run the app
```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Features
| Feature | Status |
|---------|--------|
| User registration & login (bcrypt) | ✅ |
| Auto PPT Maker (8-12 slides + notes) | ✅ |
| Report Generator (7 sections) | ✅ |
| Smart Notes + Flashcards | ✅ |
| Voice input (Web Speech API) | ✅ |
| Real-time collaborative editing | ✅ |
| Private / encrypted documents | ✅ |
| Shareable document links | ✅ |
| Cloud file management | ✅ |
| Dark mode (auto) | ✅ |
| Mobile responsive | ✅ |

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `helperai-secret-2025` | Flask session secret — change in production! |
| `DATABASE_URL` | *(recommended)* | PostgreSQL / Neon connection string, e.g. `postgresql://user:pass@host:port/dbname` |
| `NEON_DATABASE_URL` | *(optional)* | Neon SQL connection string (dashboard links are not valid) |
| `GROQ_PROJECT_ID` | *(required for GROQ)* | Sanity project slug |
| `GROQ_DATASET` | `production` | Sanity dataset name |
| `GROQ_API_TOKEN` | *(required for private GROQ queries)* | Sanity API token |

## Production Deployment
1. Set `DATABASE_URL` or `NEON_DATABASE_URL` to a Neon/PostgreSQL URL.
2. Configure Vercel environment variables for `SECRET_KEY`, `GROQ_PROJECT_ID`, `GROQ_DATASET`, and `GROQ_API_TOKEN`.
3. Deploy with Vercel using `vercel deploy`.
4. Note: Socket.IO realtime features are not fully supported on Vercel serverless functions, so use a compatible host for real-time collaboration if needed.

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Create account |
| POST | `/api/login` | Sign in |
| POST | `/api/logout` | Sign out |
| GET  | `/api/me` | Current user info |
| POST | `/api/generate/ppt` | Generate presentation |
| POST | `/api/generate/report` | Generate report |
| POST | `/api/generate/notes` | Generate smart notes |
| GET  | `/api/documents` | List user documents |
| GET  | `/api/documents/:id` | Get single document |
| POST | `/api/documents/:id/share` | Create share link |
| DELETE | `/api/documents/:id` | Delete document |
| GET  | `/shared/:token` | View shared document |

## Socket.IO Events
| Event | Direction | Description |
|-------|-----------|-------------|
| `join_room` | Client → Server | Join collaboration room |
| `leave_room` | Client → Server | Leave room |
| `note_update` | Client → Server | Broadcast note changes |
| `note_changed` | Server → Client | Receive note changes |
| `user_joined` | Server → Client | Someone joined room |
| `user_left` | Server → Client | Someone left room |

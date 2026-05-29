# Omni DJ website backend

Tiny Flask service that powers `/api/contact` and `/api/beta-signup` for omnidj.com.

## Local dev

```
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env
python app.py
```

Serves on `http://127.0.0.1:5556` by default.

Health probe: `curl http://127.0.0.1:5556/api/health`.

## Production

Deploy to Fly.io, Railway, or any small VM. Example with gunicorn:

```
gunicorn -w 2 -b 0.0.0.0:5556 app:app
```

Put it behind nginx or Cloudflare on `api.omnidj.com`. Add to Cloudflare:
- CNAME `api` → your hosting target
- Proxy enabled (orange cloud) for TLS termination

## How the frontend reaches it

The Next.js site posts to relative paths `/api/contact` and `/api/beta-signup`. In production, configure your Cloudflare Pages → Workers/redirects (or nginx) to forward `/api/*` from `omnidj.com` to `api.omnidj.com`.

## Data

SQLite at `backend/data/omnidj.db`. Two tables: `beta_signups` (idempotent on email) and `contact_messages`.

To migrate to Postgres later, swap out `sqlite3` calls in `routes/*.py` for SQLAlchemy / asyncpg.

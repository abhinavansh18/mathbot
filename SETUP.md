# MathBot — Windows Setup & Deployment Guide

This guide walks you through running MathBot on **Windows**, step by step.
No experience with Docker or terminal required — just follow the steps in order.

---

## Part 1 — What You Need First

Before you start, install these four things.
Each one has a download link and takes about 5 minutes.

---

### Step 1 — Install Docker Desktop

Docker lets you run the whole application (database, cache, API) in containers
so you don't have to install PostgreSQL or Redis separately.

1. Go to: https://www.docker.com/products/docker-desktop/
2. Click **Download for Windows**
3. Run the installer (accept all defaults)
4. After install, open **Docker Desktop** from your Start menu
5. Wait until you see the green "Engine running" status in the bottom left
6. Leave Docker Desktop open — it needs to stay running

---

### Step 2 — Install Git

Git is needed to download the project code.

1. Go to: https://git-scm.com/download/win
2. Download and run the installer (accept all defaults)
3. To check it worked: open **Command Prompt** and type:
   ```
   git --version
   ```
   You should see something like `git version 2.45.0`

---

### Step 3 — Install Python 3.11

Python is needed to run tests locally (the API itself runs inside Docker).

1. Go to: https://www.python.org/downloads/
2. Download **Python 3.11.x** (not 3.12 — use 3.11 for best compatibility)
3. Run the installer
4. ⚠️ **Important:** On the first screen, tick the box that says **"Add Python to PATH"**
5. Click Install Now
6. To check it worked:
   ```
   python --version
   ```
   You should see `Python 3.11.x`

---

### Step 4 — Get a Free Groq API Key

MathBot uses Groq to run the AI (it's free).

1. Go to: https://console.groq.com
2. Sign up for a free account
3. Click **API Keys** in the left sidebar
4. Click **Create API Key**
5. Copy the key — it looks like: `gsk_abc123...`
6. Keep this key safe — you'll need it in the next section

---

## Part 2 — Setting Up the Project

Open **Command Prompt** (press `Windows key`, type `cmd`, press Enter).
Run these commands one at a time:

---

### Step 5 — Download the project

```cmd
git clone https://github.com/yourusername/mathbot.git
cd mathbot
```

You should now be inside the `mathbot` folder.

---

### Step 6 — Create your settings file

```cmd
copy .env.example .env
```

Now open the `.env` file with Notepad:
```cmd
notepad .env
```

Find this line:
```
GROQ_API_KEY=your_groq_api_key_here
```

Replace `your_groq_api_key_here` with the Groq API key you copied in Step 4.

Also find this line:
```
SECRET_KEY=change_me_to_a_random_64_char_hex_string
```

Replace it with a random secret. You can generate one by running:
```cmd
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy that output and paste it as the SECRET_KEY value.

Save the file (Ctrl+S) and close Notepad.

---

## Part 3 — Running the Application

### Step 7 — Start everything with Docker

In your Command Prompt (still inside the `mathbot` folder):
```cmd
docker compose up --build
```

The first time this runs, it will download Docker images and install dependencies.
This can take **5–10 minutes**. You'll see a lot of text scrolling by — that's normal.

When you see lines like:
```
api  | INFO:     Application startup complete.
```
...the server is ready.

---

### Step 8 — Open the app

Open your browser and go to:
```
http://localhost:8000/docs
```

You'll see the **interactive API documentation** — this is where you can test every endpoint.

---

### Step 9 — Create an account and test it

In the browser at `http://localhost:8000/docs`:

1. Click on **POST /api/v1/auth/register**
2. Click **Try it out**
3. Fill in:
   ```json
   {
     "email": "test@example.com",
     "password": "mypassword123",
     "username": "testuser"
   }
   ```
4. Click **Execute**
5. Copy the `access_token` from the response

Now test the solver:
1. Click the green **Authorize** button at the top of the page
2. Paste your token and click Authorize
3. Click on **POST /api/v1/solve**
4. Click **Try it out**
5. Enter:
   ```json
   {
     "query": "What is 2 + 2?",
     "show_steps": true
   }
   ```
6. Click **Execute** — you should get the answer back!

---

## Part 4 — Running Tests

Open a **new** Command Prompt window (keep the Docker one running).
Navigate back to the project:
```cmd
cd mathbot
```

Install test dependencies:
```cmd
pip install -r requirements.txt
```

Run the tests:
```cmd
pytest tests/unit/ -v
```

You should see green dots and a summary like:
```
========================= 15 passed in 3.41s =========================
```

Run all tests including integration tests (requires Docker to be running):
```cmd
pytest tests/ -v
```

---

## Part 5 — Stopping the Application

To stop MathBot:
1. Go back to the Command Prompt where Docker is running
2. Press **Ctrl+C**
3. Type:
   ```cmd
   docker compose down
   ```

This stops all containers. Your data is saved in Docker volumes and will be there next time.

To start again later:
```cmd
docker compose up
```

(No `--build` needed unless you changed code)

---

## Part 6 — Making Code Changes

If you edit any Python file:

1. Stop the application (Ctrl+C, then `docker compose down`)
2. Start it again:
   ```cmd
   docker compose up --build
   ```

The `--build` flag rebuilds the Docker image with your changes.

During development, the API container mounts your local files directly, so Python changes to the `api/`, `agents/`, `services/`, etc. folders will hot-reload automatically without a full rebuild.

---

## Part 7 — Deploying to Production

When you're ready to share MathBot publicly, here are three options from easiest to most powerful.

---

### Option A — Railway (Easiest, Free Tier Available)

Railway lets you deploy Docker Compose apps directly from GitHub with one click.

1. Push your code to GitHub:
   ```cmd
   git add .
   git commit -m "Initial production setup"
   git push origin main
   ```

2. Go to: https://railway.app
3. Click **New Project** → **Deploy from GitHub repo**
4. Select your `mathbot` repository
5. Railway detects `docker-compose.yml` automatically
6. Click **Add Variables** and add:
   - `GROQ_API_KEY` = your Groq API key
   - `SECRET_KEY` = your random secret key
7. Click **Deploy**
8. Railway gives you a public URL like `https://mathbot-production.up.railway.app`

---

### Option B — Render (Free Tier, Good for APIs)

1. Go to: https://render.com
2. Create a new **Web Service**
3. Connect your GitHub repository
4. Set:
   - **Runtime:** Docker
   - **Dockerfile:** `docker/Dockerfile.api`
5. Add environment variables (same as above)
6. Add a **PostgreSQL** database from the Render dashboard
7. Add a **Redis** instance from the Render dashboard
8. Update `DATABASE_URL` and `REDIS_URL` with the Render-provided connection strings
9. Click **Deploy**

---

### Option C — Your Own Server (Full Control)

If you have a VPS (e.g., DigitalOcean Droplet, AWS EC2):

1. SSH into your server
2. Install Docker:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
3. Clone your repo:
   ```bash
   git clone https://github.com/yourusername/mathbot.git
   cd mathbot
   ```
4. Create `.env` with your production values
5. For production, change `APP_ENV=production` and `DEBUG=false` in `.env`
6. Start:
   ```bash
   docker compose up -d
   ```
   The `-d` flag runs everything in the background (detached mode)
7. Your API is now at `http://your-server-ip:80`

---

## Troubleshooting

### "Docker is not running"
Open Docker Desktop from the Start menu and wait for "Engine running" status.

### "Port 8000 is already in use"
Something else is using port 8000. Either stop that program, or edit `docker-compose.yml`
and change `"8000:8000"` to `"8001:8000"` then access at `http://localhost:8001/docs`.

### "GROQ_API_KEY is missing"
Check your `.env` file. Make sure the line reads exactly:
```
GROQ_API_KEY=gsk_yourkeyherenospacesaroundtheequals
```

### Tests fail with "connection refused"
The integration tests need Docker running. Start Docker Desktop first, then run:
```cmd
docker compose up -d
pytest tests/ -v
```

### "pip is not recognised"
Python wasn't added to PATH. Re-run the Python installer, choose **Modify**, and tick
**Add Python to environment variables**.

### Containers won't start / database errors
Try a clean restart:
```cmd
docker compose down -v
docker compose up --build
```
The `-v` removes stored data and starts fresh.

---

## File Reference

| File | What it does |
|---|---|
| `.env` | Your private settings (API keys, passwords) |
| `docker-compose.yml` | Defines all services (API, DB, Redis, etc.) |
| `main.py` | FastAPI app entry point |
| `requirements.txt` | Python packages |
| `pyproject.toml` | Project config + tool settings |
| `Makefile` | Shortcut commands (needs GNU Make) |

---

## Getting Help

- **API not responding?** Check `docker compose logs api`
- **Database error?** Check `docker compose logs db`
- **Redis error?** Check `docker compose logs redis`

View all logs at once:
```cmd
docker compose logs
```

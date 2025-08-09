# Kotak Neo Signal - Render Deployment Guide

## Steps
1. Create a new GitHub repo and push these files to it (or drag & drop in Render via Git integration).
2. Sign in to https://render.com and create a new **Web Service**.
   - Connect your GitHub repo and choose the branch to deploy from.
   - Set the **Build Command** to `pip install -r requirements.txt` (Render auto-detects for Python).
   - Set the **Start Command** to `gunicorn main:app --bind 0.0.0.0:$PORT --workers 1` (Procfile included).
3. In Render dashboard, go to **Environment** and add the variables from `.env.example` (DO NOT commit real keys to GitHub).
4. Deploy. Render will build and provide a public URL.
5. Open the URL on mobile and choose "Add to Home Screen" to install the PWA.

## Notes & Troubleshooting
- The Kotak Neo SDK may expose different method and class names. If `main.py` raises import errors, check the SDK README for the correct import path and login method names, then update `main.py` accordingly.
- For automatic login you must enable TOTP for your Kotak Neo account and provide `TOTP_SECRET`.
- If auto-login fails, check Render logs for errors and paste them here; I can help patch `main.py`.

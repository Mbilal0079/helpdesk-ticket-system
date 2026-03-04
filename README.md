# Helpdesk Ticket System

A simple Helpdesk Ticket Management System built using Python Flask.

## Features
- Create and view support tickets
- Unique Ticket ID for each submission
- Ticket priority: Low / Medium / High
- Ticket status: Open / Closed
- Close tickets with a button
- Styled UI with CSS and smooth transitions

## Tech Stack
- Python 3.x
- Flask
- HTML/CSS

## How to Run Locally
```bash
pip install -r requirements.txt
python app.py
```

## Deploy Live (Free with GitHub Student Developer Pack)

This app is ready to deploy on several platforms that offer free tiers or credits through the [GitHub Student Developer Pack](https://education.github.com/pack).

### Option 1: Deploy to Render (Free Tier)

1. Push this repo to your GitHub account.
2. Go to [Render](https://render.com) and sign up with your GitHub account.
3. Click **New → Web Service** and connect your repository.
4. Render will auto-detect the `render.yaml` configuration.
5. Click **Create Web Service** — your app will be live in minutes.

> Render's free tier keeps your app running with no credit card required.

### Option 2: Deploy to Railway (Free Credits with Student Pack)

1. Go to [Railway](https://railway.app) and sign in with GitHub.
2. Activate your free credits via the [Student Developer Pack](https://education.github.com/pack).
3. Click **New Project → Deploy from GitHub Repo** and select this repo.
4. Add the environment variable `SECRET_KEY` with a random string in the **Variables** tab.
5. Railway will auto-detect the `Procfile` and deploy your app.

### Option 3: Deploy to Heroku (Free Credits with Student Pack)

1. Go to [Heroku](https://heroku.com) and create an account.
2. Activate your Heroku credits via the [Student Developer Pack](https://education.github.com/pack).
3. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) and run:
   ```bash
   heroku login
   heroku create my-helpdesk-app
   heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   git push heroku main
   ```

### Environment Variables

| Variable     | Description                  | Required |
|-------------|------------------------------|----------|
| `SECRET_KEY` | Flask session secret key     | Yes (for production) |
| `PORT`       | Port to listen on (auto-set) | No       |
| `FLASK_ENV`  | Set to `production` for prod | No       |

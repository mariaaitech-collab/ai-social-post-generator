# AI Social Post Generator
> Writes a ready-to-post update for LinkedIn, Facebook or Instagram from a single topic, then publishes it for you.

![language](https://img.shields.io/badge/language-Python-4338CA?style=flat-square&logo=python&logoColor=white) ![framework](https://img.shields.io/badge/framework-FastAPI_%2B_React-4338CA?style=flat-square&logo=fastapi&logoColor=white) ![license](https://img.shields.io/badge/license-MIT-6366F1?style=flat-square) ![status](https://img.shields.io/badge/status-in_progress-818CF8?style=flat-square)

## Overview
Small businesses and creators need to post often, but writing a different version for every platform takes time. You type a topic, pick a platform, and the app writes a post in that platform's style (hook, body, call to action, hashtags) using Google Gemini. You can then publish it to your connected account in one click.

## Features
- AI post writing with Google Gemini, with a separate style guide for LinkedIn, Facebook and Instagram
- Connect LinkedIn, Facebook Pages and Instagram through each platform's OAuth sign-in
- One-click publishing to LinkedIn, a Facebook Page, or Instagram (with an image URL)
- Connection status and a disconnect button for each platform
- Manual access-token entry as a fallback when OAuth isn't set up
- Cleans AI output by stripping markdown and filler lines before posting

## Tech Stack
| Layer | Technology | Version |
|---|---|---|
| Backend | FastAPI + Pydantic | - |
| HTTP client | httpx | - |
| AI | google-generativeai (Gemini) | - |
| Config | python-dotenv | - |
| Frontend | React | 19.2 |
| Build | Vite | 8.1 |
| HTTP client | Axios | 1.18 |

## Screenshots
<!-- Maria: add screenshots here -->

## Getting Started
**Prerequisites:** Python 3.10+, Node.js 20+, a Gemini API key, and developer apps on LinkedIn and/or Meta.

```bash
git clone https://github.com/mariaaitech-collab/ai-social-post-generator.git
cd ai-social-post-generator

# Backend
cd backend
pip install fastapi uvicorn httpx google-generativeai python-dotenv
# create backend/.env with: GEMINI_API_KEY, LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET,
#   FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FRONTEND_URL, BACKEND_URL
uvicorn app.main:app --reload          # http://localhost:8000

# Frontend (new terminal)
cd ../client
npm install
npm run dev                            # http://localhost:5173
```

## Status
**In progress.** Generating and posting both work from `backend/app/main.py`. Still to do:
- Fill in `requirements.txt`, which is currently empty.
- Move the logic into the router, service and model modules that are already scaffolded but empty.
- Make the API URL configurable instead of hardcoded to `localhost:8000`.
- Deploy.

---
Built by Maria Shafqat · [Linktree](https://linktr.ee/mariashafqat_)

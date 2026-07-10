import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
FRONTEND_URL = "http://localhost:5173"
BACKEND_URL = "http://localhost:8000"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("GEMINI_API_KEY loaded")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

TOKENS_FILE = os.path.join(os.path.dirname(__file__), "tokens.json")

def load_tokens():
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tokens(data):
    with open(TOKENS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class ContentRequest(BaseModel):
    prompt: str
    platform: str

class PostRequest(BaseModel):
    content: str
    image_url: str = ""

@app.get("/config")
async def get_config():
    return {
        "linkedin": bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET),
        "facebook": False,
        "instagram": False,
    }

@app.get("/status")
async def get_status():
    tokens = load_tokens()
    return {
        "linkedin": bool(tokens.get("linkedin", {}).get("access_token")),
        "facebook": False,
        "instagram": False,
    }

@app.post("/disconnect/linkedin")
async def disconnect():
    tokens = load_tokens()
    tokens.pop("linkedin", None)
    save_tokens(tokens)
    return {"message": "linkedin disconnected"}

@app.get("/auth/linkedin")
async def linkedin_auth():
    if not LINKEDIN_CLIENT_ID:
        raise HTTPException(400, "LinkedIn not configured")
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": f"{BACKEND_URL}/auth/linkedin/callback",
        "scope": "w_member_social openid profile email",
        "state": "linkedin",
    }
    url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return RedirectResponse(url)

@app.get("/auth/linkedin/callback")
async def linkedin_callback(code: str = None, error: str = None):
    if error:
        return RedirectResponse(f"{FRONTEND_URL}/?error=linkedin:{error}")
    if not code:
        return RedirectResponse(f"{FRONTEND_URL}/?error=linkedin:no_code")
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{BACKEND_URL}/auth/linkedin/callback",
                "client_id": LINKEDIN_CLIENT_ID,
                "client_secret": LINKEDIN_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_data = token_res.json()
        if "access_token" not in token_data:
            return RedirectResponse(f"{FRONTEND_URL}/?error=linkedin:token_failed")
        access_token = token_data["access_token"]
        me_res = await client.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        person_id = me_res.json().get("sub", "")
        tokens = load_tokens()
        tokens["linkedin"] = {"access_token": access_token, "person_id": person_id}
        save_tokens(tokens)
    return RedirectResponse(f"{FRONTEND_URL}/?connected=linkedin")

@app.post("/post/linkedin")
async def post_linkedin(data: PostRequest):
    tokens = load_tokens()
    li = tokens.get("linkedin", {})
    if not li.get("access_token"):
        raise HTTPException(400, "LinkedIn not connected")
    person_urn = f"urn:li:person:{li['person_id']}"
    post_body = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": data.content},
                "shareMediaCategory": "ARTICLE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.linkedin.com/v2/ugcPosts",
            json=post_body,
            headers={
                "Authorization": f"Bearer {li['access_token']}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        if res.status_code == 201:
            return {"success": True, "message": "Posted to LinkedIn!"}
        else:
            raise HTTPException(res.status_code, f"LinkedIn error: {res.text}")

@app.post("/generate")
async def generate(data: ContentRequest):
    if not GEMINI_API_KEY:
        return {"content": "Error: GEMINI_API_KEY nahi mili."}
    try:
        instruction = f"You are an expert social media manager. Write a highly engaging post for {data.platform}. CRITICAL RULE: You must ONLY use well-known, 100% verified facts. Do NOT make up statistics, fake quotes, imaginary case studies, or false information."
        if data.platform == "LinkedIn":
            instruction += " Keep it professional, insightful, use bullet points, and add 2-3 professional hashtags."
        elif data.platform == "Instagram":
            instruction += " Make it fun, visually descriptive, use a lot of emojis, and add trending hashtags."
        elif data.platform == "Facebook":
            instruction += " Make it conversational, engaging, ask a question to get more comments, and use few emojis."
        final_prompt = f"{instruction}\n\nHere is the topic: {data.prompt}"
        model_names = ["gemini-2.5-flash", "gemini-2.5-pro"]
        last_error = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(final_prompt)
                if response and response.text:
                    return {"content": response.text}
            except Exception as model_error:
                last_error = model_error
                continue
        return {"content": f"Error: {str(last_error)}"}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}
import os
import json
import httpx
import re
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

FB_API_VERSION = "v22.0"

print("=" * 60)
print(f"FACEBOOK_APP_ID: {'SET' if FACEBOOK_APP_ID else 'NOT SET'}")
print(f"LINKEDIN_CLIENT_ID: {'SET' if LINKEDIN_CLIENT_ID else 'NOT SET'}")
print(f"BACKEND_URL: {BACKEND_URL}")
print(f"FRONTEND_URL: {FRONTEND_URL}")
print("=" * 60)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("GEMINI_API_KEY loaded")

app = FastAPI()
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"],
    allow_credentials=True,
)

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

class ManualTokenRequest(BaseModel):
    platform: str
    token: str
    page_id: str = ""
    ig_user_id: str = ""
    username: str = ""

# ===================== CONFIG & STATUS =====================

@app.get("/config")
async def get_config():
    return {
        "linkedin": bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET),
        "facebook": bool(FACEBOOK_APP_ID and FACEBOOK_APP_SECRET),
        "instagram": bool(FACEBOOK_APP_ID and FACEBOOK_APP_SECRET),
    }

@app.get("/status")
async def get_status():
    tokens = load_tokens()
    return {
        "linkedin": bool(tokens.get("linkedin", {}).get("access_token")),
        "facebook": bool(tokens.get("facebook", {}).get("page_token")),
        "instagram": bool(tokens.get("instagram", {}).get("ig_user_id")),
    }

@app.post("/disconnect/{platform}")
async def disconnect(platform: str):
    tokens = load_tokens()
    tokens.pop(platform, None)
    save_tokens(tokens)
    return {"message": f"{platform} disconnected"}

# ===================== DEBUG ENDPOINTS =====================

@app.get("/debug/instagram")
async def debug_instagram():
    tokens = load_tokens()
    ig = tokens.get("instagram", {})
    access_token = ig.get("access_token", "")
    
    if not access_token:
        return {"error": "No Instagram token found. Connect Instagram first."}
    
    async with httpx.AsyncClient() as client:
        token_debug = await client.get(
            f"https://graph.facebook.com/{FB_API_VERSION}/debug_token",
            params={"input_token": access_token, "access_token": f"{FACEBOOK_APP_ID}|{FACEBOOK_APP_SECRET}"}
        )
        
        accounts = await client.get(
            f"https://graph.facebook.com/{FB_API_VERSION}/me/accounts",
            params={"access_token": access_token, "fields": "id,name,access_token,instagram_business_account,connected_instagram_account"}
        )
        
        ig_info = {}
        if ig.get("ig_user_id"):
            ig_info = await client.get(
                f"https://graph.facebook.com/{FB_API_VERSION}/{ig['ig_user_id']}",
                params={"access_token": access_token, "fields": "id,username,name"}
            )
    
    return {
        "token_debug": token_debug.json(),
        "accounts": accounts.json(),
        "ig_account_info": ig_info.json() if ig_info else None,
        "saved_tokens": {k: v for k, v in ig.items() if k != "access_token"}
    }

@app.post("/manual-token")
async def manual_token(data: ManualTokenRequest):
    tokens = load_tokens()
    
    if data.platform == "instagram":
        tokens["instagram"] = {
            "access_token": data.token,
            "ig_user_id": data.ig_user_id,
            "username": data.username or "manual",
        }
    elif data.platform == "facebook":
        tokens["facebook"] = {
            "page_token": data.token,
            "page_id": data.page_id,
        }
    elif data.platform == "linkedin":
        tokens["linkedin"] = {
            "access_token": data.token,
            "person_id": data.page_id or "",
        }
    
    save_tokens(tokens)
    return {"success": True, "message": f"{data.platform} token saved manually"}

# ===================== LINKEDIN OAUTH =====================

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
    try:
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
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            person_id = me_res.json().get("sub", "")
            tokens = load_tokens()
            tokens["linkedin"] = {"access_token": access_token, "person_id": person_id}
            save_tokens(tokens)
        return RedirectResponse(f"{FRONTEND_URL}/?connected=linkedin")
    except Exception as e:
        return RedirectResponse(f"{FRONTEND_URL}/?error=linkedin:exception:{str(e)}")

# ===================== FACEBOOK OAUTH =====================

@app.get("/auth/facebook")
async def facebook_auth():
    if not FACEBOOK_APP_ID:
        raise HTTPException(400, "Facebook App ID not configured")
    params = {
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": f"{BACKEND_URL}/auth/facebook/callback",
        "scope": "email,pages_read_engagement,pages_manage_posts",
        "response_type": "code",
        "state": "facebook",
    }
    url = f"https://www.facebook.com/{FB_API_VERSION}/dialog/oauth?{urlencode(params)}"
    return RedirectResponse(url)

@app.get("/auth/facebook/callback")
async def facebook_callback(code: str = None, error: str = None, error_code: str = None, error_description: str = None):
    if error:
        err_msg = f"facebook:{error}"
        if error_description:
            err_msg += f":{error_description}"
        return RedirectResponse(f"{FRONTEND_URL}/?error={err_msg}")
    if not code:
        return RedirectResponse(f"{FRONTEND_URL}/?error=facebook:no_code")

    try:
        async with httpx.AsyncClient() as client:
            token_res = await client.get(
                f"https://graph.facebook.com/{FB_API_VERSION}/oauth/access_token",
                params={
                    "client_id": FACEBOOK_APP_ID,
                    "client_secret": FACEBOOK_APP_SECRET,
                    "redirect_uri": f"{BACKEND_URL}/auth/facebook/callback",
                    "code": code,
                },
            )
            token_data = token_res.json()

            if "access_token" not in token_data:
                error_msg = token_data.get("error", {}).get("message", str(token_data))
                return RedirectResponse(f"{FRONTEND_URL}/?error=facebook:token_failed:{error_msg}")

            user_access_token = token_data["access_token"]

            pages_res = await client.get(
                f"https://graph.facebook.com/{FB_API_VERSION}/me/accounts",
                params={
                    "access_token": user_access_token,
                    "fields": "id,name,access_token",
                },
            )
            pages_data = pages_res.json()

            if "data" not in pages_data or len(pages_data["data"]) == 0:
                return RedirectResponse(f"{FRONTEND_URL}/?error=facebook:no_pages_found:App is in Development mode. Use Manual Token instead!")

            page = pages_data["data"][0]
            page_id = page.get("id", "")
            page_token = page.get("access_token", "")

            tokens = load_tokens()
            tokens["facebook"] = {
                "page_token": page_token,
                "page_id": page_id,
            }
            save_tokens(tokens)

        return RedirectResponse(f"{FRONTEND_URL}/?connected=facebook")
    except Exception as e:
        return RedirectResponse(f"{FRONTEND_URL}/?error=facebook:exception:{str(e)}")

# ===================== INSTAGRAM OAUTH =====================

@app.get("/auth/instagram")
async def instagram_auth():
    if not FACEBOOK_APP_ID:
        raise HTTPException(400, "Facebook App ID not configured")
    params = {
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": f"{BACKEND_URL}/auth/instagram/callback",
        "scope": "instagram_basic,instagram_content_publish,pages_read_engagement",
        "response_type": "code",
        "state": "instagram",
    }
    url = f"https://www.facebook.com/{FB_API_VERSION}/dialog/oauth?{urlencode(params)}"
    return RedirectResponse(url)

@app.get("/auth/instagram/callback")
async def instagram_callback(code: str = None, error: str = None, error_code: str = None, error_description: str = None):
    if error:
        err_msg = f"instagram:{error}"
        if error_description:
            err_msg += f":{error_description}"
        return RedirectResponse(f"{FRONTEND_URL}/?error={err_msg}")
    if not code:
        return RedirectResponse(f"{FRONTEND_URL}/?error=instagram:no_code")

    try:
        async with httpx.AsyncClient() as client:
            token_res = await client.get(
                f"https://graph.facebook.com/{FB_API_VERSION}/oauth/access_token",
                params={
                    "client_id": FACEBOOK_APP_ID,
                    "client_secret": FACEBOOK_APP_SECRET,
                    "redirect_uri": f"{BACKEND_URL}/auth/instagram/callback",
                    "code": code,
                },
            )
            token_data = token_res.json()

            if "access_token" not in token_data:
                error_msg = token_data.get("error", {}).get("message", str(token_data))
                return RedirectResponse(f"{FRONTEND_URL}/?error=instagram:token_failed:{error_msg}")

            user_access_token = token_data["access_token"]

            pages_res = await client.get(
                f"https://graph.facebook.com/{FB_API_VERSION}/me/accounts",
                params={
                    "access_token": user_access_token,
                    "fields": "id,name,access_token,instagram_business_account{id,username},connected_instagram_account",
                },
            )
            pages_data = pages_res.json()

            ig_user_id = ""
            ig_page_token = ""
            ig_username = ""

            if "data" in pages_data and len(pages_data["data"]) > 0:
                for page in pages_data["data"]:
                    ig_account = page.get("instagram_business_account", {})
                    if not ig_account:
                        ig_account = page.get("connected_instagram_account", {})
                    
                    if ig_account and ig_account.get("id"):
                        ig_user_id = ig_account.get("id", "")
                        ig_username = ig_account.get("username", "")
                        ig_page_token = page.get("access_token", "")
                        break

            if not ig_user_id:
                return RedirectResponse(
                    f"{FRONTEND_URL}/?error=instagram:no_business_account:Use Manual Token instead! Go to Graph API Explorer."
                )

            tokens = load_tokens()
            tokens["instagram"] = {
                "ig_user_id": ig_user_id,
                "access_token": ig_page_token or user_access_token,
                "username": ig_username,
            }
            save_tokens(tokens)

        return RedirectResponse(f"{FRONTEND_URL}/?connected=instagram")
    except Exception as e:
        return RedirectResponse(f"{FRONTEND_URL}/?error=instagram:exception:{str(e)}")

# ===================== POST ENDPOINTS =====================

@app.post("/post/linkedin")
async def post_linkedin(data: PostRequest):
    tokens = load_tokens()
    li = tokens.get("linkedin", {})
    if not li.get("access_token"):
        raise HTTPException(status_code=400, detail="LinkedIn not connected")
    person_urn = f"urn:li:person:{li['person_id']}"
    post_body = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": data.content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                json=post_body,
                headers={
                    "Authorization": f"Bearer {li['access_token']}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "LinkedIn-Version": "202604",
                },
            )
            if res.status_code == 201:
                return JSONResponse(content={"success": True, "message": "Posted to LinkedIn!"})
            else:
                try:
                    err = res.json()
                    detail = err.get("message", str(err))
                except:
                    detail = res.text
                raise HTTPException(status_code=res.status_code, detail=f"LinkedIn error: {detail}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

@app.post("/post/facebook")
async def post_facebook(data: PostRequest):
    tokens = load_tokens()
    fb = tokens.get("facebook", {})
    page_token = fb.get("page_token", "")
    page_id = fb.get("page_id", "")

    if not page_token:
        raise HTTPException(status_code=400, detail="Facebook not connected")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"https://graph.facebook.com/{FB_API_VERSION}/{page_id}/feed",
                params={"message": data.content, "access_token": page_token},
            )
            result = res.json()

            if "id" in result:
                return JSONResponse(content={"success": True, "message": f"Posted to Facebook! Post ID: {result['id']}"})
            else:
                error_msg = result.get("error", {}).get("message", str(result))
                raise HTTPException(status_code=400, detail=f"Facebook error: {error_msg}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

@app.post("/post/instagram")
async def post_instagram(data: PostRequest):
    tokens = load_tokens()
    ig = tokens.get("instagram", {})
    ig_user_id = ig.get("ig_user_id", "")
    access_token = ig.get("access_token", "")

    if not ig_user_id:
        raise HTTPException(status_code=400, detail="Instagram not connected")
    if not data.image_url:
        raise HTTPException(status_code=400, detail="Instagram requires an image URL")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            container_res = await client.post(
                f"https://graph.facebook.com/{FB_API_VERSION}/{ig_user_id}/media",
                params={"image_url": data.image_url, "caption": data.content, "access_token": access_token},
            )
            container = container_res.json()

            if "id" not in container:
                error_msg = container.get("error", {}).get("message", str(container))
                raise HTTPException(status_code=400, detail=f"Instagram container error: {error_msg}")

            publish_res = await client.post(
                f"https://graph.facebook.com/{FB_API_VERSION}/{ig_user_id}/media_publish",
                params={"creation_id": container['id'], "access_token": access_token},
            )
            result = publish_res.json()

            if "id" in result:
                return JSONResponse(content={"success": True, "message": f"Posted to Instagram! Media ID: {result['id']}"})
            else:
                error_msg = result.get("error", {}).get("message", str(result))
                raise HTTPException(status_code=400, detail=f"Instagram publish error: {error_msg}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

# ===================== GENERATE =====================

def clean_ai_output(text):
    text = text.strip()
    fluff_patterns = [
        r"^(Here is|Here\'s|Here is a|Here\'s a|Here is an|Here\'s an|Here is the|Here\'s the|Following is|Below is|This is|Post:|Caption:|Content:|Draft:)[\s:]*",
        r"^(An engaging|A professional|A creative|A compelling)[\s\w]+post[\s:]*",
        r"^\*\*.*?\*\*[\s:]*",
    ]
    for pattern in fluff_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\n?---\n?", "\n", text)
    text = re.sub(r"\n?\*\*\*\n?", "\n", text)

    lines = text.split("\n")
    clean_lines = []
    skip_block = False
    for line in lines:
        lower = line.lower()
        if any(x in lower for x in ["image suggestion", "**image", "visual suggestion", "photo idea", "image idea"]):
            skip_block = True
            continue
        if skip_block and line.strip() == "":
            skip_block = False
            continue
        if skip_block:
            continue
        clean_lines.append(line)

    text = "\n".join(clean_lines).strip()
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)

    return text.strip()

@app.post("/generate")
async def generate(data: ContentRequest):
    if not GEMINI_API_KEY:
        return {"content": "Error: GEMINI_API_KEY nahi mili."}
    try:
        topic = data.prompt.strip()
        platform = data.platform

        if platform == "LinkedIn":
            instruction = f"""You are a top-tier LinkedIn content strategist. Write a LinkedIn post about: {topic}

STRICT FORMAT:
1. HOOK (Line 1): Bold, attention-grabbing statement or question. NO fluff.
2. BODY: Short paragraphs (2-3 lines max). Personal insight or contrarian take. NO bullet points.
3. VALUE: One actionable takeaway or perspective shift.
4. CLOSING: Thought-provoking question or CTA inviting comments.
5. HASHTAGS: 3-5 professional hashtags at the end on one line.

TONE: Confident, authoritative, conversational but professional.
RULES: ONLY verified facts. NO made-up stats. NO intro lines. NO separators. NO image suggestions. Start directly with the hook."""

        elif platform == "Facebook":
            instruction = f"""You are a viral Facebook community manager. Write a Facebook post about: {topic}

STRICT FORMAT:
1. OPENING: Relatable hook — story, bold opinion, or "Did you know?" moment. Like talking to a friend.
2. BODY: Conversational, warm, short paragraphs. Mini-story or relatable scenario.
3. ENGAGEMENT: ONE direct question that sparks comments. Use "Drop a 💙 if you agree" or "Tag someone."
4. HASHTAGS: 2-3 casual hashtags at the end.

TONE: Warm, friendly, authentic, community-driven.
RULES: ONLY verified facts. NO made-up stats. NO intro lines. NO separators. NO image suggestions. Start directly with the content."""

        elif platform == "Instagram":
            instruction = f"""You are an Instagram growth strategist. Write an Instagram caption about: {topic}

STRICT FORMAT:
1. HOOK (Line 1): Bold, emotional, or curiosity-driven opening. Make people tap "...more"
2. BODY: Short punchy paragraphs (1-2 lines each). Storytelling. Relatable struggle, win, or insight.
3. CTA: Strong call-to-action — "Double tap 💯", "Save for later 📌", "Drop thoughts 👇", "Tag squad 👥"
4. HASHTAGS: 8-12 targeted hashtags on last 2-3 lines. Mix popular and niche.

TONE: Energetic, authentic, bold, slightly informal but inspiring.
RULES: ONLY verified facts. NO made-up stats. NO intro lines. NO separators. NO image suggestions. Start directly with the hook. Use emojis naturally."""

        else:
            instruction = f"Write a social media post about: {topic}"

        model_names = ["gemini-2.5-flash", "gemini-2.5-pro"]
        last_error = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(instruction)
                if response and response.text:
                    cleaned = clean_ai_output(response.text)
                    return {"content": cleaned}
            except Exception as model_error:
                last_error = model_error
                continue
        return {"content": f"Error: {str(last_error)}"}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}
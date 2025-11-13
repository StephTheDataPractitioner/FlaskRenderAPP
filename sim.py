# flask_linkedin_oauth_demo_render_ready_clean.py
"""
Render-ready demo app for LinkedIn Standard Tier review screencast.
- Stores tokens in session only (never prints them).
- Supports /preset?token=... for setting a session token (local / screencast use ONLY).
- Simulates member-level engagement, aggregate analytics, and employee advocacy.
"""

from flask import Flask, redirect, request, session
import os
import requests
from datetime import datetime, timedelta
import random
import json

now = datetime.now()
simulated_engagement = [
    {"member_id": 1, "member_name": "Alex Johnson", "title": "Data Engineer at StrictData",
     "profile_url": "/profile/1", "profile_pic": "https://via.placeholder.com/80.png?text=AJ",
     "comment": "Great post — very useful!", "reaction": "LIKE",
     "timestamp": (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M"),
     "about": "Alex is a data engineer passionate about automating analytics pipelines.",
     "recent_activity": "Commented on multiple StrictData posts about data pipelines."},
    {"member_id": 2, "member_name": "Maria Okafor", "title": "Data Analyst at StrictData",
     "profile_url": "/profile/2", "profile_pic": "https://via.placeholder.com/80.png?text=MO",
     "comment": "Interesting insight, thanks for sharing.", "reaction": "LOVE",
     "timestamp": (now - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M"),
     "about": "Maria helps businesses transform raw data into actionable insights.",
     "recent_activity": "Recently shared a StrictData article on Power BI dashboards."},
    {"member_id": 3, "member_name": "David Chen", "title": "Machine Learning Engineer at StrictData",
     "profile_url": "/profile/3", "profile_pic": "https://via.placeholder.com/80.png?text=DC",
     "comment": "Would love to learn more about this.", "reaction": "WOW",
     "timestamp": (now - timedelta(hours=1, minutes=5)).strftime("%Y-%m-%d %H:%M"),
     "about": "David builds scalable ML solutions and contributes to open-source AI projects.",
     "recent_activity": "Liked StrictData’s post on responsible AI governance."}
]

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_dev_key")

CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("LINKEDIN_REDIRECT_URI")
SCOPES = "r_organization_social"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

@app.route("/")
def home():
    preset = os.environ.get("PRESET_ACCESS_TOKEN")
    if preset and not session.get("access_token"):
        session["access_token"] = preset
    token_status = ("<strong>Session has an access token (preset or from login).</strong>"
                    if session.get("access_token") else "<em>No access token in session yet.</em>")
    return f"""
    <h1>LinkedIn Demo — Render-ready</h1>
    <p><a href="/login">Login with LinkedIn (OAuth)</a> |
       <a href="/post">Create / Simulate Post</a> |
       <a href="/preset_help">Preset token help</a></p>
    <p>{token_status}</p>
    <p style="color:gray;font-size:0.9em">Note: This demo stores tokens only in server session and never prints the full token.</p>
    """

@app.route("/preset_help")
def preset_help():
    return """
    <h3>Preset token options (for local / screencast use)</h3>
    <ol>
      <li>Set environment variable <code>PRESET_ACCESS_TOKEN</code> in Render (recommended for non-interactive demos).</li>
      <li>Or visit <code>/preset?token=YOUR_TOKEN</code> (sets token in session; token is not shown in browser).</li>
    </ol>
    <p style="color:orange">Use preset tokens only for testing or screencasts — do not commit tokens to source control.</p>
    <p><a href="/">Back home</a></p>
    """

@app.route("/preset")
def preset():
    token = request.args.get("token")
    if not token:
        return "<p>Error: call /preset?token=YOUR_TOKEN</p><p><a href='/'>Back</a></p>"
    session["access_token"] = token
    return "<p>Access token stored in session safely. <a href='/post'>Go to Post simulation</a></p>"

@app.route("/login")
def login():
    if not CLIENT_ID or not REDIRECT_URI:
        return "<p>Error: LINKEDIN_CLIENT_ID or LINKEDIN_REDIRECT_URI not set.</p>"
    auth_redirect = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPES}"
    return redirect(auth_redirect)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "<p>Error: No code received from LinkedIn.</p>"
    token_data = {
        "grant_type": "authorization_code", "code": code,
        "redirect_uri": REDIRECT_URI, "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    r = requests.post(TOKEN_URL, data=token_data, timeout=10)
    token_json = r.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return f"<p>Error getting access token: {json.dumps(token_json)}</p>"
    session["access_token"] = access_token
    session["token_acquired_at"] = datetime.utcnow().isoformat()
    return "<h2>Logged in successfully!</h2><p>Proceed to <a href='/post'>Post simulation</a></p>"

@app.route("/post")
def post_demo():
    token_present = "Yes" if session.get("access_token") else "No"
    return f'''
    <h2>Create a Post (Simulation)</h2>
    <p>Session token present: <strong>{token_present}</strong></p>
    <form method="post" action="/submit_post">
        <textarea name="message" rows="4" cols="60">Excited to demo our LinkedIn integration!</textarea><br><br>
        <button type="submit">Publish / Simulate Post</button>
    </form>
    <p><a href="/">Back home</a></p>
    '''

@app.route("/submit_post", methods=["POST"])
def submit_post():
    message = request.form.get("message", "").strip()
    now = datetime.now()
    simulated_post = {
        "author": "urn:li:organization:YOUR_ORG_URN",
        "message": message or "(empty message)",
        "timestamp": now.strftime("%Y-%m-%d %H:%M"),
        "images": ["https://via.placeholder.com/300x180.png?text=Company+Post"],
    }
    impressions = 240 + len(message)
    likes = sum(1 for e in simulated_engagement if e["reaction"] in ("LIKE", "LOVE"))
    comments = len(simulated_engagement)
    shares = random.randint(1, 6)
    engagement_rate = round((likes + comments + shares) / impressions * 100, 2)
    employees = [{"name": "Mimolwa Emanuel", "profile_url": "#", "title": "Digital Content Creator"},
                 {"name": "Evee Nwoxsu", "profile_url": "#", "title": "Account Executive"}]

    engagement_items_html = "".join(
        f'''
        <div class="eng-item" id="eng-{idx}" style="border:1px solid #ddd;padding:8px;margin:8px 0;border-radius:6px;">
            <img src="{e['profile_pic']}" width="48" height="48" style="border-radius:50%;margin-right:8px;">
            <a href="{e['profile_url']}"><strong>{e['member_name']}</strong></a>
            <em style="color:gray"> — {e['title']}</em>
            <div>{e['comment']}</div>
            <div><small>{e['timestamp']}</small> — Reaction: <strong>{e['reaction']}</strong>
            <button onclick="simulateLike('{idx}')">Like</button>
            <button onclick="simulateViewProfile('{idx}')">View profile</button>
            <button onclick="simulateReply('{idx}')">Reply</button></div>
        </div>''' for idx, e in enumerate(simulated_engagement)
    )
    employees_html = "".join(
        f"<li>{emp['name']} — <small>{emp['title']}</small> <button onclick='simulateEmployeeReshare(\"{emp['name']}\")'>Simulate Reshare</button></li>"
        for emp in employees
    )

    return f"""
    <html>
      <head><title>Post Simulation</title><meta name="viewport" content="width=device-width,initial-scale=1"></head>
      <body style="font-family:Arial,Helvetica,sans-serif;line-height:1.4;padding:18px;">
        <h2>Post Simulation Complete</h2>
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <img src="{simulated_post['images'][0]}" style="width:300px;border-radius:6px;border:1px solid #ccc;">
          <div>
            <p><strong>Message</strong></p>
            <p style="background:#fafafa;padding:10px;border-radius:6px;border:1px solid #eee;">{simulated_post['message']}</p>
            <p><small>Published: {simulated_post['timestamp']}</small></p>
            <p><strong>Aggregate Metrics</strong></p>
            <ul>
              <li>Impressions: <span id="impressions">{impressions}</span></li>
              <li>Likes: <span id="likes">{likes}</span></li>
              <li>Comments: <span id="comments">{comments}</span></li>
              <li>Shares: <span id="shares">{shares}</span></li>
              <li>Engagement rate: <span id="eng_rate">{engagement_rate}%</span></li>
            </ul>
          </div>
        </div>
        <h3>Member-level Engagement (simulated)</h3>
        <div id="engagement_list">{engagement_items_html}</div>
        <h3>Employee Advocacy (simulated)</h3>
        <ul id="employee_list">{employees_html}</ul>
        <div id="employee_reshares" style="margin-top:8px;color:green;"></div>
        <p style="color:gray">This is a simulated UI; no real LinkedIn write is performed.</p>
        <p><a href="/post">Back to Post composer</a> | <a href="/">Home</a></p>
        <script>
          function simulateLike(idx) {{
            document.getElementById('likes').textContent = Number(document.getElementById('likes').textContent)+1;
            alert('Simulated like recorded (client-side).');
          }}
          function simulateViewProfile(idx) {{
            const el=document.getElementById('eng-'+idx); const a=el.querySelector('a'); if(a) window.open(a.href,'_blank');
          }}
          function simulateReply(idx){{
            const c=prompt('Type your reply (simulated):'); if(c){{
              document.getElementById('comments').textContent=Number(document.getElementById('comments').textContent)+1;
              alert('Simulated reply added: '+c);
            }}
          }}
          function simulateEmployeeReshare(name){{
            document.getElementById('shares').textContent=Number(document.getElementById('shares').textContent)+1;
            const container=document.getElementById('employee_reshares');
            const now=new Date().toISOString().slice(0,16).replace('T',' ');
            container.innerHTML+='<div>'+name+' reshared at '+now+'</div>';
            alert(name+' reshared (simulated).');
          }}
        </script>
      </body>
    </html>
    """

@app.route("/profile/<int:member_id>")
def profile(member_id):
    member = next((m for m in simulated_engagement if m["member_id"] == member_id), None)
    if not member:
        return "<h3>Member not found</h3><p><a href='/post'>Back to Post</a></p>", 404
    return f"""
    <html>
      <head><title>{member['member_name']} — Profile</title><meta name="viewport" content="width=device-width,initial-scale=1"></head>
      <body style="font-family:Arial,Helvetica,sans-serif;line-height:1.4;padding:18px;">
        <div style="max-width:500px;margin:auto;border:1px solid #ddd;border-radius:10px;padding:20px;">
          <div style="text-align:center;">
            <img src="{member['profile_pic']}" width="120" height="120" style="border-radius:50%;border:2px solid #ccc;"><br><br>
            <h2>{member['member_name']}</h2>
            <p style="color:gray">{member['title']}</p>
          </div>
          <hr>
          <p><strong>About:</strong></p><p style="background:#fafafa;padding:10px;border-radius:6px;border:1px solid #eee;">{member['about']}</p>
          <p><strong>Recent Activity:</strong></p><p style="background:#fafafa;padding:10px;border-radius:6px;border:1px solid #eee;">{member['recent_activity']}</p>
          <p style="text-align:center;margin-top:20px;"><a href="/post">&larr; Back to Post simulation</a></p>
        </div>
      </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = bool(os.environ.get("DEBUG", "False").lower() in ("1","true","yes"))
    app.run(host="0.0.0.0", port=port, debug=debug)

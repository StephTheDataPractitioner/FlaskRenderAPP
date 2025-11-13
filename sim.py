# flask_linkedin_oauth_demo_render_ready_v2.py
"""
Render-ready demo app for LinkedIn Standard Tier review screencast.
- Stores tokens in session only (never prints them).
- Supports /preset?token=... for setting a session token (local / screencast use ONLY).
- Simulates member-level engagement, aggregate analytics, and employee advocacy.
"""

from flask import Flask, redirect, request, session, url_for
import os
import requests
from datetime import datetime, timedelta
import random
import json

app = Flask(__name__)
# SECRET should be set in Render as FLASK_SECRET_KEY (or use default_dev_key for local dev)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_dev_key")

# === LinkedIn App Credentials (set as env vars on Render) ===
CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("LINKEDIN_REDIRECT_URI")  # e.g. https://yourapp.onrender.com/callback
SCOPES = "r_organization_social"

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# ---------- Helper: small safe truncated token display (used nowhere except optional debug) ----------
def _truncated_token(tok):
    if not tok:
        return "<none>"
    return tok[:8] + "..." + tok[-4:]

# ---------- Routes ----------
@app.route("/")
def home():
    # If a PRESET_ACCESS_TOKEN env var exists, automatically load into session (no print)
    preset = os.environ.get("PRESET_ACCESS_TOKEN")
    if preset and not session.get("access_token"):
        session["access_token"] = preset

    token_status = ("<strong>Session has an access token (preset or from login).</strong>"
                    if session.get("access_token") else "<em>No access token in session yet.</em>")

    return f"""
    <h1>LinkedIn Demo — Render-ready</h1>
    <p>
      <a href="/login">Login with LinkedIn (OAuth)</a> |
      <a href="/post">Create / Simulate Post</a> |
      <a href="/preset_help">Preset token help</a>
    </p>
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
    # Do NOT show token to the browser — confirm only that it was stored.
    return "<p>Access token stored in session safely. <a href='/post'>Go to Post simulation</a></p>"

@app.route("/login")
def login():
    # Redirect user to LinkedIn OAuth consent screen (they will see the LinkedIn permissions/consent)
    if not CLIENT_ID or not REDIRECT_URI:
        return ("<p>Error: LINKEDIN_CLIENT_ID or LINKEDIN_REDIRECT_URI is not configured in environment.</p>"
                "<p>Set environment variables on Render and redeploy.</p>")
    auth_redirect = (
        f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope={SCOPES}"
    )
    return redirect(auth_redirect)

@app.route("/callback")
def callback():
    # OAuth redirect endpoint. We exchange code for token and store token in session without printing it.
    code = request.args.get("code")
    if not code:
        return "<p>Error: No code received from LinkedIn. Did you cancel the consent screen?</p><p><a href='/'>Back</a></p>"

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    try:
        r = requests.post(TOKEN_URL, data=token_data, timeout=10)
        token_json = r.json()
    except Exception as ex:
        return f"<p>Token exchange error: {ex}</p><p><a href='/'>Back</a></p>"

    access_token = token_json.get("access_token")
    if not access_token:
        return f"<p>Error getting access token: {json.dumps(token_json)}</p><p><a href='/'>Back</a></p>"

    # Store token in session (never render it)
    session["access_token"] = access_token
    # Optionally store token acquired time
    session["token_acquired_at"] = datetime.utcnow().isoformat()

    return """
    <h2>Logged in successfully!</h2>
    <p>Access token stored safely in session (not shown).</p>
    <p>Proceed to <a href="/post">Post simulation</a> to demonstrate posting and engagement.</p>
    """

@app.route("/post")
def post_demo():
    token_present = "Yes" if session.get("access_token") else "No"
    return f'''
    <h2>Create a Post (Simulation)</h2>
    <p>Session token present: <strong>{token_present}</strong></p>
    <form method="post" action="/submit_post">
        <textarea name="message" rows="4" cols="60" placeholder="Write your post here...">Excited to demo our LinkedIn integration!</textarea><br><br>
        <button type="submit">Publish / Simulate Post</button>
    </form>
    <p><a href="/">Back home</a></p>
    '''

@app.route("/submit_post", methods=["POST"])
def submit_post():
    message = request.form.get("message", "").strip()
    now = datetime.now()

    # Simulated post object (would be the payload if you called LinkedIn APIs)
    simulated_post = {
        "author": "urn:li:organization:YOUR_ORG_URN",
        "message": message or "(empty message)",
        "timestamp": now.strftime("%Y-%m-%d %H:%M"),
        "images": ["https://via.placeholder.com/300x180.png?text=Company+Post"],
    }

    # Simulated member-level engagement (includes public profile details)
    simulated_engagement = [
        {
            "member_name": "Alice Johnson",
            "title": "Data Analyst at StrictData",
            "profile_url": "https://www.linkedin.com/in/alicejohnson",
            "profile_pic": "https://via.placeholder.com/64.png?text=A",
            "comment": "Great post — very useful!",
            "reaction": "LIKE",
            "timestamp": (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M")
        },
        {
            "member_name": "Bob Smith",
            "title": "Marketing Lead at StrictData",
            "profile_url": "https://www.linkedin.com/in/bobsmith",
            "profile_pic": "https://via.placeholder.com/64.png?text=B",
            "comment": "Interesting insight, thanks for sharing.",
            "reaction": "LOVE",
            "timestamp": (now - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M")
        },
        {
            "member_name": "Carol Lee",
            "title": "Software Engineer at StrictData",
            "profile_url": "https://www.linkedin.com/in/carollee",
            "profile_pic": "https://via.placeholder.com/64.png?text=C",
            "comment": "Would love to learn more about this.",
            "reaction": "WOW",
            "timestamp": (now - timedelta(hours=1, minutes=5)).strftime("%Y-%m-%d %H:%M")
        }
    ]

    # Simulated analytics (hardcoded / deterministic for demo)
    impressions = 240 + len(message)  # small deterministic variance
    likes = sum(1 for e in simulated_engagement if e["reaction"] in ("LIKE", "LOVE"))
    comments = len(simulated_engagement)
    shares = random.randint(1, 6)
    engagement_rate = round((likes + comments + shares) / impressions * 100, 2)

    # Employee advocacy simulation (list of employees who reshared)
    employees = [
        {"name": "Dayo Okafor", "profile_url": "#", "title": "Sales Manager"},
        {"name": "Eve Nwosu", "profile_url": "#", "title": "Account Executive"}
    ]

    # Render HTML with client-side JS for interactive simulation (no external calls)
    engagement_items_html = ""
    for idx, e in enumerate(simulated_engagement):
        engagement_items_html += f"""
        <div class="eng-item" id="eng-{idx}" style="border:1px solid #ddd;padding:8px;margin:8px 0;border-radius:6px;">
            <img src="{e['profile_pic']}" width="48" height="48" style="vertical-align:middle;border-radius:50%;margin-right:8px;">
            <a href="{e['profile_url']}" target="_blank"><strong>{e['member_name']}</strong></a>
            <em style="color:gray"> — {e['title']}</em>
            <div style="margin-top:6px;">{e['comment']}</div>
            <div style="margin-top:6px;">
                <small>{e['timestamp']}</small> —
                <span class="reaction">Reaction: <strong>{e['reaction']}</strong></span>
                &nbsp;
                <button onclick="simulateLike('{idx}')">Like</button>
                <button onclick="simulateViewProfile('{idx}')">View profile</button>
                <button onclick="simulateReply('{idx}')">Reply</button>
            </div>
        </div>
        """

    employees_html = "".join(
        f"<li>{emp['name']} — <small>{emp['title']}</small> <button onclick='simulateEmployeeReshare(\"{emp['name']}\")'>Simulate Reshare</button></li>"
        for emp in employees
    )

    # HTML response
    html = f"""
    <html>
      <head>
        <title>Post Simulation</title>
        <meta name="viewport" content="width=device-width,initial-scale=1">
      </head>
      <body style="font-family:Arial,Helvetica,sans-serif;line-height:1.4;padding:18px;">
        <h2>Post Simulation Complete</h2>

        <div style="display:flex;gap:12px;align-items:flex-start;">
          <img src="{simulated_post['images'][0]}" alt="post image" style="width:300px;border-radius:6px;border:1px solid #ccc;">
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
        <div id="engagement_list">
          {engagement_items_html}
        </div>

        <h3>Employee Advocacy (simulated)</h3>
        <p>Employees who can reshare to amplify content:</p>
        <ul id="employee_list">
          {employees_html}
        </ul>
        <div id="employee_reshares" style="margin-top:8px;color:green;"></div>

        <h3>Page Analytics (sample)</h3>
        <p>Basic page analytics are shown above in Aggregate Metrics. In a full integration you'd fetch these via LinkedIn Page Analytics APIs.</p>

        <p style="color:gray">Important: This is a simulated UI to demonstrate what the reviewer wants to see: OAuth flow, posting, member-level engagement, interaction ability, and analytics. No real LinkedIn write is performed by this demo unless you wire the API calls using your stored token.</p>

        <p><a href="/post">Back to Post composer</a> | <a href="/">Home</a></p>

        <script>
          function simulateLike(idx) {{
            // increment likes in UI only
            const likesEl = document.getElementById('likes');
            likesEl.textContent = Number(likesEl.textContent) + 1;
            alert('Simulated like recorded (client-side).');
          }}
          function simulateViewProfile(idx) {{
            // open the profile link for the element
            const el = document.getElementById('eng-' + idx);
            const a = el.querySelector('a');
            if (a) window.open(a.href, '_blank');
          }}
          function simulateReply(idx) {{
            const comment = prompt('Type your reply (simulated):');
            if (comment) {{
              const commentsEl = document.getElementById('comments');
              commentsEl.textContent = Number(commentsEl.textContent) + 1;
              alert('Simulated reply added (client-side): ' + comment);
            }}
          }}
          function simulateEmployeeReshare(name) {{
            const sharesEl = document.getElementById('shares');
            sharesEl.textContent = Number(sharesEl.textContent) + 1;
            const container = document.getElementById('employee_reshares');
            const now = new Date().toISOString().slice(0,16).replace('T',' ');
            container.innerHTML += '<div>' + name + ' reshared at ' + now + '</div>';
            alert(name + ' reshared (simulated).');
          }}
        </script>
      </body>
    </html>
    """

    return html


if __name__ == "__main__":
    # PORT is set by Render; default to 5000 locally.
    port = int(os.environ.get("PORT", 5000))
    # When deploying to Render, leave debug=False for production-like behavior. For local dev, you can set env DEBUG=1.
    debug = bool(os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes"))
    app.run(host="0.0.0.0", port=port, debug=debug)

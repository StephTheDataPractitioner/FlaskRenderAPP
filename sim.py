# flask_linkedin_oauth_demo_preset_token_step2_enhanced.py
from flask import Flask, redirect, request, session, url_for
import os
import requests
from datetime import datetime, timedelta
from collections import Counter

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_dev_key")
# === LinkedIn App Credentials ===
CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("LINKEDIN_REDIRECT_URI", "http://localhost:5000/callback")
SCOPES = "r_organization_social"  # Developer Tier scope

# LinkedIn OAuth URLs
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

@app.route("/")
def home():
    preset = os.environ.get("PRESET_ACCESS_TOKEN")
    if preset and not session.get("access_token"):
        session["access_token"] = preset

    login_link = '<a href="/login">Login with LinkedIn</a>'
    post_link = '<a href="/post">Simulate Posting</a>'
    preset_info = "<p><strong>Session has an access token (preset or from login).</strong></p>" if session.get("access_token") else "<p><em>No access token in session yet.</em></p>"

    return f"{login_link} | {post_link} | <a href='/preset_help'>How to preset token</a><br/>{preset_info}"

@app.route("/preset_help")
def preset_help():
    return (
        "<h3>Preset token options</h3>"
        "<ol>"
        "<li>Set environment variable PRESET_ACCESS_TOKEN before running the app.</li>"
        "<li>Or visit <code>/preset?token=YOUR_TOKEN</code> to set token for your session.</li>"
        "</ol>"
        "<p>Use these only locally for your screencast.</p>"
    )

@app.route("/preset")
def preset():
    token = request.args.get("token")
    if not token:
        return "<p>Error: pass token as ?token=...</p>"
    session["access_token"] = token
    return "<p>Access token set in session. Go to <a href='/post'>Simulate Posting</a>.</p>"

@app.route("/login")
def login():
    auth_redirect = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPES}"
    return redirect(auth_redirect)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: No code received"

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    token_response = requests.post(TOKEN_URL, data=token_data)
    token_json = token_response.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return f"Error getting access token: {token_json}"

    session["access_token"] = access_token
    return f"<h2>Logged in successfully!</h2><p>Access token set in session.</p><p>Access token: <code>{access_token}</code></p><p>Go to <a href='/post'>Simulate Posting</a></p>"

@app.route("/post")
def post_demo():
    token_present = "Yes" if session.get("access_token") else "No"
    return f'''
    <h2>Create a Post (Simulation)</h2>
    <p>Session token present: <strong>{token_present}</strong></p>
    <form method="post" action="/submit_post">
        <textarea name="message" rows="3" cols="50" placeholder="Write your post here..."></textarea><br>
        <button type="submit">Post to LinkedIn (Simulated)</button>
    </form>
    <p><a href="/">Back home</a></p>
    '''

@app.route("/submit_post", methods=["POST"])
def submit_post():
    message = request.form.get("message", "")
    simulated_payload = {
        "author": "urn:li:organization:YOUR_ORG_URN",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": message},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    # Mock member-level engagement
    now = datetime.now()
    fake_engagement = [
        {"member_name": "Alice Johnson", "comment": "Great post!", "reaction": "LIKE",
         "timestamp": (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M"), "profile_pic": "data:image/png;base64,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"},
        {"member_name": "Bob Smith", "comment": "Interesting insight.", "reaction": "LOVE",
         "timestamp": (now - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M"), "profile_pic": "data:image/png;base64,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"},
        {"member_name": "Charlie Lee", "comment": "Thanks for sharing!", "reaction": "CLAP",
         "timestamp": (now - timedelta(hours=1, minutes=10)).strftime("%Y-%m-%d %H:%M"), "profile_pic": "data:image/png;base64,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"}
    ]

    # Compute aggregate reactions
    reaction_counts = Counter([c["reaction"] for c in fake_engagement])
    reactions_html = " | ".join(f"{r}: {reaction_counts[r]}" for r in reaction_counts)

    comments_html = f"<p><strong>Reactions: {reactions_html}</strong></p><ul style='list-style:none;'>"
    for c in fake_engagement:
        comments_html += f"""
        <li style='margin-bottom:10px;'>
            <img src="{c['profile_pic']}" alt="profile" style="width:40px;height:40px;border-radius:50%;vertical-align:middle;">
            <strong>{c['member_name']}</strong> <em>({c['timestamp']})</em><br>
            {c['comment']} <span style="color:blue;">[{c['reaction']}]</span>
            <br>
            <button disabled style="margin-right:5px;">Like</button>
            <button disabled>Reply</button>
        </li>
        """
    comments_html += "</ul>"

    token_state = session.get("access_token", "<none>")
    truncated = (token_state[:10] + "...") if token_state != "<none>" else "<none>"

    return f"""
    <h3>Simulated LinkedIn Post Payload:</h3>
    <pre>{simulated_payload}</pre>
    <h3>Simulated Member Engagement:</h3>
    {comments_html}
    <p>Session access token (truncated): <code>{truncated}</code></p>
    <p>(Simulation only. Real member-level data will display once Standard Tier access is granted.)</p>
    <p><a href="/post">Back</a></p>
    """

if __name__ == "__main__":
    app.run(debug=True)

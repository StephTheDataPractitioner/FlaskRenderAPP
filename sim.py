# flask_linkedin_oauth_demo_render_ready.py
from flask import Flask, redirect, request, session, url_for
import os
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_dev_key")

# === LinkedIn App Credentials ===
CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("LINKEDIN_REDIRECT_URI")  # Set this in Render
SCOPES = "r_organization_social"

# LinkedIn OAuth URLs
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# ===== Routes =====
@app.route("/")
def home():
    # Automatically load preset token if available and session empty
    preset = os.environ.get("PRESET_ACCESS_TOKEN")
    if preset and not session.get("access_token"):
        session["access_token"] = preset

    login_link = '<a href="/login">Login with LinkedIn</a>'
    post_link = '<a href="/post">Simulate Posting</a>'
    token_status = "<p><strong>Session has an access token (preset or from login).</strong></p>" if session.get("access_token") else "<p><em>No access token in session yet.</em></p>"

    return f"{login_link} | {post_link} | <a href='/preset_help'>Preset token help</a><br/>{token_status}"

@app.route("/preset_help")
def preset_help():
    return (
        "<h3>Preset token options</h3>"
        "<ol>"
        "<li>Set the environment variable <code>PRESET_ACCESS_TOKEN</code> in Render.</li>"
        "<li>Or visit <code>/preset?token=YOUR_TOKEN</code> to set a token in your session.</li>"
        "</ol>"
        "<p>Use only locally or for screencast purposes.</p>"
    )

@app.route("/preset")
def preset():
    token = request.args.get("token")
    if not token:
        return "<p>Error: pass token as ?token=...</p>"
    session["access_token"] = token
    return "<p>Access token stored in session safely. <a href='/post'>Go to Post simulation</a></p>"

@app.route("/login")
def login():
    auth_redirect = (
        f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope={SCOPES}"
    )
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
    return "<h2>Logged in successfully!</h2><p>Access token stored safely in session.</p><p><a href='/post'>Go to Post simulation</a></p>"

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
    # Simulated payload
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
    # We just simulate; in real usage, you'd call LinkedIn API here
    return f"<p>Post simulated! Message length: {len(message)} chars</p><p><a href='/post'>Back</a></p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

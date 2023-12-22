# Python standard libraries
import json
import os
import sqlite3

# Third-party libraries
from flask import Flask, redirect, request, url_for, Response
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

# Internal imports
from db import init_db_command, update_user_profile, delete_user_profile
from user import User

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
# GOOGLE_CLIENT_ID = 
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)

GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

#TODO: update/handle this? idk what we should do here with Mongo
# Naive database setup
# try:
#     init_db_command()
# except sqlite3.OperationalError:
#     # Assume it's already been created
#     pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/")
def index():
    if current_user.is_authenticated:
        html_content = (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'
            '<form id="update-form" action="/update_profile" method="post">'
            '<input type="text" name="name" placeholder="Enter new name">'
            '<button type="submit">Update Name</button>'
            '</form>'
            '<button id="delete-profile">Delete Profile</button>'
            .format(current_user.name, current_user.email, current_user.profile_pic)
        )

        update_script = """
        <script>
        document.getElementById('update-form').addEventListener('submit', function(event) {
            event.preventDefault();
            var formData = new FormData(this);
            var object = {};
            formData.forEach(function(value, key){
                object[key] = value;
            });
            var json = JSON.stringify(object);

            fetch('/update_profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: json
            }).then(response => {
                if (response.ok) {
                    alert('Profile updated successfully');
                    window.location.href = '/';
                } else {
                    alert('Failed to update profile');
                }
            });
        });
        </script>
        """

        delete_script = """
        <script>
        document.getElementById('delete-profile').addEventListener('click', function() {
            if(confirm('Are you sure you want to delete your profile?')) {
                fetch('/delete_profile', {
                    method: 'DELETE'
                }).then(response => {
                    if (response.ok) {
                        alert('Profile deleted successfully');
                        window.location.href = '/';
                    } else {
                        alert('Failed to delete profile');
                    }
                });
            }
        });
        </script>
        """

        return html_content + update_script + delete_script
    else:
        return '<a class="button" href="/login">Google Login</a>'
    
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")


    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]


    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )
    
    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/update_profile", methods=["PUT"])
@login_required
def update_profile():
    new_name = request.json.get('name')
    user_id = current_user.id

    if not new_name:
        return Response(json.dumps({"error": "Name is required"}), mimetype='application/json', status=400)

    if update_user_profile(user_id, new_name) == 0:
        return Response(json.dumps({"error": "Update failed"}), mimetype='application/json', status=500)

    return Response(json.dumps({"message": "Name updated successfully"}), mimetype='application/json', status=200)


@app.route("/delete_profile", methods=["DELETE"])
@login_required
def delete_profile():
    user_id = current_user.id

    if delete_user_profile(user_id) == 0:
        return Response(json.dumps({"error": "Deletion failed"}), mimetype='application/json', status=500)

    return Response(json.dumps({"message": "User deleted successfully"}), mimetype='application/json', status=200)

if __name__ == "__main__":
    app.run(ssl_context="adhoc")
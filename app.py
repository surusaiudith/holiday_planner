from datetime import datetime
import json
import requests
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'dlMwYFRPmi4Rrdfh5rVUuUdPv2e5Bckw'
login_manager = LoginManager()
login_manager.init_app(app)

# User model
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Hardcoded user credentials (replace with real authentication in production)
users = {'admin': {'password': 'password123'}}

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('home'))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# Home route (only accessible if logged in)
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        preferences = {
            "location_type": request.form.get("location_type").lower(),
            "budget": request.form.get("budget").lower(),
            "season": request.form.get("season").lower(),
            "activities": [activity.lower() for activity in request.form.getlist("activities")],
            "num_days": int(request.form.get("num_days"))
        }

        # Load test data from JSON
        with open('data/destination.json') as f:
            destinations = json.load(f)["destinations"]

        # Filter destinations
        recommendations = [
            {
                "name": d["name"],
                "images": d["images"]  # Include images in the recommendations
            }
            for d in destinations if
            d["type"].lower() == preferences["location_type"] and
            d["budget"].lower() == preferences["budget"] and
            d["season"].lower() == preferences["season"] and
            any(activity.lower() in [a.lower() for a in d["activities"]] for activity in preferences["activities"]) and
            d["num_days"] >= preferences["num_days"]
        ]

        return render_template("results.html", recommendations=recommendations, preferences=preferences)

    return render_template("index.html")

# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Weather API route with error handling
def get_weather(city):
    api_key = "0152a10cc622469182929c0f5d489c6d"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.RequestException:
        return {"error": "Could not retrieve weather data"}

@app.route("/weather")
@login_required
def weather():
    city = request.args.get('city', 'London')
    weather_data = get_weather(city)
    return render_template('weather.html', weather=weather_data)

# Learning agent: Save feedback and improve recommendations
def load_user_data():
    try:
        with open('data/user_data.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_feedback(user_id, feedback):
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {'feedback': []}
    user_data[user_id]['feedback'].append(feedback)
    with open('data/user_data.json', 'w') as f:
        json.dump(user_data, f)

def update_recommendations(user_id, destinations):
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {'feedback': []}

    # Simple feedback logic to improve recommendations
    feedback = user_data[user_id]['feedback']
    liked_destinations = [f['destination'] for f in feedback if f['liked']]
    
    for dest in destinations:
        if dest["name"] in liked_destinations:
            dest["score"] += 1
        else:
            dest["score"] = max(dest.get("score", 0) - 1, 0)

    destinations.sort(key=lambda x: x.get("score", 0), reverse=True)
    return destinations

# Feedback route to store and update recommendations
@app.route("/feedback/<destination>", methods=["POST"])
@login_required
def feedback(destination):
    feedback = request.form['feedback']  # 'liked' or 'disliked'
    
    # Save user feedback
    user_id = current_user.id
    feedback_data = {'destination': destination, 'liked': feedback == 'liked'}
    save_user_feedback(user_id, feedback_data)
    
    # Update recommendations based on feedback
    with open('data/destination.json') as f:
        destinations = json.load(f)["destinations"]
    updated_recommendations = update_recommendations(user_id, destinations)
    
    return redirect(url_for('home'))

import json

@app.route('/update_score', methods=['POST'])
def update_score():
    # Assuming the destination is sent as part of the form data
    destination_name = request.form.get('destination_name')
    action = request.form.get('action')  # "like" or "dislike"

    # Load the current data from the destination.json file
    with open('destination.json', 'r') as file:
        data = json.load(file)

    # Update the score based on action
    for destination in data['destinations']:
        if destination['name'] == destination_name:
            if action == 'like':
                destination['score'] += 1
            elif action == 'dislike':
                destination['score'] -= 1

    # Write the updated data back to the destination.json file
    with open('destination.json', 'w') as file:
        json.dump(data, file, indent=4)

    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
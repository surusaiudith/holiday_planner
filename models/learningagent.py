import json

# Function to load user preferences data
def load_user_data():
    try:
        with open('data/user_data.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_feedback(user_id, destination, liked):
    user_data = load_user_data()

    # Initialize user feedback data if not present
    if user_id not in user_data:
        user_data[user_id] = {'feedback': []}

    # Check if the user has already given feedback for the destination
    feedback_found = False
    for feedback in user_data[user_id]['feedback']:
        if feedback['destination'] == destination:
            # Update the existing feedback
            feedback['liked'] = liked
            feedback_found = True
            break

    # If no existing feedback, append new feedback
    if not feedback_found:
        user_data[user_id]['feedback'].append({'destination': destination, 'liked': liked})
    
    with open('data/user_data.json', 'w') as f:
        json.dump(user_data, f, indent=4)



# Function to get recommendations based on user preferences
def get_recommendations(preferences, destinations):
    recommendations = []
    for destination in destinations:
        if (destination["type"].lower() == preferences["location_type"] and
            destination["budget"].lower() == preferences["budget"] and
            destination["season"].lower() == preferences["season"] and
            any(activity.lower() in preferences["activities"] for activity in destination["activities"]) and
            destination["num_days"] >= preferences["num_days"]):
            recommendations.append(destination)
    return recommendations

def update_recommendations(user_id, destinations):
    user_data = load_user_data()

    # Check if the user has any feedback
    if user_id not in user_data or 'feedback' not in user_data[user_id]:
        return destinations

    feedback = user_data[user_id]['feedback']
    liked_destinations = [f['destination'] for f in feedback if f['liked']]

    # Print the liked destinations for debugging
    print(f"Liked Destinations: {liked_destinations}")

    # Update the recommendations based on feedback
    for dest in destinations:
        print(f"Checking destination: {dest['name']}")

        # If the destination is liked, increase the score; if disliked, decrease the score
        if dest["name"] in liked_destinations:
            dest["score"] = dest.get("score", 0) + 1  # Increase score for liked destinations
        else:
            dest["score"] = max(dest.get("score", 0) - 1, 0)  # Decrease score for disliked destinations

        # Print each updated destination for debugging
        print(f"Updated Destination: {dest['name']} with score {dest['score']}")

    # Sort destinations based on score
    destinations.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Print sorted destinations for debugging
    print(f"Sorted Destinations: {[d['name'] for d in destinations]}")

    # Save the updated destinations back to destination.json
    with open('data/destination.json', 'w') as f:
        json.dump({"destinations": destinations}, f, indent=4)

    return destinations

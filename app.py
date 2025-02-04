import json
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import math
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Load users from the JSON file
def load_users():
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = {}
    return users

# Save users to the JSON file
def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

# Load packages from the JSON file
def load_packages():
    try:
        with open('packages.json', 'r') as f:
            packages = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        packages = []
    return packages

# Save packages to the JSON file
def save_packages(packages):
    with open('packages.json', 'w') as f:
        json.dump(packages, f)

# Function to send email for booking confirmation
def send_email(to_email, total_cost):
    from_email = "your-email@gmail.com"  # Replace with your email
    from_password = "your-email-password"  # Replace with your email password

    subject = "Booking Confirmation"
    body = f"Your booking has been successfully confirmed! Please pay within 15 days. Total cost: {total_cost} INR."

    # Create the email
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    # Send the email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, from_password)
            server.sendmail(from_email, to_email, message.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Function to calculate distance using the Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# Function to load the data from JSON file
def load_data():
    with open('data.json', 'r') as file:
        return json.load(file)

@app.route('/')
def home():
    # Load the data from the JSON file
    travel_packages = load_data()

    # Pass the travel packages data to the template
    return render_template('home.html', travel_packages=travel_packages)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        
        if username in users and users[username] == password:
            session['username'] = username  # Set session variable
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users:
            flash('Username already exists!', 'danger')
        else:
            users[username] = password
            save_users(users)
            flash('Registration successful! You can log in now.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# Define the path to the booking history JSON file
BOOKING_HISTORY_FILE = 'booking_history.json'

# Ensure the file exists at the start (otherwise create it)
if not os.path.exists(BOOKING_HISTORY_FILE):
    with open(BOOKING_HISTORY_FILE, 'w') as f:
        json.dump([], f)  # Initialize with an empty list if file doesn't exist


# Function to save booking data to a JSON file
def save_booking_to_history(user_email, adults, children, food_preference, total_cost, travel_date, package_place):
    # Prepare the booking data
    booking_data = {
        'user': user_email,  # Use the logged-in username here
        'adults': adults,
        'children': children,
        'foodPreference': food_preference,
        'totalCost': total_cost,
        'travelDate': travel_date,
        'packagePlace': package_place
    }

    try:
        # Open the file, read the existing data, and append the new booking
        with open(BOOKING_HISTORY_FILE, 'r') as file:
            bookings = json.load(file)  # Read existing bookings

        bookings.append(booking_data)  # Append the new booking

        # Write the updated bookings list back to the file
        with open(BOOKING_HISTORY_FILE, 'w') as file:
            json.dump(bookings, file, indent=4)  # Save with pretty printing

        print(f"Booking saved successfully for {user_email}!")

    except Exception as e:
        print(f"Error saving booking: {e}")
        return jsonify({"message": "Error saving booking!"})

    return jsonify({"message": "Booking confirmed and saved!"})

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    # Check if the user is logged in
    if 'username' not in session:
        flash('You need to log in to confirm the booking.', 'danger')
        return redirect(url_for('login'))  # Redirect to the login page

    # If the user is logged in, proceed with the booking
    data = request.get_json()

    # Extract the details from the request
    adults = data.get('adults')
    children = data.get('children')
    food_preference = data.get('foodPreference')
    total_cost = data.get('totalCost')
    travel_date = data.get('travelDate')
    package_place = data.get('packagePlace')
    user_name = data.get('userName')  # Use the username sent from the form

    # Save the booking to history
    response = save_booking_to_history(user_name, adults, children, food_preference, total_cost, travel_date, package_place)

    # Respond with a confirmation message
    return response


# Example route to render the booking form
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    # Check if the user is logged in
    if 'username' not in session:
        flash('You need to log in to make a booking.', 'danger')
        return redirect(url_for('login'))  # Redirect to the login page

    if request.method == 'GET':
        # Get the package details passed from the URL
        package_id = request.args.get('package_id')
        price = request.args.get('price')
        destination = request.args.get('destination')

        # Get the logged-in username from the session
        username = session.get('username')

        # Pass the data to the booking template
        return render_template('booking.html', price=price, destination=destination)

    if request.method == 'POST':
        # Handle the booking form submission
        booking_data = request.get_json()

        # Extract booking details from the submitted data
        user_name = booking_data['userName']
        package_place = booking_data['packagePlace']
        adults = booking_data['adults']
        children = booking_data['children']
        total_cost = booking_data['totalCost']
        food_preference = booking_data['foodPreference']
        travel_date = booking_data['travelDate']

        # Save the booking or process further
        save_booking_to_history(user_name, adults, children, food_preference, total_cost, travel_date, package_place)
        return jsonify({"message": "Booking confirmed!"})



def calculate_total_cost(adults, children, food_preference):
    veg_food_cost = 100
    non_veg_food_cost = 200
    adult_cost = 500  # Example adult cost (you can use the package price)
    child_cost = adult_cost / 2  # Child cost is half of adult cost

    total = (adults * adult_cost) + (children * child_cost)

    if food_preference == "veg":
        total += (adults + children) * veg_food_cost
    else:
        total += (adults + children) * non_veg_food_cost

    return total


# logging.basicConfig(level=logging.DEBUG)


@app.route('/detect_location')
def detect_location():
    return render_template('detect_location.html')

@app.route('/get_packages')
def get_packages():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))

    nearby_packages = []
    
    packages = load_packages()
    
    for pkg in packages:
        distance = calculate_distance(lat, lon, pkg['lat'], pkg['lon'])
        if distance <= 100:  # Show packages within 100 km radius
            nearby_packages.append({'destination': pkg['destination'], 'distance': round(distance, 2)})

    return jsonify(nearby_packages)

@app.route('/travel_packages')
def travel_packages():
    return render_template('travel_packages.html')

# Route to view the booking history
@app.route('/booking_history')
def booking_history():
    # Check if the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    user_name = session['username']

    try:
        # Open the booking history file
        with open(BOOKING_HISTORY_FILE, 'r') as file:
            bookings = json.load(file)

        # Filter bookings for the logged-in user
        user_bookings = [booking for booking in bookings if booking['user'] == user_name]

        return render_template('booking_history.html', bookings=user_bookings)

    except FileNotFoundError:
        # If the file doesn't exist, display a message
        return render_template('booking_history.html', bookings=[], message="No booking history found.")

    except json.JSONDecodeError:
        # If there's an error reading the JSON file
        return render_template('booking_history.html', bookings=[], message="Error reading booking history.")


# --------------------------------------------------------------------------------------------->

import pandas as pd 
import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import hashlib

app.secret_key = os.urandom(24)  # Secret key for session management

df = pd.read_csv('India Cities LatLng.csv')

# Display the columns to debug
print(df.columns)


# Ensure the 'static/images' folder exists
UPLOAD_FOLDER = 'static/images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # Create the directory if it doesn't exist

# Set the upload folder in Flask config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Load travel details from JSON file
def load_data():
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump([], f)
    with open("data.json", "r") as f:
        return json.load(f)

# Save travel details to JSON file
def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# Function to get latitude and longitude
def get_lat_lng(destination):
    destination = destination.lower()
    matching_row = df[df['city'].str.lower() == destination]
    if not matching_row.empty:
        lat = matching_row.iloc[0]['lat']
        lng = matching_row.iloc[0]['lng']
        return lat, lng
    else:
        return None, None

# Helper functions for user authentication
USERS_DB = 'admin.json'

def load_users():
    if not os.path.exists(USERS_DB):
        return {}
    with open(USERS_DB, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(USERS_DB, 'w') as file:
        json.dump(users, file, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(stored_hash, password):
    return stored_hash == hash_password(password)

@app.route("/admin_index", methods=["GET", "POST"])
def admin_index():
    # Ensure the user is logged in
    if 'username' not in session:
        flash("Please log in to access the travel packages.")
        return redirect(url_for('login'))

    # If there are any POST requests, you can handle them here (e.g., form submissions)
    if request.method == "POST":
        # Handle any POST logic here, if needed (this part can be customized)
        pass

    # Load travel data (travel packages available)
    travel_data = load_data()

    # Load booking history from the JSON file
    try:
        with open(BOOKING_HISTORY_FILE, 'r') as file:
            bookings = json.load(file)  # Read existing bookings
    except (FileNotFoundError, json.JSONDecodeError):
        bookings = []  # Handle cases where the file doesn't exist or can't be read

    # Pass both the travel data and booking history to the template
    return render_template("admin_index.html", travel_data=travel_data, bookings=bookings)


@app.route("/admin_add", methods=["GET", "POST"])
def add_travel():
    if 'username' not in session:
        flash("You must be logged in to add travel packages.")
        return redirect(url_for('admin_login'))

    if request.method == "POST":
        travel_data = load_data()

        # Get the destination from the form
        destination = request.form["destination"]

        # Check if the destination already exists (case-insensitive check)
        if any(item['destination'].lower() == destination.lower() for item in travel_data):
            flash(f"The destination '{destination}' already exists. Please choose a different one.", "error")
            return redirect(url_for('add_travel'))

        # If destination is not a duplicate, proceed to add the new travel package
        new_id = len(travel_data) + 1
        description = request.form["description"]
        price = request.form["price"]
        
        try:
            price = float(price)
            if price < 0:
                raise ValueError("Price must be a positive number.")
        except ValueError as e:
            return f"Invalid price: {e}", 400
        
        lat, lng = get_lat_lng(destination)
        
        image_filename = None
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                image_filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        if lat is not None and lng is not None:
            new_package = {
                "id": new_id,
                "destination": destination,
                "description": description,
                "price": price,
                "latitude": lat,
                "longitude": lng,
                "image": image_filename
            }
            travel_data.append(new_package)
            save_data(travel_data)
            flash(f"The travel package for {destination} has been added successfully!", "success")
            return redirect(url_for("admin_index"))
        else:
            error_message = "Destination not found in dataset!"
            return render_template("admin_add.html", error_message=error_message)
    
    return render_template("admin_add.html")


@app.route("/admin_edit/<int:id>", methods=["GET", "POST"])
def edit_travel(id):
    if 'username' not in session:
        flash("You must be logged in to edit travel packages.")
        return redirect(url_for('admin_login'))

    travel_data = load_data()
    travel = next((item for item in travel_data if item["id"] == id), None)
    
    if request.method == "POST" and travel:
        travel["destination"] = request.form["destination"]
        travel["description"] = request.form["description"]
        travel["price"] = request.form["price"]
        
        lat, lng = get_lat_lng(travel["destination"])
        travel["latitude"] = lat
        travel["longitude"] = lng
        
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                image_filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                travel["image"] = image_filename
        
        save_data(travel_data)
        return redirect(url_for("admin_index"))
    
    return render_template("admin_edit.html", travel=travel)

@app.route("/delete/<int:id>", methods=["POST"])
def delete_travel(id):
    if 'username' not in session:
        flash("You must be logged in to delete travel packages.")
        return redirect(url_for('admin_login'))

    travel_data = load_data()
    travel_data = [item for item in travel_data if item["id"] != id]
    save_data(travel_data)
    return redirect(url_for("admin_index"))

# Routes for user authentication
@app.route('/admin')
def admin_home():
    return redirect(url_for('admin_login'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_users()

        if username in users and check_password(users[username]['password'], password):
            session['username'] = username
            return redirect(url_for('admin_index'))  # Redirect to index page after login
        else:
            flash("Invalid credentials, please try again.")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('admin_register'))

        users = load_users()

        if username in users:
            flash("Username already exists!")
            return redirect(url_for('admin_register'))

        users[username] = {
            'username': username,
            'password': hash_password(password)
        }

        save_users(users)
        flash("Registration successful! You can now log in.")
        return redirect(url_for('admin_login'))

    return render_template('admin_register.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('username', None)
    return redirect(url_for('admin_login'))

# ============================================================================================>

from flask import Flask, render_template, request, jsonify
from math import radians, sin, cos, sqrt, atan2
import json
import os
import logging



# Function to load locations from JSON file
def load_locations_from_json(file_path='data.json'):
    locations = []
    if not os.path.exists(file_path):
        print(f"Error: The JSON file at '{file_path}' does not exist.")
        return []

    try:
        # Open the JSON file and load the data
        with open(file_path, 'r', encoding='utf-8') as file:
            locations = json.load(file)

        # Validate the data (check if each entry has 'destination', 'latitude', and 'longitude')
        for location in locations:
            if 'destination' not in location or 'latitude' not in location or 'longitude' not in location:
                print(f"Invalid data found in entry: {location}")
                locations.remove(location)

        if not locations:
            print("No valid locations loaded from the JSON.")
        return locations
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return []

# Function to calculate the great-circle distance between two points on Earth
def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Difference in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Distance in kilometers
    distance = R * c
    return distance

# @app.route('/geo')
# def index():
#     return render_template('detect_location.html')

# logging.basicConfig(level=logging.DEBUG)

@app.route('/get_nearest_location', methods=['POST'])
def get_nearest_location():
    data = request.get_json()
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')

    logging.debug(f"Received request data: latitude={user_lat}, longitude={user_lon}")

    if not user_lat or not user_lon:
        return jsonify({"message": "Invalid location data"}), 400

    # Load locations from the JSON file
    locations = load_locations_from_json()

    if not locations:
        return jsonify({"message": "No locations found in JSON file"}), 500

    # List to store cities with their distances
    distance_list = []

    for location in locations:
        try:
            lat = location['latitude']
            lon = location['longitude']
            distance = haversine(user_lat, user_lon, lat, lon)
            distance_list.append({
                "id": location["id"],
                "name": location["destination"],
                "latitude": lat,
                "longitude": lon,
                "distance_km": distance,
                "description": location["description"],
                "price": location["price"],
                "image": location["image"]
            })
        except Exception as e:
            logging.error(f"Error processing location {location['destination']}: {e}")
            continue  # Skip this entry if there's an error

    # Sort the cities by distance (ascending order)
    distance_list.sort(key=lambda x: x['distance_km'])

    return jsonify({
        "message": "Nearest locations found",
        "nearest_locations": distance_list
    })

@app.route('/nearest_location')
def nearest_location():
    if 'username' not in session:
        flash('You need to log in to view locations.', 'danger')
        return redirect(url_for('login'))  # Redirect to login if not logged in
    
    username = session.get('username')  # Get the username from session
    return render_template('nearest_location.html', username=username)

@app.route('/get_username', methods=['GET'])
def get_username():
    if 'username' in session:
        return jsonify({'username': session['username']})
    else:
        return jsonify({'username': None})



if __name__ == '__main__':
    app.run(debug=True)

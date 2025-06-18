import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin
from dotenv import load_dotenv
from netmiko import ConnectHandler
from werkzeug.security import generate_password_hash, check_password_hash

import inventory_tool

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
socketio = SocketIO(app)

connections = {}

login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

USERNAME = os.environ.get("APP_USERNAME", "admin")
PASSWORD = os.environ.get("APP_PASSWORD", "admin")

test_user = User("1", USERNAME, PASSWORD)
users = {test_user.id: test_user}

def convert_inventory_device(device_data):
    return {
        "device_type": "cisco_ios",
        "host": device_data["Management IP"],
        "username": device_data["Username"],
        "password": device_data["Password"],
        "secret": device_data["Password"],
    }

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = next((u for u in users.values() if u.username == username), None)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    inventory = inventory_tool.read_inventory("inventory.csv")
    device_names = [device["Name"] for device in inventory]
    return render_template("index.html", devices=device_names)

@socketio.on("connect_to_device")
@login_required
def handle_connect(data):
    device_id = data["device_id"]
    inventory = inventory_tool.read_inventory("inventory.csv")
    device_data = inventory_tool.get_device_data(inventory, device_id)

    if not device_data:
        emit("console_output", {"data": "Invalid device selection"})
        return

    device_config = convert_inventory_device(device_data)

    try:
        conn = ConnectHandler(**device_config)
        conn.enable()
        prompt = conn.find_prompt()
        connections[request.sid] = {"connection": conn, "history": [], "current_history_pos": -1}
        emit("console_output", {"data": f"Connected to {device_id}\r\n{prompt}"})
    except Exception as e:
        emit("console_output", {"data": f"Connection failed: {str(e)}\r\n"})

@socketio.on("command")
@login_required
def handle_command(data):
    if request.sid not in connections:
        return

    conn = connections[request.sid]
    command = data["command"].strip()
    if not command:
        return

    try:
        output = conn["connection"].send_command_timing(command, delay_factor=1)
        prompt = conn["connection"].find_prompt()
        conn["history"].append(command)
        emit("console_output", {"data": f"{output}\r\n{prompt}"})
    except Exception as e:
        emit("console_output", {"data": f"Error: {str(e)}\r\n"})

@socketio.on("disconnect")
def handle_disconnect():
    if request.sid in connections:
        connections[request.sid]["connection"].disconnect()
        del connections[request.sid]

if __name__ == "__main__":
    socketio.run(app, debug=True)
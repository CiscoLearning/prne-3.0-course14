import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from netmiko import ConnectHandler

import inventory_tool

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
socketio = SocketIO(app)

connections = {}

def convert_inventory_device(device_data):
    return {
        "device_type": "cisco_ios",
        "host": device_data["Management IP"],
        "username": device_data["Username"],
        "password": device_data["Password"],
        "secret": device_data["Password"],
    }

@app.route("/")
def index():
    inventory = inventory_tool.read_inventory("inventory.csv")
    device_names = [device["Name"] for device in inventory]
    return render_template("index.html", devices=device_names)

@socketio.on("connect_to_device")
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
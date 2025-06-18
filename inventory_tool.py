import csv
import json
import yaml
import argparse
import sys

def read_inventory(filename):
    inventory_data_list = []  
    with open(filename, "r") as file:
        for row in csv.DictReader(file):  
            inventory_data_list.append(row)  
    return inventory_data_list  

def get_device_data(inventory, device_name):
    for device in inventory:  
        if device["Name"] == device_name:  
            return device  
    return None  

def format_inventory_json(inventory_data):    
    inventory_json = json.dumps(inventory_data, indent = 4)
    return inventory_json 

def format_inventory_yaml(inventory_data):
    inventory_yaml = yaml.dump(inventory_data, indent = 4)
    return inventory_yaml

def add_device(inventory, new_device):
    inventory.append(new_device)

def remove_device(inventory, device_name):
    for device in inventory:
        if device["Name"] == device_name:
            inventory.remove(device)

def save_inventory(filename, inventory):
    fieldnames = ["Name", "Management IP", "Username", "Password", "Description"]    
    with open(filename, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(inventory)

if __name__ == "__main__":
    inventory_data = read_inventory("inventory.csv")
    R1_data = get_device_data(inventory_data, "R1-Core")

    parser = argparse.ArgumentParser(description="Manage network device inventory")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Add a new device")
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--ip", required=True)
    add_parser.add_argument("--user", required=True)
    add_parser.add_argument("--password", required=True)  # Fixed "pass" issue
    add_parser.add_argument("--desc", required=True)

    remove_parser = subparsers.add_parser("remove", help="Remove a device")
    remove_parser.add_argument("--name", required=True)

    save_parser = subparsers.add_parser("save", help="Save the current inventory to file")

    args = parser.parse_args()

    if args.command is None:
        print(inventory_data)
        sys.exit(0)

    if args.command == "add":
        new_device = {
            "Name": args.name,
            "Management IP": args.ip,
            "Username": args.user,
            "Password": args.password,
            "Description": args.desc
        }
        add_device(inventory_data, new_device)
        save_inventory("inventory.csv", inventory_data)
        print(f"Device '{args.name}' added and saved!")

    elif args.command == "remove":
        remove_device(inventory_data, args.name)
        save_inventory("inventory.csv", inventory_data)
        print(f"Device '{args.name}' removed and saved!")

    elif args.command == "save":
        save_inventory("inventory.csv", inventory_data)
        print("Inventory saved successfully!")
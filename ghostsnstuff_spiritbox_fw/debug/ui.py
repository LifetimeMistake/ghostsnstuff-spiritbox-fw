import requests
import json
from datetime import datetime

# API
SERVER_API_URL = "http://localhost:8080"

def load_current_scenario():
    response = requests.get(f"{SERVER_API_URL}/scenario/current")
    return response.json() if response.ok else {}

def start_scenario(base_scenario_name=None, custom_scenario=None):
    payload = {"base_scenario_name": base_scenario_name, "custom_scenario": custom_scenario}
    response = requests.post(f"{SERVER_API_URL}/scenario/start", json=payload)
    return response.json() if response.status_code == 200 else None

def stop_scenario():
    response = requests.post(f"{SERVER_API_URL}/scenario/stop")
    return response.json() if response.status_code == 200 else None

def load_base_prompts():
    response = requests.get(f"{SERVER_API_URL}/scenario/base_prompts")
    return response.json() if response.ok else []

def generate_new_scenario(base_scenario, prompt):
    response = requests.post(f"{SERVER_API_URL}/scenario/generate", json={
        "base_scenario": base_scenario,
        "prompt": prompt
    })
    return response.json() if response.ok else {"error": "Failed to generate scenario"}

def system_call(command):
    response = requests.post(f"{SERVER_API_URL}/system/call", json={"command": command})
    return response.json() if response.ok else {"error": "Failed to send command"}

def load_event_log():
    response = requests.get(f"{SERVER_API_URL}/events")
    return response.json() if response.ok else []


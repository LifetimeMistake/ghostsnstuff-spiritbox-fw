import requests
import json
import streamlit as st
from datetime import datetime

# API
SERVER_API_URL = "http://localhost:8080"

@st.cache_data
def get_base_scenarios():
    response = requests.get(f"{SERVER_API_URL}/scenario/base_scenarios")
    return response.json() if response.ok else []

def get_current_scenario():
    response = requests.get(f"{SERVER_API_URL}/scenario/current")
    return response.json() if response.ok else {}

def start_scenario(base_scenario_name=None, custom_scenario=None):
    payload = {"base_scenario_name": base_scenario_name, "custom_scenario": custom_scenario}
    response = requests.post(f"{SERVER_API_URL}/scenario/start", json=payload)
    return response.json() if response.status_code == 200 else None

def stop_scenario():
    response = requests.post(f"{SERVER_API_URL}/scenario/stop")
    return response.json() if response.status_code == 200 else None

def generate_scenario(base_scenario, prompt):
    response = requests.post(f"{SERVER_API_URL}/scenario/generate", json={
        "base_scenario": base_scenario,
        "prompt": prompt
    })
    return response.json() if response.ok else {"error": "Failed to generate scenario"}

def system_call(command):
    response = requests.post(f"{SERVER_API_URL}/system/call", json={"command": command})
    return response.json() if response.ok else {"error": "Failed to send command"}

def get_event_log():
    response = requests.get(f"{SERVER_API_URL}/events")
    return response.json() if response.ok else []

def display_scenario_details(scenario):
    st.write("### Game Scenario Overview")
    st.write(f"**Scenario Type**: {scenario['scenario_type']}")
    st.write(f"**Scenario Description**: {scenario['scenario_description']}")
    
    def display_ghost_details(ghost, title):
        st.write(f"#### {title}")
        st.write(f"- **Name**: {ghost['name']}")
        st.write(f"- **Personality**: {ghost['personality']}")
        st.write(f"- **Backstory**: {ghost['backstory']}")
        st.write(f"- **Goals**: {ghost['goals']}")
        
        if ghost["hints"]:
            st.write("- **Example Responses**:")
            for hint in ghost["hints"]:
                st.write(f"  - {hint}")
        
        if ghost.get("ritual"):
            st.write("- **Ritual**:")
            ritual = ghost["ritual"]
            st.write(f"  - **Name**: {ritual['name']}")
            st.write(f"  - **Description**: {ritual['description']}")
            st.write(f"  - **Phrase**: '{ritual['phrase']}'")
        
        if ghost.get("key_memories"):
            st.write("- **Key Memories**:")
            for memory in ghost["key_memories"]:
                st.write(f"  - **Memory**: {memory['memory']}")
                st.write(f"    - **Hint**: {memory['hint']}")
                st.write(f"    - **Solution**: {memory['solution']}")

    # Display Primary and Secondary Ghosts
    display_ghost_details(scenario["primary_ghost"], "Primary Ghost")
    display_ghost_details(scenario["secondary_ghost"], "Secondary Ghost")
    
    st.write("#### Shared Lore")
    st.write(scenario["shared_lore"])

    st.write("#### Final Goal")
    final_goal = scenario["final_goal"]
    st.write(f"- **Description**: {final_goal['description']}")
    
    if final_goal.get("ritual"):
        st.write("- **Ritual**:")
        ritual = final_goal["ritual"]
        st.write(f"  - **Name**: {ritual['name']}")
        st.write(f"  - **Description**: {ritual['description']}")
        st.write(f"  - **Phrase**: '{ritual['phrase']}'")

# Streamlit app layout
st.title("Spirit Box Debug UI")
tabs = st.tabs(["Scenario Selection", "Current Scenario", "System Call", "Event Log"])

# Scenario Tab
with tabs[0]:
    st.header("Scenario Management")

    # Start Scenario Options
    st.subheader("Start a New Scenario")
    base_scenarios = get_base_scenarios()
    
    # Option to start a scenario from a base scenario or custom JSON
    scenario_type = st.radio("Choose Scenario Type:", ("Base Scenario", "Custom Scenario JSON"))

    if scenario_type == "Base Scenario":
        base_scenario_choice = st.selectbox("Select Base Scenario:", base_scenarios)
        if st.button("Start Base Scenario") and base_scenario_choice:
            result = start_scenario(base_scenario_name=base_scenario_choice)
            st.write("Scenario started successfully" if result else "Failed to start scenario")

    elif scenario_type == "Custom Scenario JSON":
        custom_scenario_json = st.text_area("Paste Custom Scenario JSON here")
        if st.button("Start Custom Scenario"):
            try:
                custom_scenario_data = json.loads(custom_scenario_json)
                result = start_scenario(custom_scenario=custom_scenario_data)
                st.write("Custom scenario started successfully" if result else "Failed to start custom scenario")
            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please correct and try again.")

    # Stop Scenario Button
    st.subheader("Stop Scenario")
    if st.button("Stop Current Scenario"):
        result = stop_scenario()
        st.write("Scenario stopped successfully" if result else "Failed to stop scenario")

    # Generate a new scenario based on prompt input
    st.subheader("Generate New Scenario")
    base_prompt = st.selectbox("Select Base Prompt:", base_scenarios)
    custom_prompt = st.text_input("Enter Custom Prompt:")

    if st.button("Generate Scenario"):
        generated_scenario = generate_scenario(base_prompt, custom_prompt)
        st.json(generated_scenario if generated_scenario else "Failed to generate scenario")

    # Generate and Start Button
    if st.button("Generate and Start Scenario"):
        generated_scenario = generate_scenario(base_prompt, custom_prompt)
        if generated_scenario:
            start_result = start_scenario(custom_scenario=generated_scenario)
            st.write("Scenario generated and started successfully" if start_result else "Failed to start generated scenario")
            st.json(generated_scenario)
        else:
            st.write("Failed to generate scenario")

# Current Scenario Details Tab
with tabs[1]:
    st.header("Current Scenario Details")
    if st.button("Refresh Current Scenario"):
        current_scenario = get_current_scenario()
        if current_scenario:
            display_scenario_details(current_scenario)
        else:
            st.write("No current scenario data available.")

# System Tab
with tabs[2]:
    st.header("System Commands")
    st.write("Send commands to the Curator for system-level control and operations.")
    command = st.text_input("Enter Command:")
    if st.button("Execute Command"):
        result = system_call(command)
        st.write(result["curator_response"] if result else "Failed to execute command")

# Event Log Tab
def display_event(event):
    """Displays a formatted view of common event types."""
    event_type = event.get("type")
    if event_type == "log":
        return f"{event['level']}: {event['message']}"
    elif event_type == "ghost_call":
        return f"Ghost Action - Speech: {event.get('speech', 'None')}"
    elif event_type == "system_call":
        return f"System Call: {event['system_query']} - Response: {event['system_response']}"
    else:
        return None  # Unknown event types handled in JSON format below

with tabs[3]:
    st.header("Event Log")
    st.button("Refresh Event Log")
    
    events = get_event_log()[-50:]
    if events:
        for event in events:
            formatted_event = display_event(event)
            if formatted_event:
                if len(formatted_event) > 64:
                    title_content = f"{formatted_event[:64]}..."
                    body_content = f"...{formatted_event[64:]}"
                else:
                    title_content = formatted_event
                    body_content = formatted_event
                    
                with st.expander(f"{event['timestamp']} - {event['actor']} - {title_content}"):
                    st.write(body_content)
            else:
                with st.expander(f"{event['timestamp']} - {event['actor']} - {event['type']}"):
                    st.json(event)
    else:
        st.write("No events found.")

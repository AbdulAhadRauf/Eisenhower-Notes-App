import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
from models import UrgencyEnum, ImportanceEnum, TimeFrameEnum
from typing import Optional

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"  # Replace with your FastAPI backend URL

# --- Helper Functions ---
def get_auth_headers():
    """Returns authorization headers if a token is available."""
    if "token" in st.session_state:
        return {"Authorization": f"Bearer {st.session_state['token']}"}
    return {}

def login_user(username, password):
    """Logs in a user and returns the token."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        st.error(f"Login failed: {err.response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
        return None


def register_user(username, email, password):
    """Registers a new user."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/register",
            json={"username": username, "email": email, "password": password}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        st.error(f"Registration failed: {err.response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
        return None


def get_tasks(completed: Optional[bool] = None):
    """Fetches tasks for the current user, optionally filtering by completion status."""
    headers = get_auth_headers()
    if not headers:
        return []
    
    url = f"{API_BASE_URL}/tasks/"
    params = {}
    if completed is not None:
        params['completed'] = completed

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not fetch tasks: {e}")
        return []

def create_task(title, description, urgency, importance, time_frame):
    """Creates a new task."""
    headers = get_auth_headers()
    if not headers:
        return None
    try:
        response = requests.post(
            f"{API_BASE_URL}/tasks/",
            headers=headers,
            json={
                "title": title,
                "description": description,
                "urgency": urgency,
                "importance": importance,
                "time_frame": time_frame,
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not create task: {e}")
        return None

def update_task(task_id: int, task_update: dict):
    """Updates an existing task with the given data."""
    headers = get_auth_headers()
    if not headers:
        return None
    try:
        response = requests.put(
            f"{API_BASE_URL}/tasks/{task_id}",
            headers=headers,
            json=task_update
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not update task: {e}")
        return None

def delete_task(task_id):
    """Deletes a task."""
    headers = get_auth_headers()
    if not headers:
        return None
    try:
        response = requests.delete(f"{API_BASE_URL}/tasks/{task_id}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Could not delete task: {e}")
        return False

def plot_task_matrix(tasks):
    """Generates an Eisenhower Matrix plot for the given tasks."""
    if not tasks:
        st.info("No active tasks to visualize. Create some tasks first!")
        return None

    df = pd.DataFrame(tasks)

    # Define the 4 quadrants
    quadrants = {
        "do": df[(df['urgency'] == 'urgent') & (df['importance'] == 'important')],
        "schedule": df[(df['urgency'] == 'not_urgent') & (df['importance'] == 'important')],
        "delegate": df[(df['urgency'] == 'urgent') & (df['importance'] == 'not_important')],
        "eliminate": df[(df['urgency'] == 'not_urgent') & (df['importance'] == 'not_important')],
    }

    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Eisenhower Task Matrix', fontsize=20, weight='bold')

    # Define quadrant properties
    quadrant_props = {
        'do': {'ax': axs[0, 0], 'title': 'Do First', 'color': '#FFD2D2'},
        'schedule': {'ax': axs[0, 1], 'title': 'Schedule', 'color': '#D2EFFF'},
        'delegate': {'ax': axs[1, 0], 'title': 'Delegate', 'color': '#FFFFD2'},
        'eliminate': {'ax': axs[1, 1], 'title': 'Eliminate', 'color': '#E0E0E0'},
    }

    for q_name, q_data in quadrants.items():
        ax = quadrant_props[q_name]['ax']
        ax.set_title(quadrant_props[q_name]['title'], fontsize=16, weight='bold', pad=5)
        ax.set_facecolor(quadrant_props[q_name]['color'])

        # Display tasks in the quadrant
        y_pos = 0.9
        for _, task in q_data.iterrows():
            time_frame_abbr = "(S)" if task['time_frame'] == 'short_term' else "(L)"
            task_text = f"• {task['title']} {time_frame_abbr}"
            
            wrapped_text = "\n".join(textwrap.wrap(task_text, width=100))
            
            ax.text(0.02, y_pos, wrapped_text, va='top', ha='left', fontsize=10, wrap=True)
            y_pos -= 0.07

        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    return fig

# --- Streamlit UI ---
st.set_page_config(page_title="Task Manager", layout="wide")

st.title("Task Manager")

# --- Authentication ---
if "token" not in st.session_state:
    st.sidebar.title("Authentication")
    auth_tab, register_tab = st.sidebar.tabs(["Login", "Register"])

    with auth_tab:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

            if login_button:
                if not username or not password:
                    st.warning("Please enter both username and password.")
                else:
                    token_data = login_user(username, password)
                    if token_data:
                        st.session_state["token"] = token_data["access_token"]
                        st.session_state["username"] = username
                        st.success("Logged in successfully!")
                        st.rerun()


    with register_tab:
        st.subheader("Register")
        with st.form("register_form"):
            new_username = st.text_input("New Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("New Password", type="password")
            register_button = st.form_submit_button("Register")

            if register_button:
                if not new_username or not new_email or not new_password:
                    st.warning("Please fill out all fields.")
                else:
                    new_user = register_user(new_username, new_email, new_password)
                    if new_user:
                        st.success("Registration successful! Please login.")


else:
    # --- Main Application ---
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    if st.sidebar.button("Logout"):
        del st.session_state["token"]
        del st.session_state["username"]
        st.rerun()

    active_tasks = get_tasks(completed=False)
    
    active_tab, matrix_tab, history_tab = st.tabs(["Active Tasks", "Task Matrix", "History"])

    with active_tab:
        st.header("Your Active Tasks")
        if not active_tasks:
            st.info("You have no active tasks. Create one below!")
        else:
            for task in active_tasks:
                with st.expander(f"**{task['title']}** | {' '.join(task['urgency'].split('_')).title()} | {' '.join(task['importance'].split('_')).title()}"):
                    st.write(task['description'])
                    st.write(f"Time Frame: {task['time_frame']}")

                    # --- Action Buttons ---
                    b_col1, b_col2, b_col3 = st.columns([0.2, 0.2, 0.6])
                    with b_col1:
                        if st.button("Mark as Done", key=f"done_{task['id']}", type="primary"):
                            update_task(task['id'], {"completed": True})
                            st.rerun()
                    with b_col2:
                        if st.button("Delete", key=f"delete_{task['id']}"):
                            if delete_task(task['id']):
                                st.success(f"Task '{task['title']}' deleted.")
                                st.rerun()
                    
                    # --- Update Form ---
                    with st.form(f"update_form_{task['id']}"):
                        st.subheader("Edit Task")
                        updated_title = st.text_input("Title", value=task['title'], key=f"title_{task['id']}")
                        updated_description = st.text_area("Description", value=task['description'], key=f"desc_{task['id']}")
                        updated_urgency = st.selectbox("Urgency", options=[e.value for e in UrgencyEnum], index=[e.value for e in UrgencyEnum].index(task['urgency']), key=f"urgency_{task['id']}")
                        updated_importance = st.selectbox("Importance", options=[e.value for e in ImportanceEnum], index=[e.value for e in ImportanceEnum].index(task['importance']), key=f"importance_{task['id']}")
                        updated_time_frame = st.selectbox("Time Frame", options=[e.value for e in TimeFrameEnum], index=[e.value for e in TimeFrameEnum].index(task['time_frame']), key=f"time_frame_{task['id']}")

                        if st.form_submit_button("Update Task"):
                            update_data = {
                                "title": updated_title,
                                "description": updated_description,
                                "urgency": updated_urgency,
                                "importance": updated_importance,
                                "time_frame": updated_time_frame,
                            }
                            updated_task = update_task(task['id'], update_data)
                            if updated_task:
                                st.success("Task updated successfully!")
                                st.rerun()

        st.header("Create New Task")
        with st.form("new_task_form", clear_on_submit=True):
            title = st.text_input("Title")
            description = st.text_area("Description")
            urgency = st.selectbox("Urgency", options=[e.value for e in UrgencyEnum])
            importance = st.selectbox("Importance", options=[e.value for e in ImportanceEnum])
            time_frame = st.selectbox("Time Frame", options=[e.value for e in TimeFrameEnum])
            submit_button = st.form_submit_button("Create Task")

            if submit_button:
                 if not all([title, description, urgency, importance, time_frame]):
                     st.warning("Please fill out all fields.")
                 else:
                    new_task = create_task(title, description, urgency, importance, time_frame)
                    if new_task:
                        st.success("Task created successfully!")
                        st.rerun()

    with matrix_tab:
        st.header("Active Task Visualization")
        fig = plot_task_matrix(active_tasks)
        if fig:
            st.pyplot(fig)
            st.markdown("`(S)` - Short Term, `(L)` - Long Term")

    with history_tab:
        st.header("Completed Tasks History")
        completed_tasks = get_tasks(completed=True)
        if not completed_tasks:
            st.info("You have not completed any tasks yet.")
        else:
            for task in completed_tasks:
                h_col1, h_col2 = st.columns([0.8, 0.2])
                with h_col1:
                    st.markdown(f"- **{task['title']}**")
                with h_col2:
                    if st.button("Restore Task", key=f"restore_{task['id']}"):
                        update_task(task['id'], {"completed": False})
                        st.rerun()


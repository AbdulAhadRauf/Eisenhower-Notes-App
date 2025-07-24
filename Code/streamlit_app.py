import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import os
from models import UrgencyEnum, ImportanceEnum, TimeFrameEnum
from typing import Optional, List, Dict, Tuple
import uvicorn
from main import app as fastapi_app
import threading
from datetime import datetime, time

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"
UPLOAD_DIR = "uploads"

# --- FastAPI Server Management ---
if "server_started" not in st.session_state:
    st.session_state.server_started = True
    def run_fastapi():
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000)
    daemon = threading.Thread(target=run_fastapi, daemon=True, name="FastAPI")
    daemon.start()

# --- API Helper Functions ---
def get_auth_headers() -> Dict:
    if "token" in st.session_state:
        return {"Authorization": f"Bearer {st.session_state['token']}"}
    return {}

def handle_api_error(err, context=""):
    """Centralized error handler for API requests."""
    try:
        detail = err.response.json().get('detail', 'Unknown error')
    except (requests.exceptions.JSONDecodeError, AttributeError):
        detail = str(err)
    st.toast(f"{context} failed: {detail}", icon="❌")

# --- Cached Data Fetching ---
@st.cache_data(show_spinner="Fetching tasks...")
def get_tasks(
    completed: Optional[bool] = None,
    search_query: Optional[str] = None,
    urgency_filter: Optional[str] = None,
    importance_filter: Optional[str] = None
) -> List[Dict]:
    headers = get_auth_headers()
    if not headers:
        return []
    
    url = f"{API_BASE_URL}/tasks/"
    params = {}
    if completed is not None:
        params['completed'] = completed
    if search_query:
        params['search_query'] = search_query
    if urgency_filter and urgency_filter != "All":
        params['urgency'] = urgency_filter
    if importance_filter and importance_filter != "All":
        params['importance'] = importance_filter

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "Could not fetch tasks")
        return []

def clear_task_cache():
    """Clears the cache for the get_tasks function."""
    get_tasks.clear()

# --- CRUD Operations ---
def login_user(username, password):
    try:
        response = requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "Login")
        return None

def register_user(username, email, password):
    try:
        response = requests.post(f"{API_BASE_URL}/register", json={"username": username, "email": email, "password": password})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "Registration")
        return None

def create_task_api(task_data):
    try:
        response = requests.post(f"{API_BASE_URL}/tasks/", headers=get_auth_headers(), json=task_data)
        response.raise_for_status()
        clear_task_cache()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "Could not create task")
        return None

def update_task_api(task_id, task_update):
    try:
        response = requests.put(f"{API_BASE_URL}/tasks/{task_id}", headers=get_auth_headers(), json=task_update)
        response.raise_for_status()
        clear_task_cache()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "Could not update task")
        return None

def delete_task_api(task_id):
    try:
        response = requests.delete(f"{API_BASE_URL}/tasks/{task_id}", headers=get_auth_headers())
        response.raise_for_status()
        clear_task_cache()
        return True
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "Could not delete task")
        return False

def upload_file_api(task_id, file, file_type):
    if file is None:
        return None
    try:
        files = {'file': (file.name, file, file.type)}
        response = requests.post(f"{API_BASE_URL}/tasks/{task_id}/upload/{file_type}", headers=get_auth_headers(), files=files)
        response.raise_for_status()
        clear_task_cache()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, f"Could not upload {file_type}")
        return None

# --- UI Components ---
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
        # Abbreviation for time frame
            time_frame_abbr = "(S)" if task['time_frame'] == 'short_term' else "(L)"

            # Default values
            samay = ""
            days_left_text = ""

            if task['deadline']:
                try:
                    samay_dt = datetime.fromisoformat(task['deadline'])
                    samay = samay_dt.strftime('%A %B %d')
                    time_left = (samay_dt.date() - datetime.today().date()).days
                    days_left_text = f"({time_left} days left)" if time_left >= 0 else "(Deadline passed)"
                except ValueError:
                    samay = "Invalid date"
                    days_left_text = ""
            
            # Compose task text
            task_text = f"• {task['title']} {time_frame_abbr}. {samay} {days_left_text}"

            # Wrap text for better display
            wrapped_text = "\n".join(textwrap.wrap(task_text, width=80))

            # Display on your figure (assumes `ax` and `y_pos` are defined)
            ax.text(0.05, y_pos, wrapped_text, va='top', ha='left', fontsize=10, wrap=True)
            y_pos -= 0.07  # Adjust vertical position

        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

    plt.tight_layout(rect=[0, 0, 1, 0.96]) # type: ignore
    return fig

def task_form_logic(task: Optional[Dict] = None) -> Tuple[Optional[Dict], Optional[Tuple], bool]:
    """Renders the form widgets and returns data on submission."""
    is_edit = task is not None
    
    default_title = task['title'] if is_edit else ""
    default_desc = task['description'] if is_edit else ""
    default_urgency = [e.value for e in UrgencyEnum].index(task['urgency']) if is_edit else 0
    default_importance = [e.value for e in ImportanceEnum].index(task['importance']) if is_edit else 0
    default_timeframe = [e.value for e in TimeFrameEnum].index(task['time_frame']) if is_edit else 0
    default_deadline = datetime.fromisoformat(task['deadline']).date() if is_edit and task.get('deadline') else None

    new_title = st.text_input("Title", value=default_title).strip()
    new_description = st.text_area("Description", value=default_desc)
    new_deadline = st.date_input("Deadline (Optional)", value=default_deadline)
    
    c1, c2, c3 = st.columns(3)
    new_urgency = c1.selectbox("Urgency", options=[e.value for e in UrgencyEnum], index=default_urgency)
    new_importance = c2.selectbox("Importance", options=[e.value for e in ImportanceEnum], index=default_importance)
    new_time_frame = c3.selectbox("Time Frame", options=[e.value for e in TimeFrameEnum], index=default_timeframe)
    
    st.subheader("Attachments")
    c1, c2, c3 = st.columns(3)
    image_file = c1.file_uploader("Image", type=['png', 'jpg', 'jpeg'])
    doc_file = c2.file_uploader("Document", type=['pdf', 'doc', 'docx', 'txt'])
    voice_file = c3.file_uploader("Voice Note", type=['mp3', 'wav', 'm4a'])

    if st.button("Save Task" if is_edit else "Create Task", type="primary"):
        if not new_title or not new_description:
            st.warning("Title and Description are required.")
            return None, None, False

        deadline_datetime = datetime.combine(new_deadline, time.min) if new_deadline else None
        
        task_data = {
            "title": new_title, "description": new_description, "urgency": new_urgency,
            "importance": new_importance, "time_frame": new_time_frame,
            "deadline": deadline_datetime.isoformat() if deadline_datetime else None,
        }
        files_to_upload = (image_file, doc_file, voice_file)
        return task_data, files_to_upload, True
        
    return None, None, False

def display_attachment(task_id, file_path, label):
    if file_path and os.path.exists(file_path):
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as file:
            st.download_button(
                label=f"Download {label} ({file_name})",
                data=file, file_name=file_name, key=f"dl_{task_id}_{label}"
            )

# --- Dialog Definitions ---
@st.dialog("Create New Task")
def create_task_dialog():
    task_data, files, submitted = task_form_logic()
    if submitted and task_data and files:
        result = create_task_api(task_data)
        if result:
            st.toast("Task created successfully!", icon="✅")
            task_id = result['id']
            # Only upload if a file was provided
            if files[0]: upload_file_api(task_id, files[0], "image")
            if files[1]: upload_file_api(task_id, files[1], "document")
            if files[2]: upload_file_api(task_id, files[2], "voice")
        st.session_state.show_create_dialog = False
        st.rerun()
    if st.button("Cancel"):
        st.session_state.show_create_dialog = False
        st.rerun()

@st.dialog("Edit Task")
def edit_task_dialog():
    task = st.session_state.get("task_to_edit")
    if not task: return
    
    task_data, files, submitted = task_form_logic(task)
    if submitted and task_data and files:
        result = update_task_api(task['id'], task_data)
        if result:
            st.toast("Task updated successfully!", icon="✅")
            task_id = result['id']
            # Only upload if a file was provided
            if files[0]: upload_file_api(task_id, files[0], "image")
            if files[1]: upload_file_api(task_id, files[1], "document")
            if files[2]: upload_file_api(task_id, files[2], "voice")
        del st.session_state.task_to_edit
        st.rerun()
    if st.button("Cancel"):
        del st.session_state.task_to_edit
        st.rerun()

# --- Main App ---

st.set_page_config(page_title="Task Manager", layout="wide")
st.title("Task Manager")
st.write("by Abdul Ahad Rauf")
st.write(f"Today is: {datetime.today().strftime('%A %B %d')}")

# --- Authentication Flow ---
if "token" not in st.session_state:
    st.header("Authentication")
    auth_tab, register_tab = st.tabs(["Login", "Register"])
    with auth_tab:
        with st.form("login_form"):
            username = st.text_input("Username").strip()
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login", type="primary"):
                token_data = login_user(username, password)
                if token_data:
                    st.session_state["token"] = token_data["access_token"]
                    st.session_state["username"] = username
                    st.rerun()
    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("New Username").strip()
            new_email = st.text_input("Email").strip()
            new_password = st.text_input("New Password", type="password")
            if st.form_submit_button("Register"):
                new_user = register_user(new_username, new_email, new_password)
                if new_user:
                    st.toast("Registration successful! Logging you in...", icon="🎉")
                    token_data = login_user(new_username, new_password)
                    if token_data:
                        st.session_state["token"] = token_data["access_token"]
                        st.session_state["username"] = new_username
                        st.rerun()

else:
    # --- Main Application UI ---
    with st.sidebar:
        st.title(f"Welcome, {st.session_state['username']}!")
        if st.button("Logout", use_container_width=True):
            del st.session_state["token"]
            del st.session_state["username"]
            clear_task_cache()
            st.rerun()
        st.divider()
        if st.button("＋ Create New Task", type="primary", use_container_width=True):
            st.session_state.show_create_dialog = True
            
        st.divider()
        st.subheader("Filter & Search Tasks")
        search_query = st.text_input("Search by Title/Description", key="search_input").strip()
        urgency_options = ["All"] + [e.value for e in UrgencyEnum]
        selected_urgency = st.selectbox("Filter by Urgency", options=urgency_options, key="urgency_filter")
        importance_options = ["All"] + [e.value for e in ImportanceEnum]
        selected_importance = st.selectbox("Filter by Importance", options=importance_options, key="importance_filter")
        
        if st.button("Apply Filters", use_container_width=True):
            clear_task_cache() # Clear cache to refetch with new filters
            st.rerun()


    # --- Dialog Triggers ---
    if st.session_state.get("show_create_dialog"):
        create_task_dialog()
    if st.session_state.get("task_to_edit"):
        edit_task_dialog()

    matrix_tab, active_tab, history_tab = st.tabs(["📊 Task Matrix", "📋 Active Tasks", "📜 History"])

    with matrix_tab:
        st.header("Task Visualization")
        # Pass filters to get_tasks for matrix tab
        active_tasks_for_matrix = get_tasks(
            completed=False, 
            search_query=search_query, 
            urgency_filter=selected_urgency, 
            importance_filter=selected_importance
        )
        fig = plot_task_matrix(active_tasks_for_matrix)
        if fig:
            st.pyplot(fig)
            st.markdown("`(S)` - Short Term, `(L)` - Long Term")

    with active_tab:
        st.header("Your Active Tasks")
        # Pass filters to get_tasks for active tasks tab
        active_tasks = get_tasks(
            completed=False, 
            search_query=search_query, 
            urgency_filter=selected_urgency, 
            importance_filter=selected_importance
        )
        if not active_tasks:
            st.info("You have no active tasks. Create one from the sidebar!")
        else:
            no_of_tasks = len(active_tasks)
            st.write(f" Currents {no_of_tasks} {'Task' if no_of_tasks !=1 else 'Tasks'}")
            for task in active_tasks:
                with st.expander(f"**{task['title']}** | {task['urgency'].replace('_', ' ').title()} & {task['importance'].replace('_', ' ').title()}"):
                    st.write(task['description'])
                    if task.get('deadline'):
                        st.caption(f"Deadline: {datetime.fromisoformat(task['deadline']).strftime('%A, %B %d, %Y')}")
                    
                    display_attachment(task['id'], task.get('image_path'), "Image")
                    display_attachment(task['id'], task.get('document_path'), "Document")
                    display_attachment(task['id'], task.get('voice_note_path'), "Voice Note")
                    st.divider()
                    
                    c1, c2 = st.columns([1,1])
                    if c1.button("Mark as Done ✅", key=f"done_{task['id']}", use_container_width=True):
                        update_task_api(task['id'], {"completed": True})
                        st.toast(f"Task '{task['title']}' completed!", icon="🎉")
                        st.rerun()
                    
                    if c2.button("Edit ✏️", key=f"edit_{task['id']}", use_container_width=True):
                         st.session_state.task_to_edit = task
                         st.rerun()

    with history_tab:
        st.header("Completed Tasks History")
        # Pass filters to get_tasks for history tab
        completed_tasks = get_tasks(
            completed=True, 
            search_query=search_query, 
            urgency_filter=selected_urgency, 
            importance_filter=selected_importance
        )
        if not completed_tasks:
            st.info("You have not completed any tasks yet.")
        else:
            for task in completed_tasks:
                with st.expander(f"~~{task['title']}~~"):
                    st.write(task['description'])
                    c1, c2 = st.columns([1, 6])
                    if c1.button("Restore Task ↩️", key=f"restore_{task['id']}", use_container_width=True):
                        update_task_api(task['id'], {"completed": False})
                        st.toast(f"Task '{task['title']}' restored!", icon="💪")
                        st.rerun()
                    if c2.button("Delete Permanently 🗑️", key=f"delete_{task['id']}", use_container_width=True):
                        if delete_task_api(task['id']):
                            st.toast(f"Task '{task['title']}' permanently deleted.", icon="🗑️")
                            st.rerun()
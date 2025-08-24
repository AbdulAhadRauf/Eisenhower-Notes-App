# Eisenhower Matrix Task Manager

This project is a powerful and intuitive Task Manager application built with FastAPI and Streamlit. It helps users organize their tasks based on the Eisenhower Matrix, a productivity principle for prioritizing tasks by urgency and importance. The application provides a robust backend API and a user-friendly web interface for seamless task management.

## ✨ Features

  - **User Authentication**: Secure user registration and login system using JWT (JSON Web Tokens).
  - **Task Management (CRUD)**: Create, Read, Update, and Delete tasks with titles, descriptions, and priorities.
  - **Eisenhower Matrix Framework**: Classify tasks into four quadrants:
      - Urgent & Important
      - Not Urgent & Important
      - Urgent & Not Important
      - Not Urgent & Not Important
  - **Task Attributes**: Enhance tasks with additional details like `time_frame` (long\_term/short\_term) and optional deadlines.
  - **Interactive Dashboard**: A user-friendly interface built with Streamlit to manage and visualize tasks.
  - **Eisenhower Matrix Visualization**: A graphical representation of tasks in the four-quadrant matrix for a clear overview of priorities.
  - **File Attachments**: Upload and associate images, documents, and voice notes with your tasks.
  - **Advanced Filtering and Searching**: Easily find tasks by their completion status, urgency, importance, or through a text search.
  - **Automated Email Reminders**: A scheduled job runs daily to send email reminders to users about their pending tasks.
  - **Task History**: View and manage completed tasks, with options to restore or permanently delete them.

## 🛠️ Technologies Used

The project is built with a modern Python stack:

  - **Backend**: FastAPI
  - **Frontend**: Streamlit
  - **Database**: SQLAlchemy ORM with PostgreSQL
  - **Authentication**: Passlib for password hashing, python-jose for JWT.
  - **Data Validation**: Pydantic
  - **Asynchronous Server**: Uvicorn
  - **Task Scheduling**: APScheduler
  - **Data Manipulation**: Pandas
  - **Plotting**: Matplotlib

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

  - Python 3.8+
  - PostgreSQL Database

### Installation

1.  **Clone the repository:**

    ```sh
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add the following configuration. Replace the placeholder values with your actual database and email credentials.

    ```env
    # Database Configuration
    DB_USER=your_postgres_user
    DB_PASSWORD=your_postgres_password
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=your_database_name

    # JWT Secret Key
    SECRET_KEY=your_super_secret_key_for_jwt

    # Gmail Configuration for Email Reminders
    GMAIL_USER=your_email@gmail.com
    GMAIL_APP_PASSWORD=your_gmail_app_password
    ```

### Running the Application

Once the setup is complete, you can run the Streamlit application, which will also start the FastAPI server in the background.

```sh
streamlit run streamlit_app.py
```

Navigate to `http://localhost:8501` in your web browser to use the application. The FastAPI backend will be available at `http://localhost:8000`.

## 📝 API Endpoints

The FastAPI backend exposes the following API endpoints. All task-related routes are protected and require authentication.

### Authentication

  - `POST /register`: Register a new user.
  - `POST /login`: Log in and receive a JWT access token.
  - `GET /me`: Get the details of the currently authenticated user.

### Tasks

  - `POST /tasks/`: Create a new task.
  - `GET /tasks/`: Retrieve a list of tasks for the authenticated user.
  - `GET /tasks/{task_id}`: Get a specific task by its ID.
  - `PUT /tasks/{task_id}`: Update an existing task.
  - `DELETE /tasks/{task_id}`: Delete a task.

### File Handling

  - `POST /tasks/{task_id}/upload/{file_type}`: Upload an image, document, or voice note for a task.
  - `GET /download/{task_id}/{filename}`: Download a file associated with a task.

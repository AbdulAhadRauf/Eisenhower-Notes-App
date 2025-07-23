import sqlite3

def transfer_tasks():
    """
    Transfers tasks from tasksold.db to tasks.db.
    It first deletes all existing tasks in tasks.db to avoid ID conflicts,
    then transfers the old tasks, setting their 'completed' status to False.
    """
    old_db = 'tasksold.db'
    new_db = 'tasks.db'
    
    # Initialize connections to None
    old_conn = None
    new_conn = None

    try:
        # Connect to the old and new databases
        old_conn = sqlite3.connect(old_db)
        new_conn = sqlite3.connect(new_db)

        old_cursor = old_conn.cursor()
        new_cursor = new_conn.cursor()

        # --- NEW STEP: Clear the tasks table in the new database ---
        print("Clearing existing tasks from the destination database...")
        new_cursor.execute("DELETE FROM tasks")
        print("Existing tasks cleared.")

        # Fetch all tasks from the old database
        old_cursor.execute("SELECT id, title, description, urgency, importance, time_frame, user_id FROM tasks")
        tasks_to_transfer = old_cursor.fetchall()

        if not tasks_to_transfer:
            print("No tasks found in tasksold.db to transfer.")
            return

        print(f"Found {len(tasks_to_transfer)} tasks to transfer. Starting transfer...")

        # Insert tasks into the new database with 'completed' as False
        for task in tasks_to_transfer:
            # The new 'tasks' table schema is: id, title, description, urgency, importance, time_frame, completed, user_id
            # The old task data provides all except 'completed'
            new_cursor.execute("""
                INSERT INTO tasks (id, title, description, urgency, importance, time_frame, completed, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (task[0], task[1], task[2], task[3], task[4], task[5], False, task[6]))

        # Commit the changes to the new database
        new_conn.commit()
        print(f"✅ Successfully transferred {len(tasks_to_transfer)} tasks!")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        # Ensure connections are closed
        if old_conn:
            old_conn.close()
        if new_conn:
            new_conn.close()
            
        print("Database connections closed.")

if __name__ == "__main__":
    transfer_tasks()
# Student Schedule Reminder Group 1
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import csv
from tkinter import filedialog
import datetime
from pathlib import Path

# USER ACCOUNT
DEFAULT_USERS = {
    "student": {"password": "1234", "fullname": "Student User", "role": "student"},
    "admin": {"password": "admin123", "fullname": "Administrator", "role": "admin"},
    "instructor": {"password": "teach123", "fullname": "Instructor", "role": "instructor"}
}

MANAGER_ROLES = {"admin", "instructor"}
TERM_OPTIONS = ("Prelim", "Midterm")

users = {}
current_user = None
tasks = []
DB_PATH = Path(__file__).with_name("schedule.db")

# ---------------------------------------------
# THEME COLORS
# ---------------------------------------------
PRIMARY = "#4CAF50"
PRIMARY_HOVER = "#45a049"
DANGER = "#e53935"
INFO = "#2196F3"
WARNING = "#FF9800"
TEAL = "#009688"
BG = "#f5f5f5"
CARD_BG = "#ffffff"
DASH_BG = "#eeeeee"

# ---------------------------------------------
# DATABASE HELPERS
# ---------------------------------------------
def ensure_table_columns(cursor, table_name, columns):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing = {row[1] for row in cursor.fetchall()}
    for column_name, definition in columns.items():
        if column_name not in existing:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {definition}")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                fullname TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                section TEXT NOT NULL,
                course TEXT NOT NULL,
                year_level TEXT NOT NULL,
                instructor TEXT NOT NULL,
                term TEXT NOT NULL,
                deadline TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

        ensure_table_columns(cursor, "users", {
            "role": "role TEXT NOT NULL DEFAULT 'student'"
        })

        ensure_table_columns(cursor, "tasks", {
            "section": "section TEXT NOT NULL DEFAULT ''",
            "course": "course TEXT NOT NULL DEFAULT ''",
            "year_level": "year_level TEXT NOT NULL DEFAULT ''",
            "instructor": "instructor TEXT NOT NULL DEFAULT ''",
            "term": "term TEXT NOT NULL DEFAULT 'Prelim'"
        })

        for username, info in DEFAULT_USERS.items():
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (username, password, fullname, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, info["password"], info["fullname"], info["role"])
            )
            cursor.execute(
                "UPDATE users SET role = ? WHERE username = ?",
                (info["role"], username)
            )
        conn.commit()


def load_users():
    global users
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, fullname, role FROM users")
        rows = cursor.fetchall()
    users = {
        row[0]: {
            "password": row[1],
            "fullname": row[2],
            "role": row[3] if row[3] else "student"
        }
        for row in rows
    }

# ---------------------------------------------
# BUTTON HOVER
# ---------------------------------------------
def hover_in(event):
    event.widget.config(bg=PRIMARY_HOVER)

def hover_out(event):
    event.widget.config(bg=PRIMARY)

# ---------------------------------------------
# UPDATE DASHBOARD
# ---------------------------------------------
def update_dashboard():
    total = len(tasks)
    pending = len([t for t in tasks if t["status"] == "Pending"])
    completed = len([t for t in tasks if t["status"] == "Completed"])

    total_label.config(text=f"Total Tasks: {total}")
    pending_label.config(text=f"Pending: {pending}")
    completed_label.config(text=f"Completed: {completed}")

# ---------------------------------------------
# LOGIN WINDOW
# ---------------------------------------------
def open_login_window():
    login = tk.Tk()
    login.title("Login")
    login.geometry("420x350")
    login.configure(bg=BG)
    login.resizable(False, False)

    container = tk.Frame(login, bg=CARD_BG, bd=0, relief="solid")
    container.place(relx=0.5, rely=0.5, anchor="center", width=350, height=300)

    tk.Label(container, text="LOGIN", font=("Segoe UI", 20, "bold"), bg=CARD_BG).pack(pady=15)

    tk.Label(container, text="Username:", font=("Segoe UI", 12), bg=CARD_BG).pack()
    username_entry = tk.Entry(container, width=28, font=("Segoe UI", 12))
    username_entry.pack(pady=3)

    tk.Label(container, text="Password:", font=("Segoe UI", 12), bg=CARD_BG).pack()
    password_entry = tk.Entry(container, width=28, font=("Segoe UI", 12), show="*")
    password_entry.pack(pady=3)

    def login_user():
        global current_user
        username = username_entry.get()
        password = password_entry.get()

        if username in users and users[username]["password"] == password:
            current_user = username
            messagebox.showinfo("Success", f"Welcome {users[username]['fullname']}!")
            login.destroy()
            open_main_window()
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    login_btn = tk.Button(container, text="Login", bg=PRIMARY, fg="white",
                          width=20, height=1, font=("Segoe UI", 12), command=login_user,
                          relief="flat", bd=0)
    login_btn.pack(pady=15)

    login_btn.bind("<Enter>", hover_in)
    login_btn.bind("<Leave>", hover_out)

    tk.Label(container,
             text="© 2025 Group 1\nAll Rights Reserved",
             font=("Segoe UI", 9),
             bg=CARD_BG,
             fg="#666666",
             justify="center").pack(pady=(0, 5))

    login.mainloop()

# ---------------------------------------------
# MAIN SYSTEM WINDOW
# ---------------------------------------------
def open_main_window():
    global total_label, pending_label, completed_label

    window = tk.Tk()
    window.title("Schedule Reminder")
    window.attributes("-fullscreen", True)
    window.configure(bg=BG)
    current_role = users[current_user].get("role", "student")
    can_manage = current_role in MANAGER_ROLES

    # ------------------ PROFILE BAR ------------------
    topbar = tk.Frame(window, bg=CARD_BG, height=60)
    topbar.pack(fill="x")

    tk.Label(topbar,
             text=f"Logged in as: {users[current_user]['fullname']} ({current_role.title()})",
             font=("Segoe UI", 12), bg=CARD_BG).pack(side="right", padx=20)

    def logout():
        window.destroy()
        open_login_window()

    tk.Button(topbar, text="Logout", bg=DANGER, fg="white",
              width=10, font=("Segoe UI", 11), command=logout,
              relief="flat", bd=0).pack(side="right", padx=10, pady=10)

    content_container = tk.Frame(window, bg=BG)
    content_container.pack(fill="both", expand=True)

    canvas = tk.Canvas(content_container, bg=BG, highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(content_container, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)
    outer = tk.Frame(canvas, bg=BG)
    outer_window = canvas.create_window((0, 0), window=outer, anchor="nw")

    outer.grid_columnconfigure(0, weight=1)
    outer.grid_columnconfigure(2, weight=1)
    center = tk.Frame(outer, bg=BG)
    center.grid(row=0, column=1, pady=20, sticky="n")
    center.configure(padx=40)

    def _resize_canvas(event):
        canvas.itemconfig(outer_window, width=event.width)

    canvas.bind("<Configure>", _resize_canvas)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event):
        canvas.unbind_all("<MouseWheel>")

    window.bind("<Destroy>", _unbind_mousewheel)

    def _configure_scrollregion(_event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    outer.bind("<Configure>", _configure_scrollregion)

    # ------------------ TITLE ------------------
    tk.Label(center, text="STUDENT SCHEDULE REMINDER",
             font=("Segoe UI", 30, "bold"), bg=BG, fg="#333").pack(pady=20)

    # ------------------ DASHBOARD ------------------
    dash_frame = tk.Frame(center, bg=BG)
    dash_frame.pack()

    def make_card(parent, title):
        card = tk.Frame(parent, bg=CARD_BG, width=250, height=120)
        card.pack_propagate(False)
        tk.Label(card, text=title, font=("Segoe UI", 16, "bold"), bg=CARD_BG).pack(pady=10)
        return card

    card1 = make_card(dash_frame, "Total Tasks")
    card2 = make_card(dash_frame, "Pending")
    card3 = make_card(dash_frame, "Completed")

    card1.grid(row=0, column=0, padx=20)
    card2.grid(row=0, column=1, padx=20)
    card3.grid(row=0, column=2, padx=20)

    total_label = tk.Label(card1, text="0", font=("Segoe UI", 22), bg=CARD_BG)
    pending_label = tk.Label(card2, text="0", font=("Segoe UI", 22), bg=CARD_BG)
    completed_label = tk.Label(card3, text="0", font=("Segoe UI", 22), bg=CARD_BG)

    total_label.pack()
    pending_label.pack()
    completed_label.pack()

    # ------------------ INPUT AREA ------------------
    input_frame = tk.Frame(center, bg=BG)
    input_frame.pack(pady=20)

    def label(row, text):
        tk.Label(input_frame, text=text, bg=BG,
                 font=("Segoe UI", 14)).grid(row=row, column=0, padx=10, pady=5, sticky="e")

    label(0, "Task / Event:")
    label(1, "Subject:")
    label(2, "Section:")
    label(3, "Course:")
    label(4, "Year Level:")
    label(5, "Instructor:")
    label(6, "Term (Prelim/Midterm):")
    label(7, "Due Date (YYYY-MM-DD):")
    label(8, "Deadline (hh:mm AM/PM):")

    task_name_entry = tk.Entry(input_frame, width=40, font=("Segoe UI", 12))
    subject_entry = tk.Entry(input_frame, width=40, font=("Segoe UI", 12))
    section_entry = tk.Entry(input_frame, width=40, font=("Segoe UI", 12))
    course_entry = tk.Entry(input_frame, width=40, font=("Segoe UI", 12))
    year_entry = tk.Entry(input_frame, width=40, font=("Segoe UI", 12))
    instructor_entry = tk.Entry(input_frame, width=40, font=("Segoe UI", 12))
    term_var = tk.StringVar(value=TERM_OPTIONS[0])
    term_combo = ttk.Combobox(input_frame, width=37, font=("Segoe UI", 12),
                              textvariable=term_var, state="readonly", values=TERM_OPTIONS)
    date_entry = tk.Entry(input_frame, width=40, font=("Segoe UI", 12))
    time_entry = tk.Entry(input_frame, width=40, font=("Segoe UI", 12))

    task_name_entry.grid(row=0, column=1)
    subject_entry.grid(row=1, column=1)
    section_entry.grid(row=2, column=1)
    course_entry.grid(row=3, column=1)
    year_entry.grid(row=4, column=1)
    instructor_entry.grid(row=5, column=1)
    term_combo.grid(row=6, column=1)
    date_entry.grid(row=7, column=1)
    time_entry.grid(row=8, column=1)

    def refresh_task_table():
        task_list.delete(*task_list.get_children())
        for task in tasks:
            task_list.insert(
                "",
                "end",
                iid=str(task["id"]),
                values=(
                    task["name"],
                    task["subject"],
                    task["section"],
                    task["course"],
                    task["year_level"],
                    task["instructor"],
                    task["term"],
                    task["deadline"],
                    task["status"],
                )
            )
        update_dashboard()

    def load_tasks_from_db(refresh_ui=True):
        tasks.clear()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, subject, section, course, year_level, instructor, term, deadline, status
                FROM tasks
                ORDER BY id
                """
            )
            for row in cursor.fetchall():
                tasks.append({
                    "id": row[0],
                    "name": row[1],
                    "subject": row[2],
                    "section": row[3],
                    "course": row[4],
                    "year_level": row[5],
                    "instructor": row[6],
                    "term": row[7],
                    "deadline": row[8],
                    "status": row[9]
                })
        if refresh_ui:
            refresh_task_table()
        else:
            update_dashboard()

    def get_selected_task():
        selected = task_list.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a task first!")
            return None, None
        task_id = int(selected[0])
        for index, task in enumerate(tasks):
            if task["id"] == task_id:
                return index, task
        return None, None

    # ------------------ ADD TASK ------------------
    def add_task():
        if not can_manage:
            messagebox.showwarning("Permission", "Only instructors/admins can add tasks.")
            return
        name = task_name_entry.get().strip()
        subject = subject_entry.get().strip()
        section = section_entry.get().strip()
        course = course_entry.get().strip()
        year_level = year_entry.get().strip()
        instructor_name = instructor_entry.get().strip()
        term = term_var.get().strip()
        date = date_entry.get().strip()
        time = time_entry.get().strip()

        if not all([name, subject, section, course, year_level, instructor_name, term, date, time]):
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            deadline_dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %I:%M %p")
        except ValueError:
            messagebox.showerror("Error", "Time must follow hh:mm AM/PM (e.g., 02:30 PM).")
            return

        deadline = deadline_dt.strftime("%Y-%m-%d %I:%M %p")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tasks (name, subject, section, course, year_level, instructor, term, deadline, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, subject, section, course, year_level, instructor_name, term, deadline, "Pending")
            )
            task_id = cursor.lastrowid
            conn.commit()

        tasks.append({
            "id": task_id,
            "name": name,
            "subject": subject,
            "section": section,
            "course": course,
            "year_level": year_level,
            "instructor": instructor_name,
            "term": term,
            "deadline": deadline,
            "status": "Pending"
        })

        refresh_task_table()

        task_name_entry.delete(0, tk.END)
        subject_entry.delete(0, tk.END)
        section_entry.delete(0, tk.END)
        course_entry.delete(0, tk.END)
        year_entry.delete(0, tk.END)
        instructor_entry.delete(0, tk.END)
        term_var.set(TERM_OPTIONS[0])
        date_entry.delete(0, tk.END)
        time_entry.delete(0, tk.END)

    # ------------------ EDIT TASK ------------------
    def edit_task():
        if not can_manage:
            messagebox.showwarning("Permission", "Only instructors/admins can edit tasks.")
            return
        index, task = get_selected_task()
        if task is None:
            return

        edit = tk.Toplevel(window)
        edit.geometry("420x560")
        edit.configure(bg=BG)

        tk.Label(edit, text="Edit Task", font=("Segoe UI", 22), bg=BG).pack(pady=15)

        def input_field(text, default):
            tk.Label(edit, text=text, bg=BG, font=("Segoe UI", 12)).pack()
            entry = tk.Entry(edit, width=30, font=("Segoe UI", 12))
            entry.insert(0, default)
            entry.pack(pady=5)
            return entry

        name_entry = input_field("Task Name:", task["name"])
        subject_entry_modal = input_field("Subject:", task["subject"])
        section_entry_modal = input_field("Section:", task["section"])
        course_entry_modal = input_field("Course:", task["course"])
        year_entry_modal = input_field("Year Level:", task["year_level"])
        instructor_entry_modal = input_field("Instructor:", task["instructor"])

        try:
            deadline_dt = datetime.datetime.strptime(task["deadline"], "%Y-%m-%d %I:%M %p")
            date_part = deadline_dt.strftime("%Y-%m-%d")
            time_part = deadline_dt.strftime("%I:%M %p")
        except ValueError:
            parts = task["deadline"].split(" ", 1)
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else ""

        date_entry_modal = input_field("Deadline Date:", date_part)
        time_entry_modal = input_field("Deadline Time:", time_part)

        tk.Label(edit, text="Term (Prelim/Midterm):", bg=BG, font=("Segoe UI", 12)).pack()
        term_var_modal = tk.StringVar(value=task["term"] or TERM_OPTIONS[0])
        term_combo_modal = ttk.Combobox(edit, values=TERM_OPTIONS, textvariable=term_var_modal,
                                        state="readonly", width=28, font=("Segoe UI", 12))
        term_combo_modal.pack(pady=5)

        def save():
            new_name = name_entry.get().strip()
            new_subject = subject_entry_modal.get().strip()
            new_section = section_entry_modal.get().strip()
            new_course = course_entry_modal.get().strip()
            new_year = year_entry_modal.get().strip()
            new_instructor = instructor_entry_modal.get().strip()
            new_term = term_var_modal.get().strip()
            try:
                new_deadline_dt = datetime.datetime.strptime(
                    f"{date_entry_modal.get().strip()} {time_entry_modal.get().strip()}",
                    "%Y-%m-%d %I:%M %p"
                )
            except ValueError:
                messagebox.showerror("Error", "Time must follow hh:mm AM/PM (e.g., 02:30 PM).")
                return

            if not all([new_name, new_subject, new_section, new_course, new_year, new_instructor, new_term]):
                messagebox.showerror("Error", "All fields are required!")
                return

            new_deadline = new_deadline_dt.strftime("%Y-%m-%d %I:%M %p")

            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE tasks
                    SET name = ?, subject = ?, section = ?, course = ?, year_level = ?,
                        instructor = ?, term = ?, deadline = ?
                    WHERE id = ?
                    """,
                    (new_name, new_subject, new_section, new_course, new_year,
                     new_instructor, new_term, new_deadline, task["id"])
                )
                conn.commit()

            tasks[index]["name"] = new_name
            tasks[index]["subject"] = new_subject
            tasks[index]["section"] = new_section
            tasks[index]["course"] = new_course
            tasks[index]["year_level"] = new_year
            tasks[index]["instructor"] = new_instructor
            tasks[index]["term"] = new_term
            tasks[index]["deadline"] = new_deadline

            refresh_task_table()
            edit.destroy()

        tk.Button(edit, text="Save", bg=PRIMARY, fg="white",
                  width=15, font=("Segoe UI", 12), command=save).pack(pady=20)

    # ------------------ DELETE ------------------
    def delete_task():
        if not can_manage:
            messagebox.showwarning("Permission", "Only instructors/admins can delete tasks.")
            return
        index, task = get_selected_task()
        if task is None:
            return

        if not messagebox.askyesno("Confirm", f"Delete task '{task['name']}'?"):
            return

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task["id"],))
            conn.commit()

        del tasks[index]
        refresh_task_table()

    # ------------------ CSV IMPORT ------------------
    """
    def import_csv():
        file = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not file:
            return
        with open(file, "r") as f:
            r = csv.reader(f)
            next(r)
            for row in r:
                name, subject, deadline, status = row
                tasks.append({"name": name, "subject": subject,
                              "deadline": deadline, "status": status})
                task_list.insert("", "end", values=row)
        update_dashboard()
    """
    # ------------------ CSV EXPORT ------------------
    def export_csv():
        if not can_manage:
            messagebox.showwarning("Permission", "Only instructors/admins can export schedules.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return
        with open(file, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Name", "Subject", "Section", "Course", "Year", "Instructor", "Term", "Deadline", "Status"])
            for task in tasks:
                writer.writerow([
                    task["name"],
                    task["subject"],
                    task["section"],
                    task["course"],
                    task["year_level"],
                    task["instructor"],
                    task["term"],
                    task["deadline"],
                    task["status"],
                ])

    # ------------------ MARKED DONE ------------------
    def mark_done():
        index, task = get_selected_task()
        if task is None:
            return

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status = 'Completed' WHERE id = ?", (task["id"],))
            conn.commit()

        tasks[index]["status"] = "Completed"
        refresh_task_table()

    # ------------------ NOTIFICATION CHECKER ------------------
    def check_notifications():
        load_tasks_from_db(refresh_ui=False)
        now = datetime.datetime.now()

        for t in tasks:
            if t["status"] != "Pending":
                continue

            # PARSE DEADLINE WITH TIME
            try:
                deadline_dt = datetime.datetime.strptime(t["deadline"], "%Y-%m-%d %I:%M %p")
            except ValueError:
                try:
                    deadline_dt = datetime.datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
                except ValueError:
                    continue

            time_diff = (deadline_dt - now).total_seconds()

            if time_diff < 0:
                messagebox.showwarning("Overdue", f"Task '{t['name']}' is OVERDUE!")
            elif 0 <= time_diff <= 60:
                messagebox.showinfo("Due Now", f"Task '{t['name']}' is ALMOST DUE!")
            elif 0 < time_diff <= 10800:
                mins = int(time_diff // 60)
                messagebox.showinfo("Almost Due", f"'{t['name']}' is almost due!\n{mins} mins left.")

        window.after(60000, check_notifications)
    # ------------------ BUTTON ------------------
    add_btn = tk.Button(input_frame, text="Add Task", bg=PRIMARY, fg="white", width=20, font=("Segoe UI", 13), command=add_task)
    add_btn.grid(row=9, column=0, columnspan=2, pady=15)

    # ------------------ TABLE ------------------
    style = ttk.Style()
    style.configure("Treeview", rowheight=30)

    columns = ("Name", "Subject", "Section", "Course", "Year", "Instructor", "Term", "Deadline", "Status")
    task_list = ttk.Treeview(center, columns=columns,
                             show="headings", height=12)
    headings = {
        "Name": "Task/Event",
        "Subject": "Subject",
        "Section": "Section",
        "Course": "Course",
        "Year": "Year Level",
        "Instructor": "Instructor",
        "Term": "Term",
        "Deadline": "Deadline",
        "Status": "Status",
    }
    for col in columns:
        task_list.heading(col, text=headings[col])
        task_list.column(col, width=140 if col not in {"Term", "Status"} else 100, anchor="center")
    task_list.pack(pady=20)

    # ------------------ CONTROLS ------------------
    controls = tk.Frame(center, bg=BG)
    controls.pack(pady=20)

    mark_btn = tk.Button(controls, text="Mark Completed", bg=INFO, fg="white", width=17, command=mark_done)
    mark_btn.grid(row=0, column=0, padx=10)
    edit_btn = tk.Button(controls, text="Edit Task", bg=PRIMARY, fg="white", width=17, command=edit_task)
    edit_btn.grid(row=0, column=1, padx=10)
    delete_btn = tk.Button(controls, text="Delete Task", bg=DANGER, fg="white", width=17, command=delete_task)
    delete_btn.grid(row=0, column=2, padx=10)
    export_btn = tk.Button(controls, text="Export", bg=WARNING, fg="white", width=17, command=export_csv)
    export_btn.grid(row=0, column=3, padx=10)

    manage_entries = [
        task_name_entry,
        subject_entry,
        section_entry,
        course_entry,
        year_entry,
        instructor_entry,
        date_entry,
        time_entry,
    ]

    if not can_manage:
        notice = tk.Label(center,
                          text="Student mode: you may only mark assigned tasks as completed.",
                          bg=BG, fg="#444", font=("Segoe UI", 12, "italic"))
        notice.pack()
        for widget in manage_entries:
            widget.configure(state="disabled")
        term_combo.configure(state="disabled")
        add_btn.configure(state="disabled")
        edit_btn.configure(state="disabled")
        delete_btn.configure(state="disabled")
        export_btn.configure(state="disabled")
    else:
        term_combo.configure(state="readonly")

    load_tasks_from_db()
    check_notifications()

    window.mainloop()

# START PROGRAM
init_db()
load_users()

if __name__ == "__main__":
    open_login_window()
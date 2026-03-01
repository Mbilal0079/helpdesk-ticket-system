from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "helpdesk-secret-key-2026"

DB_PATH = os.path.join(os.path.dirname(__file__), "helpdesk.db")

# ──────────────────── Database Setup ────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        issue TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        priority TEXT DEFAULT 'Low',
        status TEXT DEFAULT 'Open',
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        user_id INTEGER,
        user_name TEXT,
        user_role TEXT DEFAULT 'user',
        message TEXT NOT NULL,
        created_at TEXT,
        FOREIGN KEY(ticket_id) REFERENCES tickets(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    # Create default admin if not exists
    admin = c.execute("SELECT * FROM users WHERE email = ?", ("admin@helpdesk.com",)).fetchone()
    if not admin:
        c.execute("INSERT INTO users (name, email, password, role, created_at) VALUES (?,?,?,?,?)",
                  ("Admin", "admin@helpdesk.com",
                   generate_password_hash("admin123"), "admin",
                   datetime.now().strftime("%b %d, %Y %I:%M %p")))
    conn.commit()
    conn.close()

init_db()

# ──────────────────── Auth Decorators ────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("🔒 Please login to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("⛔ Admin access required.", "warning")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated

# ──────────────────── Auth Routes ────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if len(password) < 4:
            flash("❌ Password must be at least 4 characters.", "warning")
            return redirect(url_for("register"))
        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("❌ Email already registered.", "warning")
            return redirect(url_for("register"))
        conn.execute("INSERT INTO users (name, email, password, role, created_at) VALUES (?,?,?,?,?)",
                     (name, email, generate_password_hash(password), "user",
                      datetime.now().strftime("%b %d, %Y %I:%M %p")))
        conn.commit()
        conn.close()
        flash("🎉 Account created! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["role"] = user["role"]
            flash(f"👋 Welcome back, {user['name']}!", "success")
            return redirect(url_for("home"))
        flash("❌ Invalid email or password.", "warning")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("👋 Logged out successfully.", "info")
    return redirect(url_for("home"))

# ──────────────────── Main Routes ────────────────────
@app.route("/")
def home():
    conn = get_db()
    stats = {
        "total": conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
        "open": conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'").fetchone()[0],
        "closed": conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Closed'").fetchone()[0],
        "high": conn.execute("SELECT COUNT(*) FROM tickets WHERE priority='High' AND status='Open'").fetchone()[0],
    }
    conn.close()
    return render_template("index.html", stats=stats)

@app.route("/create", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO tickets (user_id, name, email, issue, category, priority, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (session["user_id"], session["user_name"], session["user_email"],
             request.form["issue"], request.form["category"],
             request.form["priority"], "Open",
             datetime.now().strftime("%b %d, %Y %I:%M %p")))
        conn.commit()
        conn.close()
        flash("🎉 Ticket created successfully!", "success")
        return redirect(url_for("view_tickets"))
    return render_template("create_ticket.html")

@app.route("/tickets")
@login_required
def view_tickets():
    conn = get_db()
    filter_status = request.args.get("status", "all")
    filter_priority = request.args.get("priority", "all")
    filter_category = request.args.get("category", "all")
    search = request.args.get("search", "").strip()

    query = "SELECT t.*, (SELECT COUNT(*) FROM comments WHERE ticket_id=t.id) as comment_count FROM tickets t WHERE 1=1"
    params = []

    # Regular users see only their tickets; admin sees all
    if session.get("role") != "admin":
        query += " AND t.user_id = ?"
        params.append(session["user_id"])

    if filter_status != "all":
        query += " AND t.status = ?"
        params.append(filter_status)
    if filter_priority != "all":
        query += " AND t.priority = ?"
        params.append(filter_priority)
    if filter_category != "all":
        query += " AND t.category = ?"
        params.append(filter_category)
    if search:
        query += " AND (t.issue LIKE ? OR t.name LIKE ? OR t.email LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    query += " ORDER BY t.id DESC"
    tickets = conn.execute(query, params).fetchall()

    total_query = "SELECT COUNT(*) FROM tickets"
    total_params = []
    if session.get("role") != "admin":
        total_query += " WHERE user_id = ?"
        total_params.append(session["user_id"])
    total = conn.execute(total_query, total_params).fetchone()[0]

    conn.close()
    return render_template("tickets.html", tickets=tickets, total=total,
                           filter_status=filter_status, filter_priority=filter_priority,
                           filter_category=filter_category, search=search)

@app.route("/ticket/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    conn = get_db()
    ticket = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        conn.close()
        flash("❌ Ticket not found.", "warning")
        return redirect(url_for("view_tickets"))
    # Only owner or admin can view
    if session.get("role") != "admin" and ticket["user_id"] != session["user_id"]:
        conn.close()
        flash("⛔ Access denied.", "warning")
        return redirect(url_for("view_tickets"))
    comments = conn.execute("SELECT * FROM comments WHERE ticket_id = ? ORDER BY id ASC", (ticket_id,)).fetchall()
    conn.close()
    return render_template("ticket_detail.html", ticket=ticket, comments=comments)

@app.route("/ticket/<int:ticket_id>/comment", methods=["POST"])
@login_required
def add_comment(ticket_id):
    message = request.form["message"].strip()
    if message:
        conn = get_db()
        conn.execute(
            "INSERT INTO comments (ticket_id, user_id, user_name, user_role, message, created_at) VALUES (?,?,?,?,?,?)",
            (ticket_id, session["user_id"], session["user_name"], session.get("role", "user"),
             message, datetime.now().strftime("%b %d, %Y %I:%M %p")))
        conn.commit()
        conn.close()
        flash("💬 Comment added.", "success")
    return redirect(url_for("ticket_detail", ticket_id=ticket_id))

@app.route("/close/<int:ticket_id>")
@login_required
def close_ticket(ticket_id):
    conn = get_db()
    conn.execute("UPDATE tickets SET status='Closed' WHERE id=?", (ticket_id,))
    conn.commit()
    conn.close()
    flash(f"✅ Ticket #{ticket_id} closed.", "info")
    return redirect(request.referrer or url_for("view_tickets"))

@app.route("/reopen/<int:ticket_id>")
@login_required
def reopen_ticket(ticket_id):
    conn = get_db()
    conn.execute("UPDATE tickets SET status='Open' WHERE id=?", (ticket_id,))
    conn.commit()
    conn.close()
    flash(f"🔓 Ticket #{ticket_id} reopened.", "info")
    return redirect(request.referrer or url_for("view_tickets"))

@app.route("/delete/<int:ticket_id>")
@login_required
def delete_ticket(ticket_id):
    conn = get_db()
    conn.execute("DELETE FROM comments WHERE ticket_id=?", (ticket_id,))
    conn.execute("DELETE FROM tickets WHERE id=?", (ticket_id,))
    conn.commit()
    conn.close()
    flash(f"🗑️ Ticket #{ticket_id} deleted.", "warning")
    return redirect(url_for("view_tickets"))

# ──────────────────── Admin Routes ────────────────────
@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()
    stats = {
        "total": conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
        "open": conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'").fetchone()[0],
        "closed": conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Closed'").fetchone()[0],
        "high": conn.execute("SELECT COUNT(*) FROM tickets WHERE priority='High' AND status='Open'").fetchone()[0],
        "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "comments": conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0],
    }
    recent_tickets = conn.execute(
        "SELECT t.*, (SELECT COUNT(*) FROM comments WHERE ticket_id=t.id) as comment_count FROM tickets t ORDER BY t.id DESC LIMIT 10"
    ).fetchall()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", stats=stats, tickets=recent_tickets, users=users)

@app.route("/admin/delete-user/<int:user_id>")
@admin_required
def delete_user(user_id):
    if user_id == session["user_id"]:
        flash("❌ Cannot delete yourself.", "warning")
        return redirect(url_for("admin_dashboard"))
    conn = get_db()
    conn.execute("DELETE FROM comments WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM tickets WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("🗑️ User deleted.", "warning")
    return redirect(url_for("admin_dashboard"))

@app.route("/api/stats")
def api_stats():
    conn = get_db()
    data = {
        "total": conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
        "open": conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Open'").fetchone()[0],
        "closed": conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Closed'").fetchone()[0],
    }
    conn.close()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)

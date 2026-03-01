from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = "helpdesk-secret-key-2026"

# Store tickets in memory
tickets = []
ticket_id_counter = 1  # Start from 1

@app.route("/")
def home():
    stats = {
        "total": len(tickets),
        "open": sum(1 for t in tickets if t["status"] == "Open"),
        "closed": sum(1 for t in tickets if t["status"] == "Closed"),
        "high": sum(1 for t in tickets if t["priority"] == "High" and t["status"] == "Open"),
    }
    return render_template("index.html", stats=stats)

@app.route("/create", methods=["GET", "POST"])
def create_ticket():
    global ticket_id_counter
    if request.method == "POST":
        ticket = {
            "id": ticket_id_counter,
            "name": request.form["name"],
            "email": request.form["email"],
            "issue": request.form["issue"],
            "priority": request.form["priority"],
            "status": "Open",
            "created_at": datetime.now().strftime("%b %d, %Y %I:%M %p")
        }
        tickets.append(ticket)
        ticket_id_counter += 1
        flash("🎉 Ticket created successfully!", "success")
        return redirect(url_for("view_tickets"))
    return render_template("create_ticket.html")

@app.route("/tickets")
def view_tickets():
    filter_status = request.args.get("status", "all")
    filter_priority = request.args.get("priority", "all")
    filtered = tickets[:]
    if filter_status != "all":
        filtered = [t for t in filtered if t["status"] == filter_status]
    if filter_priority != "all":
        filtered = [t for t in filtered if t["priority"] == filter_priority]
    return render_template("tickets.html", tickets=filtered, 
                           filter_status=filter_status, filter_priority=filter_priority,
                           total=len(tickets))

@app.route("/close/<int:ticket_id>")
def close_ticket(ticket_id):
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["status"] = "Closed"
            flash("✅ Ticket #" + str(ticket_id) + " closed.", "info")
            break
    return redirect(url_for("view_tickets"))

@app.route("/reopen/<int:ticket_id>")
def reopen_ticket(ticket_id):
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["status"] = "Open"
            flash("🔓 Ticket #" + str(ticket_id) + " reopened.", "info")
            break
    return redirect(url_for("view_tickets"))

@app.route("/delete/<int:ticket_id>")
def delete_ticket(ticket_id):
    global tickets
    tickets = [t for t in tickets if t["id"] != ticket_id]
    flash("🗑️ Ticket #" + str(ticket_id) + " deleted.", "warning")
    return redirect(url_for("view_tickets"))

@app.route("/api/stats")
def api_stats():
    return jsonify({
        "total": len(tickets),
        "open": sum(1 for t in tickets if t["status"] == "Open"),
        "closed": sum(1 for t in tickets if t["status"] == "Closed"),
    })

if __name__ == "__main__":
    app.run(debug=True)

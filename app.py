from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Store tickets in memory
tickets = []
ticket_id_counter = 1  # Start from 1

@app.route("/")
def home():
    return render_template("index.html")

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
            "status": "Open"  # Default status
        }
        tickets.append(ticket)
        ticket_id_counter += 1
        print("Ticket Stored:", ticket)
        return redirect(url_for("view_tickets"))
    return render_template("create_ticket.html")

@app.route("/tickets")
def view_tickets():
    return render_template("tickets.html", tickets=tickets)

# Optional: Close ticket
@app.route("/close/<int:ticket_id>")
def close_ticket(ticket_id):
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["status"] = "Closed"
            break
    return redirect(url_for("view_tickets"))

if __name__ == "__main__":
    app.run(debug=True)

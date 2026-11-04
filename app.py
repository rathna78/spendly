import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for

from database.db import create_user, get_db, init_db, seed_db

app = Flask(__name__)

_DEV_SECRET_KEY = "dev-only-insecure-key"
_secret_key = os.environ.get("SECRET_KEY")
if not _secret_key:
    # Debug mode = `python app.py` (which runs with debug=True) or FLASK_DEBUG=1.
    if __name__ == "__main__" or os.environ.get("FLASK_DEBUG") == "1":
        _secret_key = _DEV_SECRET_KEY
    else:
        raise RuntimeError(
            "SECRET_KEY environment variable is required outside debug mode."
        )
app.secret_key = _secret_key

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


def _validate_registration(name, email, password):
    """Return an error message for the first failing rule, or None."""
    if not name:
        return "Please enter your name."
    if len(name) > 100:
        return "Name must be 100 characters or fewer."
    local, sep, domain = email.partition("@")
    if (
        not email
        or len(email) > 254
        or not sep
        or not local
        or "@" in domain
        or "." not in domain
        or domain.startswith(".")
        or domain.endswith(".")
        or any(c.isspace() for c in email)
    ):
        return "Please enter a valid email address."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = _validate_registration(name, email, password)
    if error:
        return render_template(
            "register.html", error=error, name=name, email=email
        ), 400

    try:
        create_user(name, email, password)
    except sqlite3.IntegrityError:
        return render_template(
            "register.html",
            error="An account with this email already exists.",
            name=name,
            email=email,
        ), 409

    flash("Account created. Please sign in.")
    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)

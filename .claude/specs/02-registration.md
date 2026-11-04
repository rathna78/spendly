# Spec Document

## 1. Overview

Add working user registration to Spendly.

`POST /register` validates the submitted form, hashes the password, inserts a row into `users`, and redirects to `/login` with a success message.

This step builds on the data layer from Step 1. It does **not** add login, sessions, or logout (Step 3).

---

## 2. Depends on

- Step 1 — Database setup (`users` table, `get_db()`, `init_db()`)

---

## 3. Routes

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/register` | Unchanged — renders `register.html` |
| POST | `/register` | New — validate, create user, redirect |

- Same endpoint function: `@app.route("/register", methods=["GET", "POST"])`
- Success → `302` redirect to `/login`, with flashed message "Account created. Please sign in."
- Validation failure → re-render `register.html` with `error` and status `400`
- Duplicate email → re-render `register.html` with `error` and status `409`

---

## 4. Database Schema

No schema change. Uses the existing `users` table:

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| name | TEXT | Not null |
| email | TEXT | Unique, not null |
| password_hash | TEXT | Not null |
| created_at | TEXT | Default datetime('now') |

---

## 5. Functions to Implement (`database/db.py`)

### A. `create_user(name, email, password)`

- Hashes `password` with `werkzeug.security.generate_password_hash`
- Inserts the row with a parameterized query
- Returns the new user's `id`
- Lets `sqlite3.IntegrityError` propagate on duplicate email (the route handles it)
- Follows the existing convention: catch `sqlite3.Error`, roll back, `logger.exception`, re-raise; `conn.close()` in `finally`
- Must never log the plaintext password

### B. `get_user_by_email(email)`

- Returns the matching `sqlite3.Row`, or `None`
- Parameterized query
- Not used by registration itself; added here so Step 3 (login) can reuse it

---

## 6. Validation (server-side, in the route)

| Field | Rules |
| --- | --- |
| name | Trimmed, required, max 100 characters |
| email | Trimmed, lowercased, required, one `@`, a `.` in the domain part, max 254 characters |
| password | Required, at least 8 characters (matches the form placeholder) |

- Show the first failing rule as a single `error` string
- Duplicate email: do **not** pre-check with a SELECT (race condition). Attempt the insert and catch `sqlite3.IntegrityError`, then show "An account with this email already exists."
- Note: this message reveals that an email is registered. Accepted for now; revisit if account enumeration becomes a concern.

---

## 7. Changes to `app.py`

- Import `request`, `redirect`, `url_for`, `flash` from Flask, `sqlite3`, and `create_user` from `database.db`
- Set `app.secret_key` from the `SECRET_KEY` environment variable
    - Fall back to a fixed development key only when running in debug mode
    - Fail loudly (raise) if no key is set and debug is off
- Convert `register()` to handle both GET and POST as described in section 3
- Do not log or echo the password anywhere

---

## 8. Template Changes

### `templates/register.html`

- Re-populate `name` and `email` with `value="{{ name }}"` / `value="{{ email }}"` after an error. Never re-populate the password.
- Add `required`, `autocomplete="name"`, `autocomplete="email"`, `autocomplete="new-password"`, and `minlength="8"` on the password field (client-side hints only; the server remains authoritative)

### `templates/login.html`

- Render flashed messages (`get_flashed_messages()`) in a `.auth-success` block above the form

### `static/css/style.css`

- Add `.auth-success`, styled like `.auth-error` but using the `--accent` palette

---

## 9. Files to Change

- `app.py`
- `database/db.py`
- `templates/register.html`
- `templates/login.html`
- `static/css/style.css`

---

## 10. Files to Create

- `tests/conftest.py` — app fixture using a temporary database
- `tests/test_registration.py`

Make the database path overridable so tests do not touch `expense_tracker.db` (for example, read `DB_PATH` from an environment variable, defaulting to the current location).

---

## 11. Dependencies

- No new pip packages
- Uses Flask, `werkzeug.security`, `sqlite3`, and pytest / pytest-flask (already in `requirements.txt`)

---

## 12. Rules for Implementation

- Parameterized SQL only; never build SQL with string formatting
- No ORMs
- Passwords are stored only as Werkzeug hashes; never stored or logged in plaintext
- Keep Jinja autoescaping on; do not use `|safe` on user-supplied values
- No auto-login after registration (sessions belong to Step 3)
- Keep the existing routes and placeholder routes unchanged

---

## 13. Out of Scope (flag for follow-up)

- CSRF protection for all POST forms (for example Flask-WTF or a hand-rolled token)
- Rate limiting / abuse protection
- Email verification
- Password strength rules beyond minimum length
- A terms / privacy consent checkbox
- Auto-login after registration (revisit in Step 3)

---

## 14. Expected Behavior

- Valid submission creates one `users` row with a hashed password, redirects to `/login`, and shows the success message
- Submitting an email that already exists shows an error with status `409` and creates no row
- Invalid name, email, or password shows an error with status `400` and creates no row
- After an error, name and email are pre-filled; password is empty
- The demo user (`demo@spendly.com` / `demo123`) is unaffected

---

## 15. Tests (`tests/test_registration.py`)

- Success: 302 to `/login`, row exists, `password_hash != password`, hash verifies with `check_password_hash`
- Duplicate email (including different letter case): 409, still one row
- Invalid email: 400
- Short password: 400
- Empty or whitespace-only name: 400
- Over-long name: 400
- Error responses keep name and email values and never contain the password
- `GET /register` still returns 200

---

## 16. Definition of Done

- [ ]  `POST /register` creates a user with a hashed password
- [ ]  Success redirects to `/login` and shows the flashed message
- [ ]  Duplicate email is rejected with 409 and a clear message
- [ ]  Invalid name, email, or password is rejected with 400
- [ ]  Form values (except password) are preserved on error
- [ ]  `SECRET_KEY` is read from the environment; app refuses to start without one outside debug mode
- [ ]  All SQL is parameterized
- [ ]  Tests pass with `pytest` against a temporary database
- [ ]  App starts without errors and the demo user still exists

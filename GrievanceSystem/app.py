from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            issue_type TEXT,
            description TEXT,
            location TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(complaints)")
    columns = [col[1] for col in cur.fetchall()]
    if 'timestamp' not in columns:
        conn.execute("ALTER TABLE complaints ADD COLUMN timestamp TEXT")
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute("UPDATE complaints SET timestamp = ?", (now,))
    cur.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/complaint')
def complaint():
    return render_template('complaint_form.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    issue_type = request.form['issue_type']
    description = request.form['description']
    location = request.form['location']
    timestamp = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO complaints (name, issue_type, description, location, timestamp) VALUES (?, ?, ?, ?, ?)",
                (name, issue_type, description, location, timestamp))
    complaint_id = cur.lastrowid
    conn.commit()
    conn.close()
    return render_template('submitted.html', complaint_id=complaint_id)

@app.route('/track')
def track():
    return render_template('track.html')

@app.route('/track_result', methods=['POST'])
def track_result():
    complaint_id = request.form['complaint_id']
    name = request.form['name']
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM complaints WHERE id=? AND name=?", (complaint_id, name))
    data = cur.fetchone()
    conn.close()
    if data:
        return render_template('track_result.html', complaint=data)
    else:
        return "No complaint found."

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username=?", (username,))
        result = cur.fetchone()
        conn.close()
        if result and result[0] == password_input:
            session['admin'] = True
            return redirect('/admin')
        else:
            flash('Invalid username or password.')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM complaints ORDER BY timestamp DESC")
    data = cur.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', complaints=data)

@app.route('/update_status/<int:id>/<string:new_status>')
def update_status(id, new_status):
    if not session.get('admin'):
        return redirect('/login')
    if new_status not in ['Resolved', 'Rejected']:
        return "Invalid status", 400
    conn = sqlite3.connect('database.db')
    conn.execute("UPDATE complaints SET status=? WHERE id=?", (new_status, id))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/submitted')
def submitted():
    return render_template('submitted.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
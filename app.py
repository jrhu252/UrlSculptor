from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database setup function
def init_db():
    with sqlite3.connect('urls.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS urls (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            long_url TEXT NOT NULL,
                            short_url TEXT NOT NULL UNIQUE,
                            clicks INTEGER DEFAULT 0
                        )''')
        conn.commit()

# Utility function to generate a short code
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Function to save URL to the database
def save_url(long_url, short_url):
    with sqlite3.connect('urls.db') as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO urls (long_url, short_url, clicks) VALUES (?, ?, ?)", (long_url, short_url, 0))
        conn.commit()

# Function to check if a short URL already exists
def short_url_exists(short_url):
    with sqlite3.connect('urls.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM urls WHERE short_url = ?", (short_url,))
        return cur.fetchone() is not None

# Function to get long URL from short code and update click count
def get_long_url_and_increment_clicks(short_url):
    with sqlite3.connect('urls.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT long_url, clicks FROM urls WHERE short_url = ?", (short_url,))
        result = cur.fetchone()

        if result:
            long_url, clicks = result
            # Increment click count
            cur.execute("UPDATE urls SET clicks = ? WHERE short_url = ?", (clicks + 1, short_url))
            conn.commit()
            return long_url
        return None

# Function to get diagnostics (times used) for a specific URL
def get_url_diagnostics(short_url):
    with sqlite3.connect('urls.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT long_url, clicks FROM urls WHERE short_url = ?", (short_url,))
        return cur.fetchone()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        long_url = request.form['long_url']
        custom_short_code = request.form.get('custom_short_code')

        if custom_short_code:  # If a custom short code is provided
            short_code = custom_short_code
            if short_url_exists(short_code):
                flash('Custom short URL already exists. Please choose another.', 'danger')
                return redirect(url_for('index'))
        else:  # If no custom short code, generate one
            short_code = generate_short_code()

        # Save to database
        save_url(long_url, short_code)
        flash(f'Shortened URL : {request.url_root}{short_code}', 'success')

        return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/<short_url>')
def redirect_to_long_url(short_url):
    long_url = get_long_url_and_increment_clicks(short_url)

    if long_url:
        return redirect(long_url)
    else:
        flash('Invalid short URL', 'danger')
        return redirect(url_for('index'))

@app.route('/diagnostics/<short_url>')
def diagnostics(short_url):
    diagnostics = get_url_diagnostics(short_url)

    if diagnostics:
        long_url, clicks = diagnostics
        return render_template('diagnostics.html', long_url=long_url, short_url=short_url, clicks=clicks)
    else:
        flash('Short URL not found.', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

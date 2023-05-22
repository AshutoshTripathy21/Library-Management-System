import sqlite3
import datetime
import csv

# Connect to the database
conn = sqlite3.connect('library.db')
cur = conn.cursor()

# Create the students table if it does not exist
cur.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        roll TEXT NOT NULL,
        branch TEXT NOT NULL,
        batch INTEGER NOT NULL,
        books_issued INTEGER DEFAULT 0,
        total_books INTEGER DEFAULT 0,
        password TEXT NOT NULL UNIQUE,
        joined DATE
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        password TEXT NOT NULL UNIQUE,
        aname TEXT,
        aemail TEXT
    )
''')

cur.execute('''
    INSERT INTO admins (password, aname, aemail)
    VALUES ('admin1pass', 'Admin 1', 'admin1@example.com')
''')

cur.execute('''
    INSERT INTO admins (password, aname, aemail)
    VALUES ('admin2pass', 'Admin 2', 'admin2@example.com')
''')

# Commit the changes and close the connection
conn.commit()
cur.close()
conn.close()

def register(cur, conn, name, email, roll, branch, batch, books_issued, total_books, password):
    # Connect to the database
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()

    cur.execute('INSERT INTO students (name, email, roll, branch, batch, books_issued, total_books, password, joined) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (name, email, roll, branch, batch, books_issued, total_books, password, datetime.date.today()))
    conn.commit()

    with open('csv_files/students.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        if file.tell() == 0:  # if the file is empty, write the table header
            writer.writerow(['Name', 'Email', 'Roll', 'Branch', 'Batch', 'Books_issued', 'Total_books', 'Password', 'Joined'])
        writer.writerow([name, email, roll, branch, books_issued, total_books, batch, password, datetime.date.today()])

    cur.close()
    conn.close()

def login(cur, email, password):
    # Connect to the database
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()

    cur.execute('SELECT id FROM students WHERE email = ? AND password = ?', (email, password))
    student_id = cur.fetchone()

    cur.close()
    conn.close()

    if student_id:
        return student_id[0]
    else:
        return None


def is_admin_authorized(aemail, password):

    conn = sqlite3.connect('library.db')
    cur = conn.cursor()
    cur.execute('SELECT id FROM admins WHERE aemail = ? AND password = ?', (aemail, password))
    result = cur.fetchone()
    cur.close()
    conn.close()

    return result is not None

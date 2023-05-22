import sqlite3
import csv
import datetime

# Database connection
conn = sqlite3.connect('library.db')
cur = conn.cursor()

# Check if the books table exists, create it if not
cur.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ISBN TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        availability INTEGER DEFAULT 0
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS issues (
    student_roll INTEGER NOT NULL,
    student_email TEXT NOT NULL,
    book_ISBN INTEGER NOT NULL,
    book_title TEXT NOT NULL,
    issued_on DATE,
    returned_on DATE,
    FOREIGN KEY (student_roll) REFERENCES students(roll),
    FOREIGN KEY (book_ISBN) REFERENCES books(ISBN)
    )
''')
conn.commit()
cur.close()
conn.close()

def add_book(cur, conn, ISBN, title, author, availability):
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()

    # Insert the book details into the books table
    cur.execute('INSERT INTO books (ISBN, title, author, availability) VALUES (?, ?, ?, ?)', (ISBN, title, author, availability))
    conn.commit()
    with open('csv_files/books.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        if file.tell() == 0:  # if the file is empty, write the table header
            writer.writerow(['ISBN', 'Book Title', 'Author', 'Availability'])
        writer.writerow([ISBN, title, author, availability])
    
    cur.close()
    conn.close()


def issue_book(cur, conn, student_roll, student_email, book_ISBN, book_title):
    conn =sqlite3.connect('library.db')
    cur = conn.cursor()

    cur.execute('INSERT INTO issues (student_roll, student_email, book_ISBN, book_title, issued_on) VALUES (?, ?, ?, ?, DATE("now"))',
                        (student_roll, student_email, book_ISBN, book_title))
    cur.execute('UPDATE books SET availability = availability - 1 WHERE ISBN = ?', (book_ISBN,))
    cur.execute('UPDATE students SET books_issued = books_issued + 1 WHERE roll = ?', (student_roll,))
    cur.execute('UPDATE students SET total_books = total_books + 1 WHERE roll = ?', (student_roll,))
    conn.commit()
    with open('csv_files/issue.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        if file.tell() == 0:  # if the file is empty, write the table header
            writer.writerow(['Student Roll', 'Student email', 'Book ISBN', 'Book Title', 'Issued_on', 'Returned_on'])
        writer.writerow([student_roll, student_email, book_ISBN, book_title, datetime.date.today()])
    
    cur.close()
    conn.close()


def return_book(cur, conn, student_roll, book_ISBN, book_title):
    cur.execute('UPDATE issues SET returned_on = DATE("now") WHERE student_roll = ?', (student_roll,))
    cur.execute('UPDATE books SET availability = availability + 1 WHERE ISBN = ?', (book_ISBN,))
    cur.execute('UPDATE students SET books_issued = books_issued - 1 WHERE roll = ?', (student_roll,))
    conn.commit()
    with open('csv_files/issue.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        if file.tell() == 0:  # if the file is empty, write the table header
            writer.writerow(['Student Roll', 'Student email', 'Book ISBN', 'Book Title', 'Issued_on', 'Returned_on'])
        writer.writerow([student_roll, book_ISBN, book_title, None, datetime.date.today()])
    
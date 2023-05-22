from flask import Flask, render_template, request, redirect, flash, url_for, session
import sqlite3
import pickle
import pandas
import numpy as np

from auth import register, login, is_admin_authorized
from library import add_book, issue_book, return_book


app = Flask(__name__)
app.secret_key = 'your_secret_key'

popular_df = pickle.load(open('pickle_files/popular.pickle', 'rb'))
pt = pickle.load(open('pickle_files/pt.pickle', 'rb'))
books = pickle.load(open('pickle_files/books.pickle', 'rb'))
similarity_scores = pickle.load(open('pickle_files/similarity_scores.pickle', 'rb'))


def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/', methods=['GET'])
def index():
    if 'student_id' in session:
        # Student is logged in
        conn = sqlite3.connect('library.db')
        cur = conn.cursor()
        name = session.get('name')
        cur.close()
        conn.close()
        return render_template("index.html",
                        book_name = list(popular_df['Book-Title'].values),
                        author = list(popular_df['Book-Author'].values),
                        image = list(popular_df['Image-URL-M'].values),
                        votes = list(popular_df['num_ratings'].values),
                        rating = list(popular_df['avg_rating'].values)
                        , logged_in=True, name=name)
    
        #return render_template('index.html', logged_in=True)
    else:
        # Student is not logged in
        return render_template('index.html', logged_in=False)
    

@app.route('/register', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        roll = request.form['roll']
        branch = request.form['branch']
        batch = request.form['batch']
        books_issued = request.form['books_issued']
        total_books = request.form['total_books']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        # Call the register function from auth.py
        register(cur, conn, name, email, roll, branch, batch, books_issued, total_books, password)
        # Close the database connection
        cur.close()
        conn.close()

        # Redirect to login page or any other appropriate page
        return redirect('/login')
    else:
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        # Call the login function from auth.py
        student_id = login(cur, email, password)

        if student_id:
            # Store the student ID in the session
            session['student_id'] = student_id
            session['email'] = email
            cur.execute('SELECT name FROM students WHERE email = ?', (email,))
            name = cur.fetchone()
            session['name'] = name[0] if name else None
            # Close the database connection
            cur.close()
            conn.close()
            return redirect('/')
        
        else:
            cur.close()
            conn.close()
            # Login failed, show error message
            return render_template('login.html', error='Invalid email or password')
    else:
        return render_template('login.html')
    

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        aemail = request.form['aemail']
        password = request.form['password']

        if is_admin_authorized(aemail, password):
            # Admin is authorized, store the admin ID in the session
            session['admin_id'] = aemail
            return redirect('/admin/students')
        else:
            # Invalid credentials, show error message
            error_message = 'Invalid credentials. Please try again.'
            return render_template('admin/admin_login.html', error_message=error_message)
    else:
        return render_template('admin/admin_login.html')
    

@app.route('/admin/add_book', methods=['GET', 'POST'])
def add_book_route():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    if request.method == 'POST':
        ISBN = request.form['ISBN']
        title = request.form['title']
        author = request.form['author']
        availability = request.form['availability']


        conn = get_db_connection()
        cur = conn.cursor()

        # Call the register function from auth.py
        add_book(cur, conn, ISBN, title, author, availability)

        # Close the database connection
        cur.close()
        conn.close()

        #flash('Book added successfully!')
        return redirect('/admin/books')
    else:
        return render_template('admin/add_book.html')

@app.route('/admin/students', methods=['GET'])
def view_students():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM students')
    students = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin/students.html', students=students)


@app.route('/admin/books', methods=['GET'])
def view_books():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM books')
    books = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin/books.html', books=books)


@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book_route():
    if 'student_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        student_roll = request.form['student_roll']
        student_email = request.form['student_email']
        book_ISBN = request.form['book_ISBN']
        book_title = request.form['book_title']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT availability FROM books WHERE ISBN = ?', (book_ISBN,))
        row = cur.fetchone()
        if row is not None:
            availability = row[0]

            if availability > 0:
                issue_book(cur, conn, student_roll, student_email, book_ISBN, book_title)
                cur.close()
                conn.close()
                flash('Book issued successfully')
                return redirect('/')
            else:
                # Book not available, check which student has issued the book the most times
                cur.execute('''
                    SELECT student_roll, COUNT(*) AS num_issues
                    FROM issues
                    WHERE book_ISBN = ?
                    GROUP BY student_roll
                    ORDER BY num_issues DESC
                ''', (book_ISBN,))
                issued_students = cur.fetchall()

                if issued_students:
                    # Get the student with the highest number of book issues
                    student_id_with_most_issues = issued_students[0][0]

                    # Check if the current student is the one with the most issues
                    if student_roll == student_id_with_most_issues:
                        flash('You have already issued the book. Please wait for its return.')
                    else:
                        flash('The book is currently issued by another student with more book issues.')
                else:
                    flash('Book not available.')

                return redirect('/issue')
        else:
            flash('Book not found.')
            return redirect('/issue')
    else:
        return render_template('issue.html')


@app.route('/return_book', methods=['GET', 'POST'])
def return_book_route():
    if 'student_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        student_roll = request.form['student_roll']
        book_ISBN = request.form['book_ISBN']
        book_title = request.form['book_title']

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if the issue exists and is not returned yet
        cur.execute('SELECT book_ISBN, student_roll FROM issues WHERE student_roll = ? AND returned_on IS NULL', (student_roll,))
        issue = cur.fetchone()

        if issue:
            #student_id, book_id, title = issue

            return_book(cur, conn, student_roll, book_ISBN, book_title)
            cur.close()
            conn.close()
            flash('Book returned successfully.')
            return redirect('/')
        else:
            flash('Invalid issue ID or book already returned.')
            return redirect('/return')
    else:
        return render_template('return.html')


@app.route('/admin/issue_books', methods=['GET'])
def view_issue_books():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    # Fetch the students data from the database
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM issues')
    issues = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin/issues.html', issues=issues)


@app.route('/avail_books')
def top_books():
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM books')
    books = cur.fetchall()
    return render_template("recommend/top_books.html", books=books)


@app.route('/recommend')
def recommend_ui():
    return render_template('recommend/recommend.html')

@app.route('/recommend_books',methods=['post'])
def recommend():
    user_input = request.form.get('user_input')
    index = np.where(pt.index == user_input)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:13]

    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        data.append(item)

    #print(data)

    return render_template('recommend/recommend.html',data=data)


@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect('/login')
    
    # Fetch the student's information from the database
    conn = get_db_connection()
    cur = conn.cursor()

    # Retrieve the student's details
    student_id = session['student_id']
    if student_id:
            # Store the student ID in the session
            session['student_id'] = student_id
            cur.execute('SELECT name FROM students WHERE email = ?', (student_id,))
    #email = session['email']
            cur.execute('SELECT * FROM students WHERE email = ?', (student_id,))
            student = cur.fetchone()

    # Retrieve the books issued by the student
    cur.execute('''
        SELECT books.title
        FROM issues
        JOIN books ON issues.book_ISBN = books.ISBN
        WHERE issues.student_email = ?
    ''', (student_id,))
    issued_books = cur.fetchall()
    print(issued_books)
    print(student)
    cur.close()
    conn.close()

    return render_template('profile.html', student=student, issued_books=issued_books)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect('/admin/login')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run()
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import ast

app = Flask(__name__,static_url_path='/static')

conn = psycopg2.connect(
    host="localhost",
    database="med",
    user="postgres",
    password="01234"
)

def remove_duplicates(lst):
    unique_lst = []
    seen = set()
    for sublist in lst:
        key = tuple(sublist)
        if key not in seen:
            seen.add(key)
            unique_lst.append(sublist)
    return unique_lst

@app.route('/')
def index():
    return render_template('admin_user.html')

@app.route('/redirect', methods=['POST'])
def redirect_page():
    selected_title = request.form.get('title')

    if selected_title == 'user':
        return render_template('user.html')
    elif selected_title == 'admin':
        return render_template('admin.html')
    else:
        return redirect('/')

@app.route('/user',methods=['GET', 'POST'])
def user():
    if request.method == 'POST':
        email = request.form['email']
        password= request.form['password']
        cur=conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s",(email,password))
        row=cur.fetchall()        
        email=row[0][0]
        cur.close
        if row:
            return render_template('about.html',email=email)
        else:
            return 'Goes to employee page!'
        
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = conn.cursor()
        cur.execute("SELECT * FROM admin WHERE email=%s AND password=%s", (email, password))
        row = cur.fetchall()
        cur.close()

        if row:  
            email = row[0][0]
            return render_template('admin_home.html', email=email)
        else:
            return 'Goes to employee page!'


@app.route('/logout')
def logout():
    return render_template('admin_user.html')


def get_job_data(email):
    cur = conn.cursor()
    cur.execute('SELECT jobid FROM postings, users WHERE email=%s', (email,))
    row = cur.fetchall()
    job_data = []
    if row:
        jobids = row
        for i in jobids:
            cur.execute('SELECT jobid, jobname, salary, location, type FROM postings WHERE jobid=%s', (i))

            job = cur.fetchone()
            if job:
                job_data.append({
                    'jobid': job[0],
                    'jobname': job[1],
                    'salary': job[2],
                    'location': job[3],
                    'type': job[4]
                })
    cur.close()
    return job_data

@app.route('/postings/<email>')
def postings(email):
    job_data = get_job_data(email)
    return render_template('postings.html', email=email, data=job_data)

@app.route('/favorites/<email>')
def favorites(email):
    cur=conn.cursor()
    cur.execute('SELECT jobid FROM favorites WHERE email=%s',(email,))
    row=cur.fetchall()
    data = []
    if row:
        jobids=row
        for i in jobids:
            cur.execute('SELECT * FROM postings WHERE jobid=%s',(i))
            row1=cur.fetchall()
            data.append(row1[0])
        msg='These are jobs in your favorites:'
    else: msg='There are no jobs in your favorites.'
    return render_template('favs.html',email=email,data=remove_duplicates(data),msg=msg)

@app.route('/removefromfavorites/<email>/<jobid>', methods=['GET','POST'])
def removefromfavorites(email,jobid):
    if request.method=='POST':
        cur=conn.cursor()
        cur.execute("DELETE FROM favorites WHERE email = %s AND jobid = %s", (email, jobid))
        conn.commit()
        cur.close()
    cur = conn.cursor()
    cur.execute('SELECT jobid FROM favorites WHERE email=%s', (email,))
    row = cur.fetchall()
    data = []
    if row:
        jobids = row
        for i in jobids:
            cur.execute('SELECT * FROM postings WHERE jobid=%s', (i))
            row1 = cur.fetchall()
            data.append(row1[0])
        msg = 'These are the jobs in your favorites:'
    else:
        msg = 'There are no jobs in your favorites.'
    return render_template('favs.html', email=email, data=remove_duplicates(data), msg=msg)


@app.route('/addtofavorites/<email>/<jobid>', methods=['POST'])
def addtofavorites(email, jobid):
    if request.method == 'POST':
        cur = conn.cursor()
        cur.execute("INSERT INTO favorites (jobid, email) VALUES (%s, %s)", (jobid, email))
        conn.commit()
        cur.close()
        job_data = get_job_data(email)
        return render_template('postings.html', email=email, data=job_data)  
    
from werkzeug.utils import secure_filename
import os

@app.route('/submitapplication/<email>/<jobid>', methods=['GET','POST'])
def submitapplication(email, jobid):
    if request.method == 'POST':
        coverletter= request.form['coverletter']
        cv = request.files['cv']

    if cv:
        filename = secure_filename(cv.filename)
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        cv.save(filepath)
        cur=conn.cursor()
        cur.execute('INSERT INTO appliedjobs (email,jobid,coverletter,cv) VALUES (%s,%s,%s,%s)',(email,jobid,coverletter,filepath))
        conn.commit()

        job_data = get_job_data(email)
        return render_template('postings.html', email=email, data=job_data)

@app.route('/appliedjobs/<email>')
def appliedjobs(email):
    cur = conn.cursor()
    cur.execute('SELECT email, jobid, coverletter, cv FROM appliedjobs')
    data = cur.fetchall()
    return render_template('admin_postings.html', data=data)

@app.route('/application/<email>/<jobid>', methods=['POST'])
def application(email, jobid):
    if request.method == 'POST':
        job_data = get_job_data(email)
        return render_template('application_form.html', email=email, data=job_data, jobid=jobid)

from flask import send_file

@app.route('/download_cv/<filename>')
def download_cv(filename):
    filepath = filename
    return send_file(filepath, as_attachment=True)

@app.route('/about/<email>')
def about(email):
    return render_template('about.html', email=email)

@app.route('/contact/<email>')
def contact(email):
    return render_template('contact.html', email=email)

@app.route('/profile/<email>')
def profile(email):
    return render_template('profile.html', email=email)

@app.route('/evaluate_jobs/<email>')
def evaluate_jobs(email):
    return render_template('evaluate_jobs.html', email=email)

@app.route('/evaluate_forms/<email>')
def evaluate_forms(email):
    return render_template('evaluate_forms.html', email=email)

@app.route('/add_jobs/<email>')
def add_jobs(email):
    return render_template('posting_jobs.html', email=email)

@app.route('/admin_home/<email>')
def admin_home(email):
    return render_template('admin_home.html', email=email)

@app.route('/form/<email>')
def form(email):
    return render_template('form.html', email=email)


@app.route('/submitIntForm/<email>',methods=['GET','POST'])
def submitIntForm(email):
    if request.method=='POST':
        mail=request.form['email']
        studentID=request.form['studentID']
        cur=conn.cursor()
        email = cur.execute("SELECT email FROM users WHERE email=%s",(email,))
        cur.execute('INSERT INTO intform (email,studentID) VALUES (%s,%s)',(mail,studentID))
        conn.commit()
        return render_template('form.html',email=email)

@app.route('/approvedIntForm/<email>/<req>',methods=['POST'])
def approvedIntForm(email,req):
    if request.method=='POST':
        req = ast.literal_eval(req)
        cur = conn.cursor()
        cur.execute('UPDATE intform SET status=%s WHERE email=%s AND studentID=%s',('Approved',req[0],req[1]))
        conn.commit()
    status = "Pending"
    cur = conn.cursor()
    cur.execute('SELECT * FROM intform WHERE status=%s', (status,))
    requests = cur.fetchall()
    return render_template('evaluate_forms.html', email=email, requests=requests)

if __name__ == '__main__':
    app.run(debug=True)



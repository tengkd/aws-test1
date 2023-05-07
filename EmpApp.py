from flask import Flask, render_template, request, redirect, url_for
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route("/view_employee_Page", methods=['GET', 'POST'])
def view_employee_page():
    return render_template('ViewEmp.html')

@app.route("/add_employee_Page", methods=['GET', 'POST'])
def add_employee_page():
    return render_template('AddEmp.html')

@app.route("/edit_employee_Page", methods=['GET', 'POST'])
def edit_employee_page():
    return render_template('EditEmpInfo.html')

@app.route("/about", methods=['GET', 'POST'])
def about():
    return render_template('cc_aboutus.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    pay_scale = request.form['pay_scale']
    hire_date = request.form['hire_date']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location, pay_scale, hire_date))
        db_conn.commit()
        emp_name = first_name + " " + last_name

        # Upload image file to S3
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/view_employee", methods=['POST'])
def view_employee():
    emp_id = request.form['emp_id']
    select_sql = "SELECT * FROM employee WHERE emp_id=%s"
    cursor = db_conn.cursor()
    cursor.execute(select_sql, (emp_id,))
    result = cursor.fetchone()
    cursor.close()
    if result is not None:
        emp_info = {
            'emp_id': result[0],
            'first_name': result[1],
            'last_name': result[2],
            'pri_skill': result[3],
            'location': result[4],
            'pay_scale': result[5],
            'hire_date': result[6],
        }
        return render_template('ViewEmpOutput.html', emp_info=emp_info)
    else:
        return "Employee not found"

@app.route("/edit_employee", methods=['POST'])
def edit_employee_data():
    emp_id = request.form['emp_id']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    pay_scale = request.form['pay_scale']

    update_sql = "UPDATE employee SET pri_skill=%s, location=%s, pay_scale=%s WHERE emp_id=%s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(update_sql, (pri_skill, location, pay_scale, emp_id))
        db_conn.commit()
    except Exception as e:
        return str(e)
    finally:
        cursor.close()

    select_sql = "SELECT * FROM employee WHERE emp_id=%s"
    cursor = db_conn.cursor()
    cursor.execute(select_sql, (emp_id,))
    result = cursor.fetchone()
    cursor.close()

    if result is not None:
        emp_info = {
            'emp_id': result[0],
            'first_name': result[1],
            'last_name': result[2],
            'pri_skill': result[3],
            'location': result[4],
            'pay_scale': result[5],
            'hire_date': result[6],
        }
        return render_template('edit_success.html', emp_info=emp_info)
    else:
        return "Employee not found"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

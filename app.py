from flask import Flask, render_template, request
import tensorflow as tf
import numpy as np
import cv2
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Load the trained model
model = tf.keras.models.load_model('tb_detection_model.h5')

# Database configuration
db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'tb',
    'raise_on_warnings': True
}

def load_and_preprocess_image(image):
    img = cv2.imdecode(np.fromstring(image.read(), np.uint8), cv2.IMREAD_COLOR)
    img = cv2.resize(img, (256, 256))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img / 255.0
    return img

def save_result(name, id_number, nrc, date_of_testing, result):
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO users (name, id_number, nrc, date_of_testing, results) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (name, id_number, nrc, date_of_testing, result))
        conn.commit()
        print("user saved successfully")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_user_details(id_number):
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE id_number = %s"
        cursor.execute(query, (id_number,))
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    user_details = None
    search_id = ""
    user_not_found = False
    analysis_result = None

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file:
                img = load_and_preprocess_image(file)
                img = np.expand_dims(img, axis=0)
                prediction = model.predict(img)
                analysis_result = 'TB Detected' if prediction[0][0] > 0.5 else 'No TB'
                return render_template('template.html', analysis_result=analysis_result)
        elif 'search_id' in request.form:
            search_id = request.form.get('search_id')
            user_details = get_user_details(search_id)
            if not user_details:
                user_not_found = True
        elif 'name' in request.form:
            name = request.form['name']
            id_number = request.form['id_number']
            nrc = request.form['nrc']
            date_of_testing = request.form['date_of_testing']
            result = request.form['result']
            save_result(name, id_number, nrc, date_of_testing, result)
            return '<h1>Results Uploaded Successfully</h1>'

    return render_template('template.html', 
                           user_details=user_details,
                           search_id=search_id,
                           user_not_found=user_not_found)

if __name__ == '__main__':
    app.run(debug=True)

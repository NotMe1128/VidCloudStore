from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import hashlib
import json
import os
import lib.mainf as handler


#dont know why and how this whole thing is working :skull:
#but its working so better not to touch it 

app = Flask(__name__)
app.secret_key = '0b9d3f4d6a2e7b8c1f3e4d5a6b7c8d9f'  # Session management key (definaltey not safe to keep it in code instead of a .env file)
USER_DB = 'lib/users.json'
DATA_DB = 'lib/cloud_dat.json'
UPLOAD_FOLDER = 'uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = self.hash_password(password)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def save_user(self):
        try:
            with open(USER_DB, 'r') as file:
                users = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            users = {}

        if self.username in users:
            return False  # User already exists

        users[self.username] = self.password
        with open(USER_DB, 'w') as file:
            json.dump(users, file)
        return True

    @staticmethod
    def verify_user(username, password):
        try:
            with open(USER_DB, 'r') as file:
                users = json.load(file)
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            return users.get(username) == hashed_password
        except (FileNotFoundError, json.JSONDecodeError):
            return False

# Route to render the index.html file
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')  # Use request.form for form data
    password = request.form.get('password')
    print(username,password)
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password are required.'}), 400

    if User.verify_user(username, password):
        session['username'] = username  # Store the logged-in user in session
        return render_template('main_menu.html')
    #return jsonify({'status': 'success', 'message': 'Logged in successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_process', methods=['POST'])
def register_process():
    username = request.form['username']
    #email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirmPassword']

    if not password==confirm_password:
        return jsonify({"success": False, "message": "Passwords do not match. Try again."}), 400
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    new_user = User(username, password)
    if new_user.save_user():
        try:
            handler.add_user_to_cloud(username=username)
        except Exception as e:
            print(e)
            return jsonify({"success": False, "message": "Failed to add user to the cloud_database"}), 400
        return render_template('registration_success.html')
    else:
        return jsonify({"success": False, "message": "Username already exists."}), 400

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/download')
def download():
    files=handler.jd.fetch_user_video_list(session['username'],'lib/cloud_dat.json')
    print("this is the files format\n\n\n")
    print(files)
    return render_template('download.html',files=files)


@app.route('/view_files')
def view_files_page():
    files=handler.jd.fetch_user_video_list(session['username'],'lib/cloud_dat.json')
    print("this is the files format\n\n\n")
    print(files)
    return render_template('view_files.html',files=files)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/upload-file', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('home'))

    uploaded_file = request.files.get('zip_file')

    if uploaded_file and uploaded_file.filename.endswith('.zip'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)
        print('uploading')
        try:
            handler.upload_logic(file_path, session['username'])
            return render_template("uploaded.html")
        except Exception as e:
            print(e)
            return render_template('main_menu.html')
    else:
        return jsonify({'status': 'error', 'message': 'Invalid file type. Please upload a ZIP file'}), 400
# Protect the /main-menu route and others for authenticated users only
@app.route('/main-menu')
def main_menu():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('main_menu.html')

@app.route('/uploading')
def uploading_page():
    return render_template('uploading.html')

@app.route('/upload_success')
def upload_success():
    return render_template('uploaded.html')

if __name__ == '__main__':
    app.run(debug=True)

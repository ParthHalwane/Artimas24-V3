import datetime
import os
from flask import Flask, jsonify, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from github import Github
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from flask_mail import Mail, Message
from bson import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

app.config['MONGO_URI'] = 'mongodb://parthhalwane:artimas2024pccoe@ac-yjnwgro-shard-00-00.ewdp2pv.mongodb.net:27017,ac-yjnwgro-shard-00-01.ewdp2pv.mongodb.net:27017,ac-yjnwgro-shard-00-02.ewdp2pv.mongodb.net:27017/?replicaSet=atlas-1276tn-shard-0&ssl=true&authSource=admin'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'kolekarp04082003@gmail.com'
app.config['MAIL_PASSWORD'] = 'xuux kbue owpp gfxv'
app.config['MAIL_DEFAULT_SENDER'] = 'kolekarp04082003@gmail.com'

client = MongoClient(app.config['MONGO_URI'])
db = client.artimas
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, name, email, password, verified, events=[]):
        self.id = user_id
        self.name = name
        self.email = email
        self.password = password
        self.verified = verified
        self.events = events

def get_user_by_email(email):
    return db.users.find_one({'email': email})

def get_user_by_id(user_id):
    return db.users.find_one({'_id': ObjectId(user_id)})

def register_user(name, email, password, verification_token):
    hashed_password = generate_password_hash(password)
    new_user = {
        'name': name,
        'email': email,
        'password': hashed_password,
        'verified': False,
        'verification_token': verification_token,
        'events': []
    }
    user_id = db.users.insert_one(new_user).inserted_id

    verification_link = f'https://localhost:5000/verify/{verification_token}'
    subject = 'Email Verification for Registration'
    body = render_template('email_verification.html', user=new_user, verification_link=verification_link)
    send_email(subject, new_user['email'],body)

    return str(user_id)

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(user_id)
    if user_data:
        if user_data['verified'] == True:
            return User(str(user_data['_id']), user_data['name'], user_data['email'], user_data['password'], user_data['verified'], user_data['events'])
    return None

@app.route('/')
def index():
    return render_template('index.html',messages='')

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    message_type = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user_data = get_user_by_email(email)

        if user_data and check_password_hash(user_data['password'], password):
            user = User(str(user_data['_id']), user_data['name'], user_data['email'], user_data['password'], user_data['verified'])
            if user_data['verified'] == True:
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                message_type = 'warning'
                return render_template('login.html', message = 'Please ensure you have verified your email through the verification link sent on the email.',message_type = message_type)

        elif user_data:
            message_type = 'kindofwarning'
            return render_template('login.html', message = 'Please enter the correct password',message_type = message_type)

        else:
            message_type = 'error'
            return render_template('login.html', message = 'Please ensure to sign up before you Sign in',message_type=message_type)

    return render_template('login.html', messages=message,message_type=message_type)

@app.route('/register', methods=['POST','GET'])
def register():
    message = None
    message_type = None
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = get_user_by_email(email)
        if existing_user:
            if existing_user['verified']==True:
                message_type = 'error'
                message = 'Email already registered. Please use a different email.'
                message_type=message_type
            else:
                message_type = 'warning'
                message = 'You have already registered, please click the verification link sent on the email.'
                message_type=message_type   
        else:
            verification_token = generate_verification_token()
            user_id = register_user(name, email, password, verification_token)
            user = User(user_id, name, email, password, False)
            message_type = 'success'
            message = 'Registration successful. Please check your email for verification instructions.'
            message_type=message_type

    return render_template('register.html', message=message,message_type=message_type)

@app.route('/verify/<token>')
def verify_email(token):
    user = db.users.find_one({'verification_token': token})

    if user:
        db.users.update_one({'_id': user['_id']}, {'$set': {'verified': True}})
        flash('Email verification successful. You can now log in.', 'success')
    else:
        flash('Invalid verification token. Please try again or contact support.', 'error')

    return redirect(url_for('index'))

@app.route('/dashboard')
# @login_required
def dashboard():
    # print(current_user.events)
    return render_template('dashboard.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def send_email(subject, to_email, body):
    msg = Message(subject, recipients=[to_email])

    # Attach the HTML body to the email
    msg.html = body

    # Send the email
    mail.send(msg)

def generate_verification_token():
    return str(ObjectId())

@app.route('/houdiniheist')
def houdini_heist():
    return render_template('register_houdiniheist.html')

@app.route('/neurodrain')
def neurodrain():
    return render_template('register_neurodrain.html')

@app.route('/submitForm/neurodrain', methods=['POST'])
def submit_neurodrain():
    event = 'neurodrain'
    event_collection = db[event]
    msg = None

    try:
        # form_data = request.form  # Use request.form to get form data
        form_data = request.form.to_dict(flat=True)  # Convert to a flat dictionary
        is_pccoe = True

        if 'paymentScreenshot' in request.files:
            payment_screenshot = request.files['paymentScreenshot']
            if payment_screenshot.filename != '':
                # Generate a unique filename (e.g., using timestamp)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"payment_screenshot_{timestamp}.png"

                # Read the file content as bytes
                file_content = payment_screenshot.read()

                # Use PyGithub to upload the file content to the repository
                g = Github('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')
                repo = g.get_repo('Prathmesh-Kolekar/Artimas24')

                # Specify the file path and commit message
                file_path = f'data/{filename}'
                commit_message = 'Upload payment screenshot'

                response = repo.create_file(file_path, commit_message, file_content, branch='main')
                is_pccoe=False

        current_date = datetime.datetime.today()


        # Create a single document with a dictionary structure
        # Process event registration form data
        event_data = {
            'date': current_date,
            'name': request.form.get('Name'),
            'college': request.form.get('College'),
            'department': request.form.get('Department'),
            'year': request.form.get('Year'),
            'gender': request.form.get('Gender'),
            'email': request.form.get('Email'),
            'contact': request.form.get('Contact'),
            'rules_accepted': 'Rules' in request.form,  # Check if 'Rules' checkbox is checked
            # 'user_id': current_user.id,  # Add the user ID for reference
            'is_pccoe': is_pccoe
        }


        # Insert the event data into the respective collection 
        # event_collection.insert_one(event_data)

        # Update the events array for the current user
        db.users.update_one({'email': request.form.get('Email') }, {'$push': {'events': event}})

        # subject = 'Event Registration Confirmation'
        # template = render_template('registeration_confirmation.html',user_name = request.form.get('Name'),event=event)  # Adjust the path to your HTML template
        # send_email(subject,request.form.get('Email'), template )

        db[event].insert_one(event_data)

        return jsonify({'success': True, 'message': 'Form data stored successfully.'}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error storing form data.'}), 500





@app.route('/verifyEmail/<event>', methods=['GET'])
def verify_person(event):
    email_to_verify = request.args.get('email')
    # event_collection = db[event]

    user = db.users.find_one({'email': email_to_verify , 'verified' : True})

    if user:
        # print(user)
        if event in user['events']:
            return jsonify({'exists': True, 'error': 'Member already registered for the event.'})
        else:
            return jsonify({'exists': False, 'error': None})
    else:
        return jsonify({'exists': True, 'error': 'Member does not have an account yet'})
    

@app.route('/submitForm/houdiniheist', methods=['POST'])
def submit_houdiniheist():
    event = 'houdiniheist'
    try:
        # form_data = request.form  # Use request.form to get form data
        form_data = request.form.to_dict(flat=True)  # Convert to a flat dictionary
        is_pccoe = True

        # print(form_data)
        # Check if 'paymentScreenshot' is in request.files
        if 'paymentScreenshot' in request.files:
            payment_screenshot = request.files['paymentScreenshot']
            if payment_screenshot.filename != '':
                # Generate a unique filename (e.g., using timestamp)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"payment_screenshot_{timestamp}.png"

                # Read the file content as bytes
                file_content = payment_screenshot.read()

                # Use PyGithub to upload the file content to the repository
                g = Github('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')
                repo = g.get_repo('Prathmesh-Kolekar/Artimas24')

                # Specify the file path and commit message
                file_path = f'data/{filename}'
                commit_message = 'Upload payment screenshot'

                # Print or log file content
                # print(f"File Content: {file_content}")

                # Print or log file path
                # print(f"File Path: {file_path}")

                # Create the file in the repository
                response = repo.create_file(file_path, commit_message, file_content, branch='main')
                is_pccoe=False

                # Print or log GitHub API response
                # print(f"GitHub API Response: {response}")

        # Get the current date and time
        current_date = datetime.datetime.today()

        # Extract member data
        members = []
        # print(list(form_data))
        for i in range(1, 5):  # Update range to 4 to include member 3
            member_email = form_data.get(f'email{i}', {})
            # print(member_data)
            
            if member_email != 'aimsa.pccoepune.org':
                db.users.update_one({'email':member_email},{'$push':{'events':event}})
                # print()
                member_entry = {
                'name': '',
                'email': '',
                'college': '',
                'rollNo': '',
                }
            else:
                member_entry = {
                    'name': form_data.get(f'name{i}', ''),
                    'email': form_data.get(f'email{i}', ''),
                    'college': form_data.get(f'college{i}', ''),
                    'rollNo': form_data.get(f'rollNo{i}', ''),
                }
            members.append(member_entry)

        # Create a single document with a dictionary structure
        form_entry = {
            'date': current_date,
            'members': members,
            'is_pccoe':is_pccoe
        }

        # print(form_entry)

        db[event].insert_one(form_entry)

        return jsonify({'success': True, 'message': 'Form data stored successfully.'}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error storing form data.'}), 500

    

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/temp_dash')
@login_required
def temp_dash():
    return render_template('temp_dash.html', user=current_user)

@app.route('/temp_team')
# @login_required
def temp_team():
    return render_template('team_registeration.html', user=current_user)

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from flask_mail import Mail, Message
from bson import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
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

    verification_link = f'http://localhost:5000/verify/{verification_token}'
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
    return render_template('login.html',messages='')

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
@login_required
def dashboard():
    print(current_user.events)
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
    return render_template('houdiniheist.html')

msg=None
@app.route('/register_event/<event>', methods=['GET', 'POST'])
@login_required
def register_event(event):
    # Get the event collection
    event_collection = db[event]
    msg = None

    if request.method == 'POST':
        # Process event registration form data
        event_data = {
            'name': request.form.get('Name'),
            'college': request.form.get('College'),
            'department': request.form.get('Department'),
            'year': request.form.get('Year'),
            'gender': request.form.get('Gender'),
            'email': request.form.get('Email'),
            'contact': request.form.get('Contact'),
            'rules_accepted': 'Rules' in request.form,  # Check if 'Rules' checkbox is checked
            'user_id': current_user.id  # Add the user ID for reference
        }

        # Insert the event data into the respective collection 
        event_collection.insert_one(event_data)

        # Update the events array for the current user
        current_user.events.append(event)
        db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'events': current_user.events}})

        subject = 'Event Registration Confirmation'
        template = render_template('registeration_confirmation.html',user_name = request.form.get('Name'),event=event)  # Adjust the path to your HTML template
        send_email(subject,request.form.get('Email'), template )
        msg = 'Registeration Succesful'
    return render_template(f'register_{event}.html',messages=msg)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/temp_dash')
@login_required
def temp_dash():
    return render_template('temp_dash.html', user=current_user)

if __name__ == '__main__':
    app.run(debug=True)

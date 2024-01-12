from flask import Flask, render_template, request, flash
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False  # Use either TLS or SSL, not both
app.config['MAIL_USERNAME'] = 'kolekarp04082003@gmail.com'
app.config['MAIL_PASSWORD'] = 'xuux kbue owpp gfxv'  # Generate an App Password for your Gmail account
app.config['MAIL_DEFAULT_SENDER'] = 'kolekarp04082003@gmail.com'

mail = Mail(app)

@app.route('/', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        age = request.form['age']

        send_registration_email(email, name, age)

        flash('Registration email sent successfully!', 'success')

    return render_template('index.html')

def send_registration_email(email, name, age):
    subject = 'Registration Confirmation'
    body = f'Thank you for registering, {name}! Your registration details:\n\nEmail: {email}\nName: {name}\nAge: {age}'

    message = Message(subject, recipients=[email], body=body)
    mail.send(message)

if __name__ == '__main__':
    app.run(debug=True)

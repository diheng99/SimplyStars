from flask import Blueprint, jsonify, render_template, redirect, url_for, session, flash
from SimplyStars.forms import RegisterForm, forgetPasswordForm, changePasswordForm, OTPForm
from SimplyStars.models import User, db
from SimplyStars.NetworkController import generate_otp, send_email

accounts = Blueprint('AccountController', __name__)
login_attempts = {}

class UserFactory:
    @staticmethod
    def create_user(form_data):

        new_user = User(
            username=form_data['username'],
            email_address=form_data['email_address'],
            password=form_data['password']  
        )
        return new_user

@accounts.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm() # Forms are created and passed into html for rendering
    
    if form.validate_on_submit(): # Listens for POST submitted by forms.
        
        otp = generate_otp()
        
        session['temp_user_data'] = {
            'username': form.username.data,
            'email_address': form.email_address.data,
            'password': form.password.data,
            'otp': otp
        }
        
        send_email(form.email_address.data, otp)
        return redirect(url_for('AccountController.otp_verification'))
    
    return render_template('register.html', form=form)

@accounts.route('/otp_verification', methods=['GET', 'POST'])
def otp_verification():
    form = OTPForm()

    if form.validate_on_submit():
        user_otp = form.otp.data

        # Check if the OTP matches
        if 'temp_user_data' in session and session['temp_user_data'].get('otp') == user_otp:
            # OTP is correct, proceed with user registration or next steps
            # You may want to remove the OTP from the session after successful verification
            session_temp_data = session.pop('temp_user_data')
            
            new_user = UserFactory.create_user(session_temp_data)

            db.session.add(new_user)
            db.session.commit()
            
            return redirect(url_for('login_page'))
        
        else:
            # OTP is incorrect, show an error message
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('otp_verification.html', form=form)

@accounts.route('/forgetPassword', methods=['GET','POST'])
def forgetPassword_page():
    form = forgetPasswordForm()
    
    if form.validate_on_submit():
        otp = generate_otp()
        send_email(form.email_address.data, otp)
        
        session['user_data'] = {
            'email_address': form.email_address.data,
            'otp': otp
        }
        
        return redirect(url_for('AccountController.otp_reset_verify'))
    
    return render_template('forgetPassword.html', form=form)

@accounts.route('/change_password', methods=['GET','POST'])
def change_password():
    form = changePasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email_address=session['user_data']['email_address']).first()
        
        user.password = form.password.data
        db.session.commit()
        session.pop('user_data', None)
        login_attempts[user] = 0
        return redirect(url_for('login_page'))
    
    return render_template('changePassword.html', form=form)

@accounts.route('/otp_reset_verify', methods=['GET', 'POST'])
def otp_reset_verify():
    form = OTPForm()

    if form.validate_on_submit():
        user_otp = form.otp.data

        # Check if the OTP matches
        if 'user_data' in session and session['user_data'].get('otp') == user_otp:
            # OTP is correct, proceed with user registration or next steps
            # You may want to remove the OTP from the session after successful verification
            del session['user_data']['otp']
                
            return jsonify({'success': True, 'redirect_url': url_for('AccountController.change_password')})
        else:
            # OTP is incorrect, return an error in JSON format
            return jsonify({'success': False, 'error': 'Invalid OTP. Please try again.'}), 400

    # For a GET request or if form validation fails
    return render_template('otp_reset_verify.html', form=form)

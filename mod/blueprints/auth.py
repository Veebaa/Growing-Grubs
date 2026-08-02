"""
Authentication routes for Growing Grubs application.

This module contains routes for user registration, login, logout, and profile management.
"""

from typing import Optional, Tuple, Dict, Any
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from mod import db
from mod.models import Users
from mod.user_manager import RegistrationForm, LoginForm
from mod.logging_config import get_logger
from mod.config import AVAILABLE_PROFILE_IMAGES, SUCCESS_MESSAGES, ERROR_MESSAGES
from mod.validators import Validator
from mod.services import UserService

logger = get_logger(__name__)

# Create auth blueprint
auth_bp = Blueprint(
    'auth',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    """
    Handle user registration.
    
    Returns:
        Registration form or redirect to login on success
    """
    # Create an instance of RegistrationForm to handle user registration
    form = RegistrationForm()

    # Check if the form was submitted and is valid
    if form.validate_on_submit():
        logger.info(f"Registering new User {form.username.data}")
        try:
            # Create a new user instance with the form data
            user = Users(
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                profile_image=form.profile_image.data
            )
            # Hash the password before storing it
            user.set_password(form.password.data)
            # Add the new user to the session
            db.session.add(user)
            # Commit the transaction to save the user to the database
            db.session.commit()

            flash(SUCCESS_MESSAGES.get('registration_success', 'You have been successfully registered.'), 'success')

            logger.info(f"User {form.username.data} registered successfully!")
            # Redirect the user to the login page after successful registration
            return redirect(url_for('auth.login'))

        except SQLAlchemyError as e:
            # Log an error if the registration fails and roll back the session
            logger.error(f"IntegrityError during registration: {e}")
            db.session.rollback()
            flash(ERROR_MESSAGES.get('database_error', 'A database error occurred. Please try again.'), 'error')
            return f"Commit failed. Error: {e}"

    # Render the registration form template if the form is not submitted or invalid
    return render_template('register_user.html', title='Register', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    
    Returns:
        Login form or redirect to profile on success
    """
    # Redirect the user to their profile page if they are already authenticated
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} is authenticated. Redirecting to profile page.')
        return redirect(url_for('auth.profile'))

    # Create an instance of LoginForm to handle user login
    form = LoginForm()

    # Check if the form was submitted and is valid
    if form.validate_on_submit():
        # Retrieve the user by username
        user = Users.query.filter_by(username=form.username.data).first()
        
        # Check if the user exists and if the password is correct
        if user and user.check_password(form.password.data):
            # Log the user in and remember their session based on the form input
            login_user(user, remember=form.remember.data)
            logger.info(f'User {user.username} logged in successfully.')

            # Redirect to the 'next' parameter
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('auth.profile'))
        else:
            # Log the error if login fails (without credentials)
            logger.warning(f"Login failed for user {form.username.data}")

            # Flash an error message if the login fails
            flash(ERROR_MESSAGES.get('invalid_credentials', 'Invalid login credentials.'), 'error')
            return redirect(url_for('auth.login'))

    # Render the login form template if the form is not submitted or invalid
    return render_template('login.html', title='Log In', form=form)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Handle user logout.
    
    Returns:
        Redirect to index page
    """
    # Log the user out
    logout_user()
    # Flash a message indicating successful logout
    flash(SUCCESS_MESSAGES.get('logout_success', 'You have been logged out.'), 'success')
    # Redirect the user to the index page
    return redirect(url_for('health.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Display and manage user profile.
    
    Returns:
        Profile template with user data
    """
    logger_local = current_app.logger
    
    if request.method == 'POST':
        # Handle form submission for profile updates
        new_first_name = request.form.get('first_name', current_user.first_name)
        new_last_name = request.form.get('last_name', current_user.last_name)
        new_email = request.form.get('email', current_user.email)
        new_profile_image = request.form.get('profile_image', current_user.profile_image)
        
        try:
            # Use service layer to update profile
            UserService.update_profile(
                user_id=current_user.id,
                first_name=new_first_name,
                last_name=new_last_name,
                email=new_email,
                profile_image=new_profile_image
            )
            flash(SUCCESS_MESSAGES.get('profile_update_success', 'Profile updated successfully!'), 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            logger_local.error(f"Error updating profile: {e}")
            flash(ERROR_MESSAGES.get('update_error', 'Error updating profile. Please try again later.'), 'error')
    
    # Render profile template
    return render_template(
        'profile.html',
        user=current_user,
        available_images=AVAILABLE_PROFILE_IMAGES
    )


@auth_bp.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    """
    Edit user profile information.
    
    Returns:
        JSON response or redirect
    """
    logger_local = current_app.logger
    
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    try:
        # Use service layer
        UserService.update_profile(
            user_id=current_user.id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            profile_image=data.get('profile_image')
        )
        
        logger_local.info(f"User {current_user.username} updated their profile")
        flash(SUCCESS_MESSAGES.get('profile_update_success', 'Profile updated successfully!'), 'success')
        
        if request.is_json:
            return {'success': True, 'message': 'Profile updated successfully'}, 200
        return redirect(url_for('auth.profile'))
        
    except ValueError as e:
        logger_local.warning(f"Validation error for user {current_user.id}: {e}")
        flash(str(e), 'error')
        if request.is_json:
            return {'success': False, 'message': str(e)}, 400
        return redirect(url_for('auth.profile'))
        
    except Exception as e:
        logger_local.error(f"Error updating profile for user {current_user.id}: {e}")
        flash(ERROR_MESSAGES.get('update_error', 'Error updating profile. Please try again later.'), 'error')
        if request.is_json:
            return {'success': False, 'message': 'Error updating profile'}, 500
        return redirect(url_for('auth.profile'))


@auth_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """
    Delete user account.
    
    Returns:
        Redirect to index page
    """
    logger_local = current_app.logger
    user_id = current_user.id
    username = current_user.username
    
    try:
        # Use service layer
        UserService.delete_account(user_id)
        
        logger_local.info(f"User {username} deleted their account")
        flash(SUCCESS_MESSAGES.get('account_deletion_success', 'Your account has been successfully deleted.'), 'success')
        return redirect(url_for('health.index'))
        
    except Exception as e:
        logger_local.error(f"Error deleting account for user {user_id}: {e}")
        flash(ERROR_MESSAGES.get('deletion_error', 'An error occurred while deleting your account. Please try again later.'), 'error')
        return redirect(url_for('auth.profile'))

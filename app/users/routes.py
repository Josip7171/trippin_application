from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required

from app import bcrypt, db
from app.models import User, Trip, Event
from app.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             ResetPasswordForm, RequestResetForm)
from app.trips.forms import PasswordCheckForm
from app.users.utils import save_picture, send_reset_email, registration_email, trip_is_full

import random, string

users = Blueprint('users', __name__)


def randomStringDigits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


@users.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        rand_password = randomStringDigits()
        hashed_password = bcrypt.generate_password_hash(rand_password).decode('utf-8')
        user = User(first_name=form.first_name.data, last_name=form.last_name.data,
                    full_name=form.full_name.data,username=form.username.data, email=form.email.data,
                    address=form.address.data, country=form.country.data, phone_number=form.phone_number.data,
                    gender=form.gender.data, birth_date=form.birth_date.data, about_me=form.about_me.data,
                    password=hashed_password)

        try:
            db.session.add(user)
            db.session.commit()
            registration_email(user, rand_password)
            flash(f'Račun stvoren! privremena lozinka je "{rand_password}".'
                  f'Za novu lozinku provjerite email pretinac', 'success')
            return redirect(url_for('users.login'))
        except:
            flash('Račun nije stvoren. Provjerite Vaš unos.', 'danger')
    return render_template('register2.html', title='Register', form=form)


@users.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login2.html', title='Login', form=form)


@users.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Uspješno ste se odjavili!", "info")
    return redirect(url_for('main.home'))


@users.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.address = form.address.data
        current_user.country = form.country.data
        current_user.phone_number = form.phone_number.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your account has been updated.', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.address.data = current_user.address
        form.country.data = current_user.country
        form.phone_number.data = current_user.phone_number
        form.about_me.data = current_user.about_me
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account3.html', form=form, image_file=image_file)


@users.route("/user/<int:id>", methods=["POST", "GET"])
def user_trips(id):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(id=id).first_or_404()
    trips = Trip.query.filter_by(user_id=id).order_by(Trip.date_created.desc()).paginate(page=page, per_page=5)
    trips2 = Trip.query.all()
    mydict = {}
    for i in range(len(trips2), 0, -1):
        users = User.query.filter(User.trips_joined.any(id=i)).all()
        mydict[i] = [x.username for x in users]
    return render_template('user_trips2.html', user=user, trips=trips, mydict=mydict, dict_length=len(mydict))


@users.route('/reset_password', methods=['POST', 'GET'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route('/reset_password/<token>', methods=['POST', 'GET'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token!', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated. You can now login.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@users.route('/add/<int:trip_id>', methods=['GET', 'POST'])
@login_required
def add_traveler(trip_id):
    selected_trip = Trip.query.get_or_404(trip_id)

    if selected_trip.is_private:
        form = PasswordCheckForm()
        if form.validate_on_submit():
            if bcrypt.check_password_hash(selected_trip.trip_password, form.trip_password.data):
                pass
            else:
                flash('Netočna lozinka.', 'danger')
                return redirect(url_for("main.home"))

        else:
            return render_template("password_check.html", form=form, title="Provjera")

    count = 0
    for user in selected_trip.users:
        count+=1
    if count == selected_trip.people_number:
        flash("Izlet popunjen. Pokušajte ponovno kasnije", "info")
        return redirect(url_for('main.home'))
    current_user.trips_joined.append(selected_trip)
    count+=1

    if selected_trip.people_number == count:                    # posalji autoru mail da mu je izlet pun
        event = Event.query.filter_by(name=selected_trip.name, event='is_full').first()
        if event:
            if event.executed == False:
                trip_is_full(selected_trip.author, selected_trip)
                event.executed = True                               # posalji tu poruku samo jednom...

    db.session.add(current_user)
    db.session.commit()
    flash(f'Prijavili ste se na putovanje "{selected_trip.name}" !', "success")
    return redirect(url_for('main.home'))


@users.route('/remove/<int:trip_id>', methods=['GET', 'POST'])
@login_required
def remove_traveler(trip_id):
    selected_trip = Trip.query.get_or_404(trip_id)
    current_user.trips_joined.remove(selected_trip)
    db.session.add(current_user)
    db.session.commit()
    flash(f'>Odjava sa "{selected_trip.name}" uspješna!', "success")
    return redirect(url_for('main.home'))



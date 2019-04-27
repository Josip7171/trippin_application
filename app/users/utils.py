from flask import url_for, current_app
import secrets, os
from PIL import Image

from app import mail
from flask_mail import Message


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def save_picture_trip(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/trip_pics', picture_fn)

    output_size = (300, 225)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def registration_email(user, rand_password):
    token = user.get_reset_token()
    msg = Message('Registracija', sender='trippinapplication@gmail.com',
                  recipients=[user.email])
    msg.body = f'''Da biste izmjenili svoju lozinku kliknite na sljedeći link
{url_for('users.reset_token', token=token, _external=True)}

Trenutna lozinka je "{rand_password}"


Ugodan ostatak dana želi Vam TrippinApp!
    '''
    mail.send(msg)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Resetiranje lozinke', sender='trippinapplication@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password visit the folowing link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request than simply ignore this email and no changes will be made.

    '''
    mail.send(msg)


def send_nortification_mail_24(user):
    msg = Message('Pocetak izleta za 24 sata!', sender='trippinapplication@gmail.com',
                  recipients=[user.email])
    msg.body = f'''Pozdrav "{ user.username }",
Obavještavamo Vas da vrijeme polaska izleta na koji ste se prijavili je za točno 24 sata.
    
Ugodan ostatak dana želi vam TrippinApp!
    '''
    mail.send(msg)


def send_nortification_mail_2(user):
    msg = Message('Izlet: Polazak za 1 sat!', sender='trippinapplication@gmail.com',
                  recipients=[user.email])
    msg.body = f'''Pozdrav "{user.username}",
Obavještavamo Vas da vrijeme polaska izleta na koji ste se prijavili je za točno 2 sata!

Dobar provod na izletu želi vam TrippinApp!
    '''
    mail.send(msg)


def trip_is_full(user):
    msg = Message('Vaš izlet je popunjen!', sender='trippinapplication@gmail.com',
                  recipients=[user.email])
    msg.body = f'''Pozdrav "{user.username}",
Obavještavamo Vas da je Vaš izlet popunjen!

Ugodan ostatak dana želi vam TrippinApp!
    '''
    mail.send(msg)


from google.appengine.ext import vendor
vendor.add('extensions')

from requests_toolbelt.adapters import appengine
appengine.monkeypatch()

import Cookie
import google.auth.transport.requests
import google.oauth2.id_token
import logging
import os
import google_sheets


HTTP_REQUEST = google.auth.transport.requests.Request()
COOKIE_NAME = os.getenv('FIREBASE_TOKEN_COOKIE', 'firebaseToken')


class User(object):

    def __init__(self, data):
        for key, value in data.iteritems():
            setattr(self, key, value)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    @property
    def domain(self):
        return self.email.split('@')[-1]


def get_user():
    cookie = Cookie.SimpleCookie(os.getenv('HTTP_COOKIE'))
    morsel = cookie.get(COOKIE_NAME)
    if not morsel:
        return
    firebase_token = morsel.value
    try:
        claims = google.oauth2.id_token.verify_firebase_token(
                        firebase_token, HTTP_REQUEST)
        return User(claims)
    except ValueError as e:
        if 'Token expired' in str(e):
            logging.info('Firebase token expired.')
            return
        raise


def can_read(sheet, user, path):
    for row in sheet:
        if user.email == row.get('email') \
                or user.domain == row.get('domain'):
            return True
    return False


class SheetsAuthMiddleware(object):

    def __init__(self, app, title=None, errors=None, admins=None,
                 sign_in_path=None, static_dirs=None):
        self.app = app
        self.errors = errors
        self.admins = admins
        self.sign_in_path = sign_in_path
        self.title = title
        self.static_dirs = None

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']

        # Static dirs are unprotected.
        if self.static_dirs:
            for static_dir in self.static_dirs:
                if static_dir.startswith(path):
                    return self.app(environ, start_response)

        user = get_user()
        sheet = google_sheets.get_or_create_sheet_from_settings(
                title=self.title, emails=self.admins)

        # Redirect to the sign in page if not signed in.
        if not user:
            status = '302 Found'
            url = self.sign_in_path
            response_headers = [('Location', url)]
            start_response(status, response_headers)
            return []

        if not can_read(sheet, user, path):
            status = '403 Forbidden'
            response_headers = []
            start_response(status, response_headers)
            return []

        return self.app(environ, start_response)

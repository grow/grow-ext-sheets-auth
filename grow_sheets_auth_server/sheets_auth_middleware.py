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
        else:
            logging.exception('Problem with Firebase token.')
    return None


def can_read(sheet, user, path):
    for row in sheet:
        if user.email == row.get('email') \
                or user.domain == row.get('domain'):
            return True
    return False


class SheetsAuthMiddleware(object):

    def __init__(self, app, title=None, errors=None, admins=None,
                 request_access_path=None, sign_in_path=None,
                 static_paths=None):
        self.app = app
        self.errors = errors
        self.admins = admins
        self.request_access_path = request_access_path
        self.sign_in_path = sign_in_path
        self.title = title
        self.redirect_to_sheet_path = '/_grow-sheets-auth'
        self.static_paths = static_paths
        self.unprotected_paths = []
        if self.static_paths:
            self.unprotected_paths += self.static_paths
        if self.request_access_path:
            self.unprotected_paths.append(self.request_access_path)
        if self.sign_in_path:
            self.unprotected_paths.append(self.sign_in_path)

    def redirect(self, url, start_response):
        status = '302 Found'
        response_headers = [('Location', url)]
        start_response(status, response_headers)
        return []

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']

        # Static dirs are unprotected.
        if self.unprotected_paths:
            for dir_path in self.unprotected_paths:
                if path.startswith(dir_path):
                    return self.app(environ, start_response)

        user = get_user()
        sheet = google_sheets.get_or_create_sheet_from_settings(
                title=self.title, emails=self.admins)

        if path == self.redirect_to_sheet_path:
            sheet_id = google_sheets.Settings.instance().sheet_id
            url = google_sheets.EDIT_URL.format(sheet_id)
            return self.redirect(url, start_response)

        # Redirect to the sign in page if not signed in.
        if not user:
            if self.sign_in_path:
                url = '{}?next={}'.format(self.sign_in_path, path)
                return self.redirect(url, start_response)
            else:
                status = '401 Unauthorized'
                response_headers = []
                start_response(status, response_headers)
                return []

        if not can_read(sheet, user, path):
            if self.request_access_path:
                url = self.request_access_path
                return self.redirect(url, start_response)
            else:
                status = '403 Forbidden'
                response_headers = []
                start_response(status, response_headers)
                return []

        return self.app(environ, start_response)

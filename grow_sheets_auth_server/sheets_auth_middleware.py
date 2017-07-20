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


def get_user():
    cookie = Cookie.SimpleCookie(os.getenv('HTTP_COOKIE'))
    morsel = cookie.get(COOKIE_NAME)
    if not morsel:
        return
    firebase_token = morsel.value
    try:
        return google.oauth2.id_token.verify_firebase_token(
                firebase_token, HTTP_REQUEST)
    except ValueError as e:
        if 'Token expired' in str(e):
            logging.info('Firebase token expired.')
            return
        raise


class SheetsAuthMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        user = get_user()
        emails = ['jeremydw@gmail.com']
        sheet = google_sheets.get_or_create_sheet_from_settings(emails=emails)
        return self.app(environ, start_response)

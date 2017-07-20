import os

if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    from google.appengine.ext import vendor
    vendor.add('extensions')
    from requests_toolbelt.adapters import appengine
    appengine.monkeypatch()

import Cookie
import google.auth.transport.requests
import google.oauth2.id_token
import logging


HTTP_REQUEST = google.auth.transport.requests.Request()


def get_user():
    cookie = Cookie.SimpleCookie(os.getenv('HTTP_COOKIE'))
    morsel = cookie.get('firebaseToken')
    if not morsel:
        return
    firebase_token = morsel.value
    return google.oauth2.id_token.verify_firebase_token(
            firebase_token, HTTP_REQUEST)


class SheetsAuthMiddleware(object):

    def __init__(self, app):
        self.app = None

    def __call__(self, environ, start_response):
        user = get_user()
        return self.app(environ, start_response)

from .. import grow_build_server
from sheets_auth_middleware import *
import logging
import os
import yaml


# Get default locales from podspec, if it exists.
podspec_path = os.path.join(os.path.dirname(__file__), '..', '..', 'podspec.yaml')
if not os.path.exists(podspec_path):
    config = {}
    static_dirs = []
else:
    podspec = yaml.load(open(podspec_path))
    config = podspec.get('meta', {}).get('server', {})
    static_dirs = []
    for static_dir in podspec.get('static_dirs', []):
        static_dirs.append(static_dir['serve_at'])


app = SheetsAuthMiddleware(
        grow_build_server.app, static_dirs=static_dirs, **config)

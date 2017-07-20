from .. import grow_build_server
from sheets_auth_middleware import *
import logging
import os
import yaml


# Get default locales from podspec, if it exists.
podspec_path = os.path.join(os.path.dirname(__file__), '..', '..', 'podspec.yaml')
podspec_path = os.path.abspath(podspec_path)
if not os.path.exists(podspec_path):
    config = {}
    static_dirs = []
else:
    podspec = yaml.load(open(podspec_path))
    config = podspec.get('meta', {}).get('server', {})
    static_paths = []
    for static_dir in podspec.get('static_dirs', []):
        static_paths.append(static_dir['serve_at'])


logging.info('Using config -> {}'.format(config))
logging.info('Using static paths -> {}'.format(', '.join(static_paths)))
app = SheetsAuthMiddleware(
        grow_build_server.app, static_paths=static_paths, **config)

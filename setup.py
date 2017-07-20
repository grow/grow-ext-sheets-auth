from setuptools import setup


setup(
    name='grow-ext-sheets-auth-server',
    version='1.0.0',
    license='MIT',
    author='Grow Authors',
    author_email='hello@grow.io',
    include_package_data=False,
    packages=[
        'grow_sheets_auth_server',
    ],
    install_requires=[
        'google-api-python-client',
        'google-auth',
        'requests',
        'requests-toolbelt',
    ],
#    dependency_links=[
#        'git+git://github.com/grow/grow-ext-build-server#egg=grow-ext-build-server',
#    ],
)

#!/usr/bin/env python

"""
  TODO: Add Copyright and license info
"""
import os
import datetime
from setuptools import setup, find_packages


def get_version():
    """
    Get a PEP440 compliant version number
    https://www.python.org/dev/peps/pep-0440/
    """
    # If building a tag, tag is the version. Tag builds are release builds.
    if "CI_COMMIT_TAG" in os.environ:
        return os.environ["CI_COMMIT_TAG"]

    # Prefix with lowercase branch name
    version = "1.0.0.dev0"  # public version identifier
    version_fmt = "{}+{}"  # after '+' comes local version identifier
    if "CI_COMMIT_REF_SLUG" in os.environ:
        version = version_fmt.format(version, os.environ["CI_COMMIT_REF_SLUG"])
        version_fmt = "{}.{}"

    # Add either commit sha, or datetime
    if "CI_COMMIT_SHA" in os.environ:
        return version_fmt.format(version, os.environ["CI_COMMIT_SHA"])
    else:
        return version_fmt.format(version, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))


setup(
    name='techlock-auth-service',
    version=get_version(),
    description='TechLock Authentication service',
    author='Michiel Vanderlee',
    author_email='jmt.vanderlee@gmail.com',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'bcrypt>=3.1.6,<4',
        'coloredlogs>=10.0,<11',
        'flask>=1.1.1,<2',
        'flask-compress>=1.4.0,<2',
        'flask-cors>=3.0.7,<4',
        'flask-jwt-extended>=3.16.0,<4',
        'flask_log_request_id>=0.10.0,<1.0.0',
        'flask_marshmallow>=0.8.0,<1',
        'flask-migrate>=2.1.1,<3',
        'flask-rest-api>=0.16.1,<1',
        'flask_sqlalchemy>=2.3.2,<3',
        'gunicorn>=19.9.0,<20',
        'prometheus_client>=0.7.0,<1.0.0',
        'psycopg2-binary>=2.8.3,<3',
        'pyotp>=2.3.0,<3',
        'python-json-logger>=0.1.10,<1',
        'pytz==2019.2',
    ],
)

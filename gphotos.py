# Imports from Python Standard Library
import datetime as dt
import logging
import os.path
from sys import path

# Third party imports
import click
import requests

from google_auth import GoogleAuth as GoogleAuthOriginal

# Get absolute path of the dir script is run from
CWD = path[0]  # pylint: disable=C0103


# override to add browser launch feature
class GoogleAuth(GoogleAuthOriginal):
    @staticmethod
    def get_token_from_user(oauth2_login_url):
        # Print auth URL and wait for user to grant access and
        # input authentication code into the console.
        print(oauth2_login_url)
        click.launch(oauth2_login_url, wait=True)
        auth_code = input("Enter auth code from the above link: ")
        return auth_code


def configure_logging():
    # Configure root logger. Level 5 = verbose to catch mostly everything.
    logger = logging.getLogger()
    logger.setLevel(level=5)

    log_folder = os.path.join(CWD, 'logs')
    if not os.path.exists(log_folder):
        os.makedirs(log_folder, exist_ok=True)

    log_filename = 'photos_{0}.log'.format(dt.datetime.now().strftime('%Y%m%d_%Hh%Mm%Ss'))
    log_filepath = os.path.join(log_folder, log_filename)
    log_handler = logging.FileHandler(log_filepath)

    log_format = logging.Formatter(
            fmt='%(asctime)s.%(msecs).03d %(name)-12s %(levelname)-8s %(message)s (%(filename)s:%(lineno)d)',
            datefmt='%Y-%m-%d %H:%M:%S')
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    # Lower requests module's log level so that OAUTH2 details aren't logged
    logging.getLogger('requests').setLevel(logging.WARNING)


@click.command()
@click.argument('filename')
def main(filename):
    # Path to config file
    config_path = os.path.join(CWD, 'config.ini')
    logging.debug('Using config file: %s', config_path)

    # Setup Google OAUTH instance for accessing Google Photos
    oauth2_scope = ('https://picasaweb.google.com/data/ '
                    'https://www.googleapis.com/auth/userinfo.email')
    oauth = GoogleAuth(config_path, oauth2_scope, service='GooglePhotos')
    oauth.google_authenticate()

    # Check if filename exists in user's Google Photos library
    logging.debug('Getting emails for: %s', oauth.google_get_email())
    request_url = 'https://picasaweb.google.com/data/feed/api/user/default?kind=photo&q={0}'.format(filename)
    authorization_header = {"Authorization": "OAuth %s" % oauth.access_token}
    resp = requests.get(request_url, headers=authorization_header)

    logging.debug(resp.text)
    if filename+'</title>' in resp.text:
        print('file exists on google photos')
    else:
        print('file probably not uploaded')

if __name__ == '__main__':
    configure_logging()
    main()

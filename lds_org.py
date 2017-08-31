import os
import logging
import pprint
import contextlib
import requests

__version__ = '0.1.1'
CONFIG_URL = "https://tech.lds.org/mobile/ldstools/config.json"
ENV_USERNAME = 'LDSORG_USERNAME'
ENV_PASSWORD = 'LDSORG_PASSWORD'

logger = logging.getLogger("lds-org")


@contextlib.contextmanager
def session(username=None, password=None):
    """A context manager.

    Example:
    ```
    with session() as lds:
        rv = lds.get(....)
    ```
    """
    lds = LDSOrg(username, password, signin=True)
    logger.debug(u"%x yielding start", id(lds.session))
    yield lds
    logger.debug(u"%x yielding stop", id(lds.session))
    lds.get(lds['signout-url'])


class LDSOrg(object):
    """Access LDS.org JSON web tools.

    Access LDS.org and the lds tools in JSON.  You can also use the session
    to access webpages and screen scrape from there.
    """

    def __init__(self, username=None, password=None, signin=False,
                 url=None):
        """Get endpoints and possibly signin.

        Args:
            username (str): LDS.org username
            password (str): LDS.org password
            signin (bool): Sign in using environment variables when not
                supplying the username and password
            url (str): override the current signin URL when it changes
        """
        self.session = requests.Session()
        self.unitNo = ''

        logger.debug(u'%x __init__', id(self.session))
        self._get_endpoints()
        if url is None:
            url = self['auth-url']
        if username or signin:
            self.signin(username, password, url)

    def __iter__(self):
        """Iterate through the endpoints."""
        return iter(self.endpoints)

    def __getitem__(self, key):
        """Simplify endpoint usage."""
        return self.endpoints[key]

    def __getattr__(self, key):
        """Reflect to session for any needs.

        Now we can use the class instance just as we would a session.
        """
        logger.debug(u'%x getattr %s', id(self.session), key)
        return getattr(self.session, key)

    def signin(self, username=None, password=None, url=None):
        """Sign in to LDS.org using a member username and password.

        To keep username and password out of code, use the following
        environment variables: LDSORG_USERNAME AND LDSORG_PASSWORD

        Args:
            username (str or None): LDS.org username or use environ
            password (str or None): LDS.org password or use environ
            url (str): Override the default endpoint url
        """
        if username is None:
            username = os.getenv(ENV_USERNAME)
        if password is None:
            password = os.getenv(ENV_PASSWORD)

        if url is None:
            url = self['auth-url']
        logger.debug(u'%x SIGNIN %s %s', id(self.session), username, url)
        rv = self.session.post(url, data={'username': username,
                                          'password': password})
        if 'etag' not in rv.headers:
            raise ValueError('Username/password failed')
        logger.debug(u'%x SIGNIN success!', id(self.session))

        # Get the persons unit number, needed for other endponts
        rv = self.get('current-user-unit')
        assert rv.status_code == 200
        logger.debug(u'%x Headers %s', id(self.session),
                     pprint.pformat(rv.headers))
        self.unitNo = rv.json()['message']

    def get(self, eurl, *args, **kwargs):
        """Get an HTTP response from endpoint or URL.

        Some endpoints need substitution to create a valid URL. Usually,
        this appears as %@ in the endpoint.  By default this method will
        replace all occurances of %@ in the endpoint with the ward number
        of the logged in user.  You can use the ward_No parameter or fix
        it yourself if this is not the correct behaviour.

        Args:
            eurl (str): an endpoint or URL
            args (tuple): substituation for '%*' in the endpoint
                ward_No: for use with an endpoint
            kwargs (dict): paramaters for :meth:`requests.Session.get`

        Returns:
            :class:`requests.Response`
        """
        try:
            url = self.endpoints[eurl]
            logger.debug(u'%x GET %s', id(self.session), eurl)
        except KeyError:
            pass
        else:
            # Fix any substitution as needed
            url = url.replace('%@', kwargs.pop('ward_No', self.unitNo))
            if '%' in url:
                if args:
                    url = url % args
                else:
                    raise ValueError("endpoint %s needs arguments" % url)
            eurl = url
        logger.debug(u'%x GET %s', id(self.session), eurl)
        rv = self.session.get(eurl, **kwargs)
        logger.debug('Request Headers %s',
                     pprint.pformat(dict(rv.request.headers)))
        try:
            length = len(rv.raw)
        except TypeError:
            length = 0
        logger.debug(u'%x response=%s length=%d',
                     id(self.session), str(rv), length)
        logger.debug('Response Headers %s', pprint.pformat(dict(rv.headers)))
        return rv

    def _get_endpoints(self):
        """Get the currently supported endpoints provided by LDS Tools.

        See https://tech.lds.org/wiki/LDS_Tools_Web_Services
        """
        # Get the endpoints
        logger.debug(u"%x Get endpoints", id(self.session))
        rv = self.session.get(CONFIG_URL)
        assert rv.status_code == 200
        self.endpoints = rv.json()
        logger.debug(u'%x Got %d endponts', id(self.session),
                     len(self.endpoints))


if __name__ == "__main__":  # pragma: no cover
    import sys
    import argparse
    import getpass

    parser = argparse.ArgumentParser()
    parser.add_argument('-e', metavar='ENDPOINT/URL',
                        help="Endpoint to pretty print")
    parser.add_argument('arg', nargs='*',
                        help='Arguments for endpoint URLs')
    parser.add_argument('--logger', help='Filename for log')
    args = parser.parse_args()

    if args.logger:
        h = logging.FileHandler(args.logger, 'wt')
        logger.addHandler(h)
        logger.setLevel(logging.DEBUG)

    username = os.getenv(ENV_USERNAME)
    password = os.getenv(ENV_PASSWORD)
    if username is None or password is None:
        logger.info("Asking for username and password.")
        asking = raw_input if sys.version_info.major < 3 else input
        username = asking('LDS.org username:')
        password = getpass.getpass('LDS.org password:')
        if username is None or password is None:
            print("Give username and password at input or set environment"
                  " %s and %s." %s (ENV_USERNAME, ENV_PASSWORD))
            sys.exit(1)

    lds = LDSOrg()

    if not args.e:
        # pprint available endoints
        pprint.pprint(sorted(str(k) for k, v in lds.endpoints.items()
                     if isinstance(v, str) and v.startswith('http')))
    else:
        lds.signin(username, password)
        rv = lds.get(args.e, *[int(_) for _ in args.arg])
        if rv.status_code != 200:
            print("Error: %d %s" % (rv.status_code, str(rv)),
                  file=sys.stderr)
        content_type = rv.headers['content-type']
        if 'html' in content_type:
            print("<!-- %s -->" % str(rv))
            print("<!-- %s -->" % rv.url)
            print(rv.text)
        elif 'json' in content_type:
            pprint.pprint(rv.json())

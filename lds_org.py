"""Get LDS.org information in JSON.

There are a series of named endpoints which map directly to a URL.
Some of these URLs expect to have a value such as the local unit
number, which are handled silently behind the scenes.

This module can be used from the command line to collect and examine
the returned data in either a pretty printed format or JSON by using
the commandline option '-j'.

Examples:
    See all the published endpoints.
    $ python -m lds_org

    See callings with peoples names
    $ python -m lds_org -e callings-with-dates

    Export username and password to the environment to prevent system
    from asking for them.
    $ export LDSORG_USERNAME = your username
    $ export LDSORG_PASSWORD = "your password"

    List of members who have moved in within the last X months.  This is
    a case where we need to provide extra information, the number of
    months.  Simply add it to the command line.
    $ python -m lds_org -e members-moved-in 2

    Get the URL to a members photo.  First you need to know the members
    ID number.  Get your current membership number
    $ python -m lds_org -e current-user-id
    $ python -m lds_org -e photo-url -m memberID individual
"""
import os
import contextlib
import logging
import pprint
import requests

__version__ = '0.2.0'
CONFIG_URL = "https://tech.lds.org/mobile/ldstools/config.json"
ENV_USERNAME = 'LDSORG_USERNAME'
ENV_PASSWORD = 'LDSORG_PASSWORD'

logger = logging.getLogger("lds-org")


class Error(Exception):
    """Exceptions for module logic."""

    pass


@contextlib.contextmanager
def session(username=None, password=None):
    """Use LDSOrg as a context manager.

    Example:
    >>> with session() as lds:
    ...     rv = lds.get(....)
    """
    lds = LDSOrg(username, password, signin=True)
    logger.debug(u"%x yielding start", id(lds.session))
    yield lds
    logger.debug(u"%x yielding stop", id(lds.session))
    lds.get('signout-url')


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
        self.unit_number = ''

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
        """Reflect to requests.Session for any needs.

        Now we can use the class instance just as we would a session.
        """
        self._debug(u'getattr %s', key)
        return getattr(self.session, key)

    def signin(self, username=None, password=None, url=None):
        """Sign in to LDS.org using a member username and password.

        While allowed, use environment variable to keep credentials out
        of code repositories.  Environment variables are:
            LDSORG_USERNAME
            LDSORG_PASSWORD

        Args:
            username (str or None): LDS.org username or use environ
            password (str or None): LDS.org password or use environ
            url (str): Override the default endpoint url

        Exceptions:
            Error

        Side effects:
            self.signed_in = True
        """
        if username is None:
            username = os.getenv(ENV_USERNAME)
        if password is None:
            password = os.getenv(ENV_PASSWORD)

        if url is None:
            url = self['auth-url']
        self._debug(u'SIGNIN %s %s', username, url)
        rv = self.session.post(url, data={'username': username,
                                          'password': password})
        if 'etag' not in rv.headers:
            raise Error('Username/password failed')
        self._debug(u'SIGNIN success!')
        self.signed_in = True

    def _get_unit(self):
        """Get unit number of currently logged in user.

        Returns: (str) unit number

        Side Effect:
            adds attribute 'unit_number' to object
        """

        self._debug(u'Silently get unit number')
        rv = self.get('current-user-unit')
        assert rv.status_code == 200
        self._debug(u'Headers %s', pprint.pformat(rv.headers))
        self.unit_number = rv.json()['message']
        self._debug(u'unit number = %s', self.unit_number)
        return self.unit_number

    def get(self, endpoint, *args, **kwargs):
        """Get an HTTP response from endpoint or URL.

        Some endpoints need substitution to create a valid URL. Usually,
        this appears as "{}" in the endpoint.  By default this method will
        replace any "{unit}" with the authorized users unit number if
        not given.

        Args:
            endpoint (str): endpoint or URL
            args (tuple): substituation for any '{}' in the endpoint
            kwargs (dict): unit, paramaters for :meth:`requests.Session.get`
                unit: unit number
                member: member number

        Returns:
            :class:`requests.Response`

        Exceptions:
            Error for unknown endpoint
            KeyError for missing endpoint keyword arguments
        """
        self._debug(u'GET %s', endpoint)
        try:
            url = self.endpoints[endpoint]
        except KeyError:
            if endpoint.startswith('http'):
                url = endpoint
            else:
                raise Error("Unknown endpoint", endpoint)

        # Get any unit or member information
        unit_member = dict()
        for key in ('member', 'unit'):
            try:
                v = kwargs.pop(key)
                if v is not None:
                    unit_member[key] = v

            except KeyError:
                pass
        if 'unit' not in unit_member and self.unit_number:
            unit_member['unit'] = self.unit_number
        # Do any substitution in the endpoint
        try:
            url = url.format(*args, **unit_member)
        except IndexError:
            self._error(u"missing positional args %s", args)
            raise Error("Missing positional arguments",
                        url, args, unit_member)
        except KeyError as err:
            if 'unit' in err.args:
                self._debug(u"'unit' needed. Get it and retry.")
                unit_member['unit'] = self._get_unit()
                kwargs.update(unit_member)
                return self.get(endpoint, *args, **kwargs)
            self._error(u"missing key words %s", (err.args))
            raise

        self._debug('GET %s', url)
        rv = self.session.get(url, **kwargs)
        self._debug('Request Headers %s',
                    pprint.pformat(dict(rv.request.headers)))
        try:
            length = len(rv.raw)
        except TypeError:
            length = 0
        self._debug(u'response=%s length=%d', str(rv), length)
        self._debug('Response Headers %s', pprint.pformat(dict(rv.headers)))
        return rv

    def _debug(self, msg, *args):
        """Wrap logging with session number."""
        return logger.debug(u'%x ' + msg, id(self.session), *args)

    def _error(self, msg, *args):
        """Wrap logging with session number."""
        return logger.error(u'%x ' + msg, id(self.session), *args)

    def _get_endpoints(self):
        """Get the currently supported endpoints provided by LDS Tools.

        See https://tech.lds.org/wiki/LDS_Tools_Web_Services
        """
        # Get the endpoints
        self._debug(u"Get endpoints")
        rv = self.session.get(CONFIG_URL)
        assert rv.status_code == 200
        self.endpoints = rv.json()
        self._debug(u'Got %d endponts', len(self.endpoints))
        ep = self.endpoints
        for k, v in ep.items():
            if not v.startswith('http'):
                continue
            # Fix unit parameter
            if 'unit/%@' in v:
                v = ep[k] = v.replace('unit/%@', 'unit/{unit}')
            elif 'unitNumber=%@' in v:
                v = ep[k] = v.replace('=%@', '={unit}')
            elif k.startswith('unit-') and v.endswith('/%@'):
                v = ep[k] = v[:-2] + '{unit}'
            # Fix member parameter
            if 'membership-record/%@' in v:
                v = ep[k] = v.replace('%@', '{member}')
            elif 'photo/url/%@' in v:
                v = ep[k] = v.replace('url/%@', 'url/{member}')
            # Fix misc
            for pattern in ('%@', '%d', '%.0f'):
                if pattern in v:
                    v = ep[k] = v.replace(pattern, '{}')


class DataAdapter(object):
    """Adapts dict JSON data provided by LDS.org.

    Allows you to access json data as attributes.

    >>> DataAdapter({'a': 123}).a
    123
    """

    def __init__(self, data):
        self._data = data

    def __getattr__(self, name):
        return self._data[name]


if __name__ == "__main__":  # pragma: no cover
    import sys
    import argparse
    import getpass
    import json

    def main():
        """Remove module execution variables from globals."""
        parser = argparse.ArgumentParser()
        parser.add_argument('-e', metavar='ENDPOINT',
                            help="Endpoint to pretty print")
        parser.add_argument('-m', metavar='MEMBER', default=None,
                            help="Member number")
        parser.add_argument('-u', metavar='UNIT', default=None,
                            help='Unit number other than authorized users')
        parser.add_argument('-j', action='store_true', help="output as JSON")
        parser.add_argument('args', nargs='*',
                            help='Arguments for endpoint URLs')
        parser.add_argument('--log', help='Filename for log, - for stdout')
        args = parser.parse_args()

        if args.log:
            if args.log == '-':
                h = logging.StreamHandler(sys.stdout)
            else:
                h = logging.FileHandler(args.log, 'wt')
            logger.addHandler(h)
            logger.setLevel(logging.DEBUG)

        username = os.getenv(ENV_USERNAME)
        password = os.getenv(ENV_PASSWORD)
        if not all((username, password)):
            logger.info("Asking for username and password.")
            asking = raw_input if sys.version_info.major < 3 else input
            username = asking('LDS.org username:')
            password = getpass.getpass('LDS.org password:')
            if not all((username, password)):
                print("Give username and password at input or set environment"
                      " %s and %s." % (ENV_USERNAME, ENV_PASSWORD))
                sys.exit(1)

        lds = LDSOrg()

        if not args.e:
            # pprint available endoints
            for k, v in sorted((_ for _ in lds.endpoints.items()
                                if _[-1].startswith('http'))):
                print("[{:25s}] {}".format(k, v))
        else:
            lds.signin(username, password)
            rv = lds.get(args.e, member=args.m, unit=args.u, *args.args)
            if rv.status_code != 200:
                print("Error: %d %s" % (rv.status_code, str(rv)))
            content_type = rv.headers['content-type']
            if 'html' in content_type:
                print("<!-- %s -->" % str(rv))
                print("<!-- %s -->" % rv.url)
                print(rv.text)
            elif 'json' in content_type:
                if not args.j:
                    pprint.pprint(rv.json())
                else:
                    print(json.dumps(rv.json(), sort_keys=True))
    main()

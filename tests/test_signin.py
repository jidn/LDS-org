import os
import datetime
import pytest
import lds_org


class TestWithoutSignin(object):

    def test_endpoints(self):
        lds = lds_org.LDSOrg()
        assert len(lds.endpoints) > 20
        assert lds['auth-url'].startswith('https://signin')
        assert len(list(iter(lds))) > 20

    def test_signin_fails(object):
        with pytest.raises(ValueError) as err:
            lds_org.LDSOrg('CainTheCursed', 'sonofadam', signin=True)
        assert 'password failed' in err.value.message

    def test_environment_vars(self):
        username = os.getenv(lds_org.ENV_USERNAME)
        password = os.getenv(lds_org.ENV_PASSWORD)
        self.has_environ = username is not None and password is not None
        assert self.has_environ


@pytest.mark.xfail(not os.getenv(lds_org.ENV_USERNAME) or
                   not os.getenv(lds_org.ENV_PASSWORD),
                   reason='Missing environment username/password')
class TestSignin(object):
    """Signin test using environment variables

    The following environment variable are required to complete tests.

    LDSORG_USERNAME
    LDSORG_PASSWORD
    """

    def test_signin_params(self):
        username = os.getenv(lds_org.ENV_USERNAME)
        password = os.getenv(lds_org.ENV_PASSWORD)
        lds = lds_org.LDSOrg()
        assert lds.unitNo == ''
        lds.signin(username, password)
        assert lds.unitNo

    def test_signin_with_environment(self):
        lds = lds_org.LDSOrg(signin=True)
        assert lds.unitNo

    def test_as_context(self):
        with lds_org.session() as lds:
            assert lds.unitNo

    def test_get_using_endpoint(self):
        with lds_org.session() as lds:
            rv = lds.get('stake-units')
            data = rv.json()
            assert len(data)
            assert 'wardName' in data[0]

    def test_get_as_url(self):
        with lds_org.session() as lds:
            key = 'X-LDS-org'
            lds.headers.update({key: 'hello'})
            rv = lds.get('http://headers.jsontest.com')
            json = rv.json()
            assert key in json

    def test_endpoint_needs_more(self):
        with lds_org.session() as lds:
            with pytest.raises(ValueError) as err:
                lds.get('cal2x-event')
            assert 'needs arguments' in err.value.message

    def test_endpoint_substitution(self):
        """Get the most recently completed calendar event.
        """
        zero = datetime.datetime.utcfromtimestamp(0)
        now = datetime.datetime.utcnow()
        past = now - datetime.timedelta(days=60)
        start = (past - zero).total_seconds() * 1000
        end = (now - zero).total_seconds() * 1000

        with lds_org.session() as lds:
            rv = lds.get('cal2x-events', start, end)
            events = rv.json()
            assert len(events)
            event = events[-1]
            rv = lds.get('cal2x-event', event['id'])
            assert rv.status_code == 200
            assert rv.json()['id'] == event['id']

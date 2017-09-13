import os
import sys
import collections
import logging
from io import StringIO
import pytest
import context  # noqa: F401
import lds_org

# lds_org.logger.addHandler(logging.FileHandler('test.log', 'wt'))
lds_org.logger.addHandler(logging.StreamHandler(sys.stdout))
lds_org.logger.setLevel(logging.DEBUG)


@pytest.mark.xfail(not os.getenv(lds_org.ENV_USERNAME) or
                   not os.getenv(lds_org.ENV_PASSWORD),
                   reason='Missing environment username/password')
class TestSignin(object):
    """Signin test using environment variables

    The following environment variable are required to complete tests.

    LDSORG_USERNAME
    LDSORG_PASSWORD
    """

    def test_environment_vars(self):
        username = os.getenv(lds_org.ENV_USERNAME)
        password = os.getenv(lds_org.ENV_PASSWORD)
        assert all((username, password))

    def test_signin_params(self):
        username = os.getenv(lds_org.ENV_USERNAME)
        password = os.getenv(lds_org.ENV_PASSWORD)
        lds = lds_org.LDSOrg()
        assert lds.unit_number == ''
        lds.signin(username, password)
        assert lds.signed_in is True
        lds._get_unit()
        assert lds.unit_number

    def test_as_context(self):
        with lds_org.session() as lds:
            assert lds.signed_in

    def test_get_using_endpoint(self):
        with lds_org.session() as lds:
            rv = lds.get('stake-units')
            data = rv.json()
            assert len(data)
            assert 'wardName' in data[0]

    def test_get_as_url(self):
        """Verify headers are loaded."""
        with lds_org.session() as lds:
            key = 'X-LDS-org'
            lds.headers.update({key: 'hello'})
            rv = lds.get('http://headers.jsontest.com')
            if 503 == rv.status_code:
                "Remote system is over quota"
                pytest.xfail("jsontest.com is over quota. Try later.")
            assert 200 == rv.status_code
            json = rv.json()
            assert key in json

    def test_endpoint_photo_url(self):
        with lds_org.session() as lds:
            rv = lds.get('current-user-detail')
            assert 200 == rv.status_code
            assert lds.unit_number == ''
            details = rv.json()

            # Needs member number
            with pytest.raises(KeyError) as err:
                lds.get('photo-url')
                assert 'member' in err.args

            # Needs positional arguments
            with pytest.raises(lds_org.Error) as err:
                lds.get('photo-url', member=details['individualId'])
                assert err.value.args[0].endswith('positional arguments')

            rv = lds.get('photo-url', 'individual', member=details['individualId'])
            assert 200 == rv.status_code
            photo = rv.json()
            assert 'individualId' in photo
            assert details['individualId'] == photo['individualId']

    def test_endpoint_needs_more(self):
        with lds_org.session() as lds:
            with pytest.raises(lds_org.Error) as err:
                lds.get('cal2x-event')
            assert err.value.args[0].endswith('positional arguments')

#    def test_calendar(self):
#        """Get the most recently completed calendar event.
#        """
#        def millisec_from_1970(dt):
#            return dt.total_seconds() * 1000
#        zero = datetime.datetime.utcfromtimestamp(0)
#        now = datetime.datetime.utcnow()
#        past = now - datetime.timedelta(days=120)
#        start = millisec_from_1970(past - zero)
#        end = millisec_from_1970(now - zero)
#        endpoint = 'cal-events'
#        with lds_org.session() as lds:
#            rv = lds.get(endpoint, 0, end)
#            assert 200 == rv.status_code
#            events = rv.json()
#            assert len(events)
#            event = events[-1]
#            rv = lds.get(endpoint[:-1], event['id'])
#            assert rv.status_code == 200
#            assert rv.json()['id'] == event['id']

    def test_logging(self):
        """Checking the logger
        """
        pseudo = StringIO()
        handler = logging.StreamHandler(pseudo)
        lds_org.logger.setLevel(logging.DEBUG)
        lds_org.logger.addHandler(handler)

        with lds_org.session() as lds:
            rv = lds.get('current-user-id')
            assert rv.status_code == 200
        log = pseudo.getvalue().split('\n')
        assert 'Get endpoints' in log[0]
        lds_org.logger.removeHandler(handler)


@pytest.mark.xfail(not os.getenv(lds_org.ENV_USERNAME) or
                   not os.getenv(lds_org.ENV_PASSWORD),
                   reason='Missing environment username/password')
class TestSnippets(object):

    def test_get_using_unit(self):
        Unit = collections.namedtuple('Unit', 'name number')
        with lds_org.session() as lds:
            rv = lds.get('stake-units')
            data = rv.json()
            assert len(data)
            units = sorted(Unit(_['wardName'], _['wardUnitNo'])
                           for _ in data)
            assert len(units)
            for unit in units:
                rv = lds.get('unit-membership', unit=unit.number)
                households = len(rv.json())
                assert households > 30

    def test_my_photo(self):
        with lds_org.session() as lds:
            rv = lds.get('current-user-id')
            my_id = rv.json()
            rv = lds.get('photo-url', 'individual', member=my_id)
            data = rv.json()
            assert 'photoType' in data
            assert data['photoType'] == 'INDIVIDUAL'
            assert 'largeUri' in data


class TestWithoutSignin(object):

    def test_signin_fails(object):
        with pytest.raises(lds_org.Error) as err:
            lds_org.LDSOrg('CainTheCursed', 'sonofadam', signin=True)
        assert str(err.value).endswith('password failed')

    def test_endpoints(self):
        """Help detect changes in endpoints.
        Get comparison text with
        $ python lds_org.py | grep http | sed -e 's/^[ \t]*//' | sort
        """
        lds = lds_org.LDSOrg()
        assert len(lds.endpoints) > 20
        assert len(list(iter(lds))) > 20
        urls = sorted(v for v in lds.endpoints.values()
                      if v.startswith('http'))
        static = sorted('''https://lds.qualtrics.com/SE/?SID=SV_esOCWpQ67JUc6na
https://play.google.com/store/apps/details?id=org.lds.ldstools
https://signin.lds.org/login.html
https://wsmobile1.lds.org/CP/CalendarProxyService/v1/Event/{}
https://wsmobile1.lds.org/CP/CalendarProxyService/v1/Events/{}-{}
https://wsmobile1.lds.org/CP/CalendarProxyService/v1/Locations?blah=adm/appVersion
https://wsmobile1.lds.org/CP/CalendarProxyService/v1/Subscribed
https://www.lds.org
https://www.lds.org/callings/melchizedek-priesthood/records-and-technology-support/lds-tools-release-notifications?lang=eng#android
https://www.lds.org/callings/melchizedek-priesthood/records-and-technology-support/lds-tools-release-notifications?lang=eng#ios
https://www.lds.org/mls/mbr/services/recommend/endowed-members?unitNumber={unit}&lang=eng
https://www.lds.org/mls/mbr/services/report/action-interview-list/full/unit/{unit}/?lang=eng
https://www.lds.org/mls/mbr/services/report/action-interview-list/unit/{unit}/?lang=eng
https://www.lds.org/mls/mbr/services/report/birthday-list/unit/{unit}/?month=1&months=12&organization=selectAll&lang=eng
https://www.lds.org/mls/mbr/services/report/membership-record/{member}?lang=eng
https://www.lds.org/mls/mbr/services/report/membership-records?unitNumber={unit}&lang=eng
https://www.lds.org/mls/mbr/services/report/members-moved-in/unit/{unit}/{}?lang=eng
https://www.lds.org/mls/mbr/services/report/members-with-callings?unitNumber={unit}&lang=eng
https://www.lds.org/mls/mbr/services/report/unit-statistics?unitNumber={unit}&lang=eng
https://www.lds.org/mobilecalendar/heartbeat
https://www.lds.org/mobilecalendar/services/lucrs/cal/allColors
https://www.lds.org/mobilecalendar/services/lucrs/cal/{}/color/{}/
https://www.lds.org/mobilecalendar/services/lucrs/cal/subscribed
https://www.lds.org/mobilecalendar/services/lucrs/evt/{}
https://www.lds.org/mobilecalendar/services/lucrs/evt/calendar/{}-{}
https://www.lds.org/mobilecalendar/services/lucrs/loc/locations
https://www.lds.org/mobilecalendar/services/lucrs/mem/currentUserOptions/{}
https://www.lds.org/mobiledirectory/heartbeat
https://www.lds.org/mobiledirectory/services/ludrs/1.1/mem/mobile/current-user-id
https://www.lds.org/mobiledirectory/services/ludrs/1.1/mem/mobile/current-user-id
https://www.lds.org/mobiledirectory/services/ludrs/1.1/mem/mobile/current-user-unitNo
https://www.lds.org/mobiledirectory/services/ludrs/1.1/mem/mobile/member-assignments
https://www.lds.org/mobiledirectory/services/ludrs/1.1/mem/mobile/member-detaillist/{unit}
https://www.lds.org/mobiledirectory/services/ludrs/1.1/mem/mobile/member-detaillist-with-callings/{unit}
https://www.lds.org/mobiledirectory/services/ludrs/1.1/photo/url/{member}/{}
https://www.lds.org/mobiledirectory/services/ludrs/1.1/unit/mobile/current-user-units
https://www.lds.org/mobiledirectory/services/ludrs/1.1/unit/unit-leadershiplist/{unit}
https://www.lds.org/mobiledirectory/services/ludrs/1.1/unit/unit-leadershiplist/{unit}
https://www.lds.org/mobiledirectory/services/ludrs/unit/current-user-stake-wards
https://www.lds.org/mobiledirectory/services/ludrs/unit/stake-leadership-positions
https://www.lds.org/mobiledirectory/services/v2/ldstools/current-user-detail
https://www.lds.org/mobiledirectory/services/v2/ldstools/member-detaillist-with-callings/{unit}
http://tech.lds.org/mobile/ldstools/leader-access-1.0.json
http://tech.lds.org/mobile/ldstools/lists.json
http://www.ldsmobile.org/lt-ios-help/?feed=rss2
http://www.lds.org/callings/melchizedek-priesthood/records-and-technology-support/lds-tools-faq?lang=eng
http://www.lds.org/callings/melchizedek-priesthood/records-and-technology-support/lds-tools-faq?lang=eng
http://www.lds.org/legal/privacy?lang=eng
http://www.lds.org/legal/terms?lang=eng
http://www.lds.org/signinout/?lang=eng&signmeout'''.splitlines())
        assert urls == static

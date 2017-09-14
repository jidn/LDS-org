import collections
from pprint import pprint
import lds_org


def stake_households():
    Unit = collections.namedtuple('Unit', 'name number')
    with lds_org.session() as lds:
        rv = lds.get('stake-units')
        data = rv.json()
        units = sorted(Unit(_['wardName'], _['wardUnitNo'])
                       for _ in data)
        for unit in units:
            rv = lds.get('unit-membership', unit=unit.number)
            print('{:4} [unit {}]{}'.format(len(rv.json()), unit.number, unit.name))


def my_photo():
    with lds_org.session() as lds:
        rv = lds.get('current-user-id')
        my_id = rv.json()
        rv = lds.get('photo-url', 'individual', member=my_id)
        pprint(rv.json())

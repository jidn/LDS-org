import context  # noqa: F401
import lds_org
import pytest


def test_adapter():
    data = {'a': 123, 'b': 1}
    adapt = lds_org.DataAdapter(data)
    assert data['a'] == adapt.a
    assert data['b'] == adapt.b
    with pytest.raises(KeyError) as err:
        adapt.c
    assert "'c'" == str(err.value)

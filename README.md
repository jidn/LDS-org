![version](http://img.shields.io/pypi/v/lds_org.svg)
![license](http://img.shields.io/pypi/l/lds_org.svg)
![Travis](https://img.shields.io/travis/jidn/LDS-org.svg)
![coverage](https://coveralls.io/repos/github/jidn/lds_org/badge.svg?branch=master)

# LDS-org

Most times, I can quickly jump the LDS.org website and get the exact
information I need.  However, there are those repeated tasks I don't
really want to to run time and time again.  Hmm... sounds like a job
for a computer.

In my current role as Clerk, reports and information are my life.  I
want to make it easier to get that information.

## Install

For install you can use pip:

```sh
pip install lds-org
```

## QuickStart

Using the command line, see the available endpoints and your current ID.

```sh
python -m lds_org
python -m lds_org -e current-user-id
```

Now lets get the same in python.

```python
import lds_org

lds = lds_org.LDSOrg()
lds.signin(username, password)
rv = lds.get('current-user-id')
print(rv.json())
```

To make conneciton a bit easier, we can create a session for repeated use.

```python
with lds_org.session() as lds:
    rv = lds.get(some_context_of_interest)
    ...
```

## Endpoints

Endpoints are URLs to resources, most of which provide JSON.
The list of endpoints are found at <https://tech.lds.org/mobile/ldstools/config.json> and are somewhat documented at <https://tech.lds.org/wiki/LDS_Tools_Web_Services>.

Some endpoints need additional data, usually the unit number which appears as `%@` in the endpoints found at [tech.lds.org](https://tech.lds.org/mobile/ldstools/config.json).
However, tech.lds.org uses it for other items as well.
I alter the URLs for better understanding by replace `%@` with `{unit}` and `{member}` as I currently understand the the endpoints.

The module will automatically replace `{unit}` with the authorized users unit number if it is not provided.  You can also provide a unit number for a different unit in a stake.

For example, get the number of household in the stake by unit.

```python
Unit = collections.namedtuple('Unit', 'name number')
with lds_org.session() as lds:
    rv = lds.get('stake-units')
    data = rv.json()
    units = sorted(Unit(_['wardName'], _['wardUnitNo'])
                   for _ in data)
    for unit in units:
        rv = lds.get('unit-membership', unit=unit.number)
        print('{:4} [unit {}]{}'.format(len(rv.json()), unit.number, unit.name))
```

You can also pass in `unit` and `member` information on the command line. See the help at

```sh
python -m lds_org -h
```

### Photos

The `photo-url` endpoint needs two arguments, an member ID and the type of photo.  The photo type is either 'household' or 'individual'.  See [LDS Tools Web Services](https://tech.lds.org/wiki/LDS_Tools_Web_Services#Signin_services) for more information.

```python
from pprint import pprint

# Get my personal picture
with lds_org.session() as lds:
    rv = lds.get('current-user-id')
    my_id = rv.json()
    rv = lds.get('photo-url', 'individual', member=my_id)
    pprint(rv.json())
```

If you know the member ID (use endpoint `current-user-id` for yourself), you can do it from the command line as well with

```sh
python -m lds_org -e current-user-id
python -m lds_org -e photo-url -m memberId individual
```

### JSON

When asking for endpoint information from the command line, the output is pretty printed.
However, you may want to take the information and use it.  You want the output in JSON.
Using the command line option of `-j` the endpoint data is given as JSON.

### Secure your username and password

You need to keep your username and password secret.  However, you also
want to automate the process of getting and processing information
from LDS.org.  You could put your username and password in your code,
but the possibility of sharing your information is very possible when
you show or share your code.

This module can use environment variables containing your username and
password.  In \*nix based systems, you can add the following to your
.bashrc or its equivelent.

```sh
export LDSORG_USERNAME=username
export LDSORG_PASSWORD="password"
```

Personally, I create a seperate file to fix the command line environment.
I take the above and put it in a file 'ldsorg-password.sh'.  From the
command line, type the following and you should see your LDS.org username.

```sh
source ldsorg-password.sh
echo $LDSORG_USERNAME
```

Once this is done, you no longer need to either enter your credentials from
the command line or specify a username/password in your code.

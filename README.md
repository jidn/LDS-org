# LDS-org

Most times, I can quickly jump on LDS.org and get the exact information
I need.  However, there are those repeated tasks I don't really want to
to run time and time again.  Hmm... sounds like a job for a computer.

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
python -m lds-org
python -m lds-org -e current-user-id
```

Now lets get the same in python.

```python
import lds_org

lds = lds_org.LDSOrg()
lds.signin(username, password)
rv = lds.get('current-user-id')
print(rv.json())
print(sorted(k for k, v in lds.endpoints.items()
      if isinstance(v, basestring) and v.startswith('http')))
```

### Working endpoints

There are some endpoints, while published, don't appear to be working. Here is a list of working endpoint providing JSON.  See <https://tech.lds.org/wiki/LDS_Tools_Web_Services> for more information.

* current-user-detail
* current-user-id
* current-user-unit
* current-user-units
* leader-access
* member-assignments
* organization-list-url
* stake-leadership
* stake-units
* unit-leadership
* unit-leadership-new
* unit-members-and-callings
* unit-members-and-callings-v2
* unit-membership
* cal2x-event
* cal2x-events

Calendar requests appear to be working but the descriptions at  <https://tech.lds.org/wiki/LDS_Tools_Web_Services> appear to be out of date.  For an example see the testing suite.


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

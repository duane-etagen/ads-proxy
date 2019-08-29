adsproxy
--------


Proof-of-concept


Setup
-----

Tunnel through SSH

Configure port forwarding using a server with a route already existing on the
PLC. That is, in ~/.ssh/config:

```
Host host_with_route_on_plc
    LocalForward 50000 plc_ip:48898
```

Edit and run test.py to intercept ADS requests made to your local machine (port
48898):

```sh
$ python test.py
```

Run an additional ADS client script to tunnel through SSH, fixing up your source
AMS ID without any client-side modifications:

```python
import os
os.environ['DYLD_LIBRARY_PATH'] = '/Users/klauer/docs/Repos/pyads/adslib'

import pyads

# plc_remote_ip = '172.21.148.145'  # <-- actual IP
plc_remote_ip = '127.0.0.1'         # <-- tunnel
plc_remote_net_id = '172.21.148.145.1.1'

plc = pyads.Connection(plc_remote_net_id, 851, plc_remote_ip)
plc.open()

print(plc.read_device_info())
```

```sh
$ python client.py
2019-08-29T13:28:53-0700 Info: Connected to 127.0.0.1
('Plc30 App', <pyads.structs.AdsVersion object at 0x10e93feb8>)
2019-08-29T13:28:53-0700 Info: connection closed by remote
```

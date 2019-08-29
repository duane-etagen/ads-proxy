import logging
import adsproxy

logging.basicConfig()
logging.getLogger('adsproxy').setLevel('DEBUG')

actual_plc_host = '172.21.148.145'

plc_host = '127.0.0.1:50000'
plc_net_id = actual_plc_host + '.1.1'
osx_net_id = '172.21.148.141.1.1'
windows_net_id = '172.21.148.142.1.1'

adsproxy.run(net_id_to_host={plc_net_id: plc_host},
             masquerade_as=windows_net_id)

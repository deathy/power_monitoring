#!/usr/bin/env python3
from pyHS100 import SmartPlug
from influxdb import InfluxDBClient
from time import sleep

client = InfluxDBClient(host='192.168.XXX.XXX', database="EnergyDB")

plug_ips = ["192.168.XXX.XXX", "192.168.XXX.XXX", "192.168.XXX.XXX"]
plug_info = {}
plug_connections = {}

for plug_ip in plug_ips:
    plug = SmartPlug(plug_ip)
    sys_info = plug.get_sysinfo()
    plug_info[plug_ip] = {
        'mac': sys_info['mac'],
        'alias': sys_info['alias']
    }
    plug_connections[plug_ip] = plug

while True:
    for ip, plugcon in plug_connections.items():
        realtime = plugcon.get_emeter_realtime()
        points = [{
            "measurement": "power",
            "tags": {
                "Device": plug_info[ip]['alias']
            },
            "fields": {
                "power": realtime['power_mw'],
                "voltage": realtime['voltage_mv'],
                "current": realtime['current_ma'],
            }
        }]
        client.write_points(points)
    sleep(1)

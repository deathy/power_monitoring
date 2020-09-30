#!/usr/bin/env python3
import sqlite3
from pyHS100 import SmartPlug
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(''),
    autoescape=select_autoescape(['html', 'xml'])
)

db_conn = sqlite3.connect('daily_power_usage.db')
db_conn.execute("""CREATE TABLE IF NOT EXISTS power_usage 
                    (
                        mac_address TEXT, 
                        device_label TEXT, 
                        measurement_date DATE, 
                        measurement_wh INTEGER,
                        PRIMARY KEY (mac_address, measurement_date)
                    )""")

plug_ips = ["192.168.XXX.XXX", "192.168.XXX.XXX", "192.168.XXX.XXX"]
plug_info = {}
plug_connections = {}


def log_daily_data(plug_conn, year, month):
    daily = plug_conn.get_emeter_daily(year, month)
    for day in daily.keys():
        date_for_entry = datetime.date(year, month, day)
        formatted_date = date_for_entry.strftime('%Y-%m-%d')
        day_power_wh = int(daily[day] * 1000)
        db_conn.execute(
            "INSERT OR REPLACE INTO power_usage (mac_address, device_label,measurement_date,measurement_wh) "
            "VALUES (?,?,?,?)", (plug_info[plug_ip]['mac'], plug_info[plug_ip]['alias'],
                                 formatted_date, day_power_wh))


for plug_ip in plug_ips:
    plug = SmartPlug(plug_ip)
    sys_info = plug.get_sysinfo()
    plug_info[plug_ip] = {
        'mac': sys_info['mac'],
        'alias': sys_info['alias']
    }
    plug_connections[plug_ip] = plug
    # try previous month
    month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    log_daily_data(plug, month_ago.year, month_ago.month)
    # current month
    now = datetime.datetime.now()
    log_daily_data(plug, now.year, now.month)

db_conn.commit()

cur = db_conn.execute("""SELECT device_label,measurement_date,SUM(measurement_wh) 
FROM power_usage 
GROUP BY device_label,measurement_date ORDER BY date(measurement_date) DESC""")
results = cur.fetchall()

summary = {}
for row in results:
    label, date, wh = row
    if not (date in summary):
        summary[date] = {'total_wh': 0, 'device_details': []}
    summary[date]['total_wh'] += wh
    summary[date]['device_details'].append({'device': label, 'wh': wh})

template = env.get_template('daily_template.html')
rendered = template.render(summary=summary)

with open('daily_rendered.html', 'w') as f:
    f.write(rendered)

db_conn.close()

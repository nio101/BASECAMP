# influxDB.py

"""
BC_commons - influxDB sub_module

handles all the read/write stuff with influxDB

- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""


# from . import tools as bc
import basecamp.tools as bc
from influxdb import InfluxDBClient
import datetime


# =======================================================
# Functions

def write(influx_json_body):
    influx_json_body[0]['time'] = datetime.datetime.utcnow().isoformat()
    bc.log.debug("writing to influxDB: "+str(influx_json_body))
    try:
        client.write(influx_json_body)
    except Exception as e:
        bc.log.error(e.__str__())
        bc.notify("ERROR", "Can't reach influxDB!")


def read(query):
    bc.log.debug("requesting from influxDB: "+str(query))
    try:
        client.query(query)
    except Exception as e:
        bc.log.error(e.__str__())
        bc.notify("ERROR", "Can't reach influxDB!")


# =======================================================
# Init

def init():
    global client
    _influxdb_host = bc.config.get("influxDB", "influxdb_host")
    _influxdb_port = bc.config.get("influxDB", "influxdb_port")
    _influxdb_query_url = "http://"+_influxdb_host+":"+_influxdb_port+"/query"

    # influxDB init
    client = InfluxDBClient(_influxdb_host, _influxdb_port)
    client.switch_database('basecamp')
    print("influxDB will be contacted on "+str(_influxdb_host)+":"+str(_influxdb_port))
    print("*** basecamp.influxDB: influxDB client initialized ***")

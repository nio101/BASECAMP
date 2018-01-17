# db.py

"""
basecamp.db

bastracts all the init/read/write stuff with influxDB

- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""

import basecamp.tools as tools
from influxdb import InfluxDBClient
import datetime


# =======================================================
# basecamp.db's variables shared with client services

influx_json_body_template = [
    {
        "measurement": "logs",
        "tags": {},
        "time": "",
        "fields": {}
    }
]

_influxdb_host = None
_influxdb_port = None
client = None


# =======================================================
# Functions

def write_points(influx_json_body):
    """
    write to the db using the json body
    returns: True if success
    """
    # TODO: fill in the 'time field' if a bool option is True (default)
    if client is None:
        print("Error: db.client has not been initialized!")
        exit(1)
    influx_json_body[0]['time'] = datetime.datetime.utcnow().isoformat()
    tools.log.debug("writing to influxDB: "+str(influx_json_body))
    try:
        client.write_points(influx_json_body)
    except Exception as e:
        tools.log.error(e.__str__())
        tools.notify("ERROR", "while trying to write to influxDB with json_body={}".format(str(influx_json_body)))
        return False
    return True


def query(query):
    """
    query the db using a query string
    """
    if client is None:
        print("Error: db.client has not been initialized!")
        exit(1)
    tools.log.debug("requesting from influxDB: "+str(query))
    try:
        client.query(query)
    except Exception as e:
        tools.log.error(e.__str__())
        tools.notify("ERROR", "while querying influxDB with query={}".format(query))
    # TODO: we're not returning anything here !?!
    return


# =======================================================
# Init

def init():
    """
    initialize the influxDB access
    returns: a JSON body for writing
    """
    global _influxdb_host
    global _influxdb_port
    global client
    if tools.config is None:
        print("ERROR: tools.config has not been initialized!")
        exit(1)
    else:
        _influxdb_host = tools.config.get("influxDB", "influxdb_host")
        _influxdb_port = tools.config.get("influxDB", "influxdb_port")
        # _influxdb_query_url = "http://"+_influxdb_host+":"+_influxdb_port+"/query"

        # influxDB init
        client = InfluxDBClient(_influxdb_host, _influxdb_port)
        client.switch_database('basecamp')
        print("influxDB will be contacted on "+str(_influxdb_host)+":"+str(_influxdb_port))
        print("*** basecamp.influxDB: influxDB client initialized ***")
        return list(influx_json_body_template)

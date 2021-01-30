# SystemD services status monitoring tool
# Alexey Nizhegolenko 2021
# Standalone background script for monitoring the SystemD services status
# Sending into the time series databases for drawing dashboards and alerting


import os
import re
import sys
import logging
import subprocess
import logging.handlers
import configparser
import parsedatetime
from time import time, sleep
from datetime import datetime
from influxdb import InfluxDBClient


class SyslogBOMFormatter(logging.Formatter):
    def format(self, record):
        result = super().format(record)
        return "ufeff" + result


handler = logging.handlers.SysLogHandler('/dev/log')
formatter = SyslogBOMFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
root = logging.getLogger(__name__)
root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
root.addHandler(handler)


def sendout(influxhost, influxport, influxdbdb, influxuser, influxpasswd, srvstatus, measurement): # NOQA

    client = InfluxDBClient(host=influxhost, port=influxport,
                            username=influxuser, password=influxpasswd, database=influxdbdb) # NOQA
    srvinfo = {}
    metrics = []
    sendtags = {}
    hostname = os.uname()[1]

    sendtags['host'] = hostname
    sendtags['service'] = srvstatus[0]
    srvinfo['measurement'] = measurement
    srvinfo['tags'] = sendtags
    srvinfo['fields'] = srvstatus[1]

    metrics.append(srvinfo)

    # Sending json data to InfluxDB
    try:
        client.write_points(metrics)
    except Exception:
        logging.exception("Issues with sending data to InfluxDB server: ") # NOQA


def service_stat(service, user=False):

    # Preparing variables and params
    service_name = ''
    service_status = {}

    # Getting SystemD services status
    if user:
        out = subprocess.Popen(["systemctl", "--user", "status", service], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)  # NOQA
    else:
        out = subprocess.Popen(["systemctl", "status", service], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) # NOQA
    output, err = out.communicate()

    service_regx = r"Loaded:.*\/([^ ]*);"
    status_regx = r"Active:(.*) since (.*);(.*)"
    status_regx_fail = r"Active:(.*) ([^ ]+) since (.*);(.*)"

    output = output.decode("utf-8")
    for line in output.splitlines():
        # Match string like: name.service - Some Application Decription
        try:
            service_search = re.search(service_regx, line)
        except Exception:
            continue
        if service_search:
            service_name = service_search.group(1)
            continue

        # Matching string like: Active: inactive (dead) since Wed 2018-09-19 10:57:30 EEST; 4min 26s ago  # NOQA
        status_search = re.search(status_regx, line)
        status_search_f = re.search(status_regx_fail, line)

        if status_search:
            status = status_search.group(1).strip()
            status_fail = status_search_f.group(1).strip().split()[0]
            if status == 'active (running)':
                service_status['status'] = 1
            elif status == 'active (exited)':
                service_status['status'] = 2
            elif status == 'inactive (dead)':
                service_status['status'] = 3
            elif status_fail == 'failed':
                service_status['status'] = 4
            else:
                service_status['status'] = 0

            # Get and convert service status "since" time in to seconds
            since_date = status_search.group(2).strip()
            cal = parsedatetime.Calendar()
            time_struct, parse_status = cal.parse(since_date)
            delta = datetime.now() - datetime(*time_struct[:6])
            seconds = delta.total_seconds()

            # Add all needed data to the dict
            service_status['status_time'] = int(seconds)
            break

    return service_name, service_status


def main():

    os.environ["LC_ALL"] = "C"

    # Preparing for reading config file
    pwd = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    config = configparser.ConfigParser()
    config.read('%s/settings.ini' % pwd)

    # Getting params from config
    interval = config.get('INTERVAL', 'seconds')
    services = config.get('SERVICES', 'name').split()
    influxhost = config.get('INFLUXDB', 'host')
    influxport = config.get('INFLUXDB', 'port')
    influxdbdb = config.get('INFLUXDB', 'database')
    influxuser = config.get('INFLUXDB', 'username')
    influxpasswd = config.get('INFLUXDB', 'password')
    measurement = config.get('INFLUXDB', 'measurement')

    user_services = []

    if config.has_section('USER_SERVICES'):
        user_services = config.get('USER_SERVICES', 'name').split()

    now = datetime.now()
    print('Srvinfo started at %s' % now)

    while True:
        # Run loop with
        for name in services:
            if service_stat(name) == ('', {}):
                pass
            else:
                srvstatus = service_stat(name)
                sendout(influxhost, influxport, influxdbdb, influxuser, influxpasswd, srvstatus, measurement) # NOQA
        for name in user_services:
            if service_stat(name, True) == ('', {}):
                pass
            else:
                srvstatus = service_stat(name, True)
                sendout(influxhost, influxport, influxdbdb, influxuser, influxpasswd, srvstatus, measurement) # NOQA
        sleep(int(interval))


if __name__ == '__main__':

    try:
        main()
    except Exception:
        logging.exception("Oops the Exception in main(): ")
    except KeyboardInterrupt:
        logging.exception("Exception KeyboardInterrupt: ")
        sys.exit(0)

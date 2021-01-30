# Srvinfo

### Version 1.0

## Getting statuses for the systemd services with InfluxDB & Grafana

![Alt text](https://github.com/ratibor78/servicestat/blob/master/services_grafana.png?raw=true "Grafana dashboard example")
![Alt text](https://github.com/ratibor78/servicestat/blob/master/services_grafana1.png?raw=true "Grafana dashboard example")

Srvinfo - the standalone Python based script for checking the statuses of the systemd services, and sending them into the InfluxDB database.

This software have the similar functionality with the other my application [Srvstatus] (https://github.com/ratibor78/srvstatus), but in apposite to it,
this script don't use the [Telegraf] (https://www.influxdata.com/time-series-platform/telegraf/) for sending the data into the InfluxDB database.
This new script was designed as standalone one, so you don't need any additional applications for getting the systemd services statistic.

# Main Features:

- Parsing the list of the given systemd services and sending their statuses in to the InfluxDB database.
- Using standard python libs for maximum easy use.
- Having an external **settings.ini** file for comfortable changing parameters.
- Having a Dockerfile inside for quick building Docker image.
- Contains an install.sh script that will do the installation process easy.
- Runs as a systemd service for easy setup

JSON format that script sends to InfluxDB looks like:

```
[
   {
      "measurement": "services_stats",
      "tags": {
         "host": "myhost",
         "service": "nginx.service"
      },
      "fields": {
         "status": 1,
         "status_time": 3966161
      }
   }
]
```

This script send a JSON format with services statuses coded by digits:
```
active (running) = 1
active (exited) = 2
inactive (dead) = 3
failed  = 4
no match = 0
```  
so you need to convert it back to string in Grafana.
You can take a look on my test Grafana dashboard to see how it may be done.

Also script provide a services names and time recent services status in seconds,
so you can use it in Grafana dashboards also.

You can find the Grafana dashboard example in service **status.json** file or find it on grafana.com: https://grafana.com/dashboards/8348

## Installation
You can install it in a few ways:

Using install.sh script:
1) Clone the repository.
2) CD into the directory and then run **install.sh**, it will asks you to set properly settings.ini parameters, like list of the services and InfluxDB settings.  
3) After the script will finish the application installation you'll need to start the systemd service with **systemctl start srvinfo.service**.

Manually:

1) Clone the repository, create an environment and install requirements
```sh
$ cd /opt && git clone https://github.com/ratibor78/srvinfo.git
$ cd /opt/srvinfo
$ python3 -m venv venv && source venv/bin/activate
$ pip3 install -r requirements.txt
```
2) Rename **settings.ini.back** to **settings.ini** and specify a list of services that you need to check in one string
separated with spaces, also set all the other parameters.
Next rename and modify the **srvinfo.service.template** file and copy into systemd directory. You need tp change the '$PWD'
in the *srvinfo.service.template** with the path of the directory with the repository.

```sh
$ cp settings.ini.bak settings.ini
$ vi settings.ini
$ cp srvinfo.service.template srvinfo.service
$ vi srvinfo.service
$ cp srvinfo.service /lib/systemd/system/
```
3) Then enable and start service
```sh
$ systemctl enable srvinfo.service
$ systemctl start srvinfo.service
```

Examples how to setup the services in the **settings.ini** file:
```
   [SERVICES]
    name = docker.service nginx.service
```
  You can also add your own **user services** list same to (systemctl --user some.service):

```
   [USER_SERVICES]
    name = syncthing.service
```

After you'll setup, modify and start the srvinfo service, you must found the services status metrics in the InfluxDB.

Have fun !

License
----

MIT

**Free Software, Hell Yeah!**

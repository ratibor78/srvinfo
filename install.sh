#! /usr/bin/env bash

##
## Installation script for Srvinfo
## Alexey Nizhegolenko 2021
##

WORKDIR=$(pwd)

echo ""
echo "Creating virtual ENV and install all needed requirements..."
sleep 1
python3 -m venv venv && source venv/bin/activate

pip3 install -r requirements.txt && deactivate

echo ""
echo "Please edit settings.ini file and set the needed parameters..."
sleep 2
cp settings.ini.back settings.ini

"${VISUAL:-"${EDITOR:-vi}"}" "settings.ini"

echo ""
echo "Installing Srvinfo systemd service..."
sleep 2
while read line
do
    eval echo "$line"
done < "./srvinfo.service.template" > /lib/systemd/system/srvinfo.service

systemctl enable srvinfo.service


echo ""
echo "Finished so you can start getting the systemd services statuses"
echo "Please run 'systemctl start srvinfo.service' for starting the Srvinfo script"
echo "Good Luck !"

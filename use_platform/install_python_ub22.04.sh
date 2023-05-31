#!/bin/bash

_WHOAMI=`whoami`

cd ~/Downloads/
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py 
python3.10 get-pip.py

if [ ! -e "/usr/bin/pip3.10" ] && [ -e "/home/$_WHOAMI/.local/bin/pip3.10" ]; then
    sudo ln -s "/home/$_WHOAMI/.local/bin/pip3.10" /usr/bin/pip3.10
fi

pip3.10 install pipenv
pipenv install --three python-telegram-bot flask gunicorn requests beautifulsoup4 bs4 chardet decorator idna peewee py
## ref.: https://stackoverflow.com/a/74994229
pip3.10 install python-telegram-bot==13.7
pip3.10 install pytz
pip3.10 install pyyaml
pip3.10 install psutil

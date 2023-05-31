#!/bin/bash
_LAN_DEV=`ifconfig -s | awk '{print $1}' | grep -E "enp|eth" | head -1`
_PPP_DEV=`ifconfig -s | awk '{print $1}' | grep "ppp" | head -1`
_DYNAMICIP="127.0.0.1"
_EXTERNALIP="168.95.1.1"

if [ "${_DYNAMICIP}" == "127.0.0.1" ] && [ ! -z "${_LAN_DEV}" ]; then
  l_get_dev_full_name=`ifconfig | grep "${_LAN_DEV}" | sed "s/: .*//g"`
  l_get_ipv4=`ifconfig "${l_get_dev_full_name}" | grep "inet " | awk '{print $2}'`
  if [ ! -z "${l_get_ipv4}" ]; then
    _DYNAMICIP="${l_get_ipv4}"
  fi
fi
if [ "${_DYNAMICIP}" == "127.0.0.1" ] && [ ! -z "${_PPP_DEV}" ]; then
  l_get_dev_full_name=`ifconfig | grep "${_PPP_DEV}" | sed "s/: .*//g"`
  l_get_ipv4=`ifconfig "${l_get_dev_full_name}" | grep "inet " | awk '{print $2}'`
  if [ ! -z "${l_get_ipv4}" ]; then
    _DYNAMICIP="${l_get_ipv4}"
  fi
fi
if [ "${_DYNAMICIP}" == "127.0.0.1" ]; then
  echo "I can not find any avaliable ip address from enp... eth... ppp..."
  exit 1
else
  _EXTERNALIP=`curl ifconfig.me 2>/dev/null 3>&1`
fi

echo "internal_ip=${_DYNAMICIP}"
echo "external_ip=${_EXTERNALIP}"
exit 0

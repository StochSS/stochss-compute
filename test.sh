#!/usr/bin/env bash

CWD=$(pwd)
TMP_DIR=$1

if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}x${NC} This script must not be run as root" 
   exit 1
fi
if [ -z $(which python3) ]; then
  echo "python3 not found"
  exit 1
fi
if [ -z $(which pip) ]; then
  echo "python3 pip not found"
  exit 1
fi
if [[ ! -f requirements.txt ]]; then
  echo "requirements.txt not found"
  exit 1
fi

if [[ -z "${TMP_DIR}" ]]; then
  TMP_DIR=/tmp/piplock.$(date +'%s%N')
fi
if [[ ! -z "$(which deactivate)" ]]; then
  deactivate
fi

mkdir -p ${TMP_DIR}
cd ${TMP_DIR}
python3 -m pip install -U pip
python3 -m pip install -U virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install wheel
pip install -v --no-cache-dir --isolated --no-warn-conflict -r ${CWD}/requirements.txt
check=$(pip check --no-cache-dir --isolated)
check_exit=$?
if [[ $check_exit -ne 0 ]]; then
  echo ${check}
  exit 1
fi
touch ${CWD}/requirements.lock
pip freeze -r ${CWD}/requirements.txt --all -l > ${CWD}/requirements.lock
deactivate
rm -rf ${TMP_DIR}
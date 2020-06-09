#!/bin/bash

source /opt/intel/openvino/bin/setupvars.sh
export OPENCV_LOG_LEVEL=SILENT

MODELS_ROOT="/srv/models"
FILENAME="${MODEL_PACKAGE##*/}"
DIRNAME=${FILENAME%.*}


if [ ! -d "$MODELS_ROOT/$DIRNAME" ]; then
    mkdir -p $MODELS_ROOT/$DIRNAME
    cd $MODELS_ROOT/$DIRNAME
    curl -SL -o model.tgz -O ${MODEL_PACKAGE}
    tar -zxf model.tgz
    rm -f model.tgz
fi

cd /app
python3 -u main.py
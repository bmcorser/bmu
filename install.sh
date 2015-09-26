#!/bin/bash
if [ -f test/system/ngrok ]; then
    echo "ngrok is present"
else
    echo "installing ngrok"
    pushd test/system
    wget https://dl.ngrok.com/ngrok_2.0.19_linux_amd64.zip -O ngrok.zip
    unzip ngrok.zip
    rm -v ngrok.zip
    popd
fi
pip install -r requirements.txt
pip install -r test-requirements.txt
pip install -e .

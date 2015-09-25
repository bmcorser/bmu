if [ -f ngrok ]; then
    echo "ngrok is present"
else
    echo "installing ngrok"
    wget https://dl.ngrok.com/ngrok_2.0.19_linux_amd64.zip -O ngrok.zip
    unzip ngrok.zip
    rm -v ngrok.zip
fi

#! /bin/sh

echo 'use `sftp -i client_keys -P 8022 localhost` to connect to sftp server'

../../main.py -c sftp.yml

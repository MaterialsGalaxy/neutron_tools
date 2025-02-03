#!/bin/bash
echo "#Galaxy stuff">>~/.bashrc
echo "export HISTORY_ID=\"$HISTORY_ID\"">>/etc/profile
echo "export API_KEY=\"$API_KEY\"">>/etc/profile
echo "export GALAXY_URL=\"$GALAXY_URL\"">>/etc/profile
echo "export GALAXY_WEB_PORT=\"$GALAXY_WEB_PORT\"">>/etc/profile
echo "export REMOTE_HOST=\"$REMOTE_HOST\"">>/etc/profile
echo "export PYTHONPATH=\"/home/shiny/miniconda3/envs/GSASII/GSAS-II/GSASII\"">>/etc/profile
exec shiny-server 2>&1 > /tmp/gxit.log

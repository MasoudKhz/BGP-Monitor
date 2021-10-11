# BGP-Monitor
Description 

# How to install and run in Ubuntu 20.04.3 LTS (GNU/Linux)
* Install following packages
- apt-get update
apt-get upgrade
sudo apt-get install libpcap0.8 libpcap0.8-dev libpcap-dev
sudo apt-get install librdkafka-dev -y
sudo apt-get install librdkafka1 -y
apt-get install build-essential -y
export KAFKA_LIBS="-L/usr/lib/x86_64-linux-gnu -lrdkafka"
export KAFKA_CFLAGS="-I/usr/include/librdkafka"
export JANSSON_CFLAGS="-I/usr/local/include/"
export JANSSON_LIBS="-L/usr/local/lib -ljansson"
pip3 install --upgrade pip
pip3 install virtualenv

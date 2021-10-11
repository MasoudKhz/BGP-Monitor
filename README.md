# BGP-Monitor
Description 

## How to install and run in Ubuntu 20.04.3 LTS (GNU/Linux)
* Install following packages
``` 
apt-get update
apt-get upgrade
sudo apt-get install libpcap0.8 libpcap0.8-dev libpcap-dev
sudo apt-get install librdkafka-dev -y
sudo apt-get install librdkafka1 -y
sudo apt-get install libtool
sudo apt-get install autoconf
sudo apt-get install build-essential -y
sudo apt-get install postgresql postgresql-contrib -y
sudo apt install default-jdk -y
export KAFKA_LIBS="-L/usr/lib/x86_64-linux-gnu -lrdkafka"
export KAFKA_CFLAGS="-I/usr/include/librdkafka"
export JANSSON_CFLAGS="-I/usr/local/include/"
export JANSSON_LIBS="-L/usr/local/lib -ljansson"
pip3 install --upgrade pip
pip3 install virtualenv
```

* Clone project from git
```
cd /usr/local
git clone ...
```

* Install Jansson 
```
cd /usr/local/jansson
./configure
make
make install
```

* Config PostgreSQL
```
sudo -u postgres psql

postgres=# CREATE DATABASE postgres;
postgres=# CREATE USER postgres WITH PASSWORD 'admin@123456';
postgres=# GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
postgres=# CREATE TABLE peer_state(peer_ip VARCHAR(20) NOT NULL, state VARCHAR(5) NOT NULL, primary key(peer_ip));
postgres=# CREATE TABLE kafka(id  SERIAL NOT NULL, PREFIX  VARCHAR(40) NOT NULL, PEER  VARCHAR(40)  NOT NULL, AS_PATH  VARCHAR(300)  NOT NULL, COMMUNITIES  VARCHAR(300)  NOT NULL, LCOMMUNITIES  VARCHAR(300)  NOT NULL, primary key(PREFIX, PEER, AS_PATH, COMMUNITIES)
);
postgres=# CREATE TABLE kafka2(id  SERIAL NOT NULL, device_ip  VARCHAR(50)  NOT NULL, peer_ip  VARCHAR(50)  NOT NULL, peer_as  VARCHAR(50)  NOT NULL, nexthub  VARCHAR(50)   NOT NULL, prefix  VARCHAR(50)   NOT NULL, comm  VARCHAR(500)  NOT NULL, primary key(peer_ip, peer_as, nexthub, PREFIX, comm)
);

postgres=# \q
```

* Install Zookeeper & Kafka
```
vim /etc/systemd/system/zookeeper.service
```
```
[Unit]
Description=Apache Zookeeper server
Documentation=http://zookeeper.apache.org
Requires=network.target remote-fs.target
After=network.target remote-fs.target

[Service]
Type=simple
ExecStart=/usr/local/kafka/bin/zookeeper-server-start.sh /usr/local/kafka/config/zookeeper.properties
ExecStop=/usr/local/kafka/bin/zookeeper-server-stop.sh
Restart=on-abnormal

[Install]
WantedBy=multi-user.target
```

```
vim /etc/systemd/system/kafka.service
```
```
[Unit]
Description=Apache Kafka Server
Documentation=http://kafka.apache.org/documentation.html
Requires=zookeeper.service

[Service]
Type=simple
Environment="JAVA_HOME=/usr/lib/jvm/java-1.11.0-openjdk-amd64"
ExecStart=/usr/local/kafka/bin/kafka-server-start.sh /usr/local/kafka/config/server.properties
ExecStop=/usr/local/kafka/bin/kafka-server-stop.sh

[Install]
WantedBy=multi-user.target
```
```
systemctl daemon-reload
sudo systemctl start zookeeper
sudo systemctl start kafka
sudo systemctl enable zookeeper
sudo systemctl enable kafka
```

* Install Pmacct
* cd /usr/local/pmacct/
* ./configure --enable-kafka --enable-jansson --enable-bgp-bins
* sudo make
* sudo make install

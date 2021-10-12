# BGP-Monitor

## How to install and run in Ubuntu 20.04.3 LTS (GNU/Linux)
* Install following packages
``` 
apt-get update
apt-get upgrade
sudo apt-get install libpcap0.8 libpcap0.8-dev libpcap-dev -y
sudo apt-get install librdkafka-dev -y
sudo apt-get install librdkafka1 -y
sudo apt-get install libtool -y
sudo apt-get install autoconf
sudo apt-get install build-essential -y
sudo apt-get install postgresql postgresql-contrib -y
sudo apt install default-jdk -y
sudo apt install python3-pip -y
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
git clone https://github.com/MasoudKhz/BGP-Monitor.git
cd BGP-Monitor
pip install -r requirements.txt
```

* Install Jansson 
```
cd /usr/local/BGP-Monitor/jansson
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
postgres=# ALTER DATABASE postgres RESET log_statement;
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
ExecStart=/usr/local/BGP-Monitor/kafka/bin/zookeeper-server-start.sh /usr/local/kafka/config/zookeeper.properties
ExecStop=/usr/local/BGP-Monitor/kafka/bin/zookeeper-server-stop.sh
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
ExecStart=/usr/local/BGP-Monitor/kafka/bin/kafka-server-start.sh /usr/local/BGP-Monitor/kafka/config/server.properties
ExecStop=/usr/local/BGP-Monitor/kafka/bin/kafka-server-stop.sh

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
```
cd /usr/local/pmacct/
./configure --enable-kafka --enable-jansson --enable-bgp-bins
sudo make
sudo make install
```

* Create your nfacctd (a binary installed with pmacct) configuration file with the following information. Modify the highlighted areas to add your relevant information. Verify nfacctd is working before removing the # in front of daemonize so logs are displayed at the terminal. Once you know everything is working uncomment this and restart nfacctd.
```
vim /usr/local/BGP-Monitor/pmacct/nfacctd.conf
```
```
plugins: kafka
# Interface :
pcap_interface: ens192
# Interface IP
nfacctd_ip: 2.189.3.152
nfacctd_port: 20013
nfacctd_time_new: true

nfacctd_disable_checks: true
bgp_daemon_msglog: true
bgp_peer_src_as_type: bgp
bgp_src_as_path_type: bgp

kafka_topic: pmacct
kafka_history:20m
kafka_history_roundoff: m
# Your Kafka Server IP
kafka_broker_host: 2.189.3.153
kafka_broker_port: 9092
kafka_refresh_time: 1
kafka_refresh_time: 10

bgp_table_dump_kafka_topic: pmacct.bgp
bgp_table_dump_refresh_time: 600
bgp_daemon: true
bgp_src_lrg_comm_type: bgp
# BGP deamon IP
bgp_daemon_ip: 2.189.3.152
# Max number of peer
bgp_daemon_max_peers: 100
nfacctd_net: bgp
nfacctd_as: bgp
# Your BGP ASN :
bgp_daemon_as: 5000
aggregate: src_host, dst_host,in_iface, out_iface, timestamp_start, timestamp_end, src_port, dst_port, proto, tos, tcpflags, tag, src_as, dst_as, peer_src_as, peer_dst_as, peer_src_ip, peer_dst_ip, local_pref, as_path
```

* SET retention time of Kafka
```
/usr/local/BGP-Monitor/kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic pmacct.bgp --config retention.ms=60000 
```

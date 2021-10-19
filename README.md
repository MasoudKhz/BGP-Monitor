# BGP-Monitor

## How to install and run in Ubuntu 20.04.3 LTS (GNU/Linux)
* Install following packages
``` 
apt-get update
apt-get upgrade
sudo apt-get install libpcap0.8 libpcap0.8-dev libpcap-dev -y
sudo apt-get install librdkafka-dev -y
sudo apt-get install librdkafka1 -y
sudo apt-get install build-essential -y
sudo apt-get install postgresql postgresql-contrib -y
sudo apt install default-jdk -y
sudo apt install python3-pip -y
sudo apt install unzip -y
sudo apt-get install autoconf
sudo apt-get install libjansson-dev
export KAFKA_LIBS="-L/usr/lib/x86_64-linux-gnu -lrdkafka"
export KAFKA_CFLAGS="-I/usr/include/librdkafka"
export JANSSON_CFLAGS="-I/usr/local/include/"
export JANSSON_LIBS="-L/usr/local/lib -ljansson"
pip3 install --upgrade pip
pip3 install virtualenv
```

* Download project from git
```
cd /usr/local
wget https://github.com/MasoudKhz/BGP-Monitor/archive/refs/heads/master.zip
unzip master.zip
mv BGP-Monitor-master BGP-Monitor-master
cd BGP-Monitor
pip install -r requirements.txt
```

* Install Jansson 
```
cd /usr/local/BGP-Monitor/jansson
sudo apt-get install libtool -y
autoreconf --force --install
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
postgres=# ALTER USER pmacct WITH SUPERUSER; 
postgres=# CREATE TABLE peer_state(device_ip VARCHAR(40) NOT NULL, peer_ip VARCHAR(20) NOT NULL, state VARCHAR(5) NOT NULL, primary key(device_ip, peer_ip));
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
ExecStart=/usr/local/BGP-Monitor/kafka/bin/zookeeper-server-start.sh /usr/local/BGP-Monitor/kafka/config/zookeeper.properties
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
cd /usr/local/BGP-Monitor/pmacct/
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

* **Start nfacctd** -> 
Nfacctd (included with pmacct) can be started with the configuration above. This will start a process that listens for incoming network flows. Once you have added the nfacctd daemon as a neighbor in your router (next bullet down) you should also see BGP state move to OPEN state with your router.
```
sudo nfacctd -f /usr/local/BGP-Monitor/pmacct/nfacctd.conf
```
* SET retention time of Kafka
```
/usr/local/BGP-Monitor/kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic pmacct.bgp --config retention.ms=60000 
```
* **Edit Crontab**
```
#write out current crontab
crontab -l > mycron
#echo new cron into cron file
echo "*/10 * * * * sudo python3 /usr/local/BGP-Monitor/script/BGP.py >> /dev/null" >> mycron
echo "*/10 * * * * sudo python3 /usr/local/BGP-Monitor/script/Kafka_Stream.py >> /dev/null" >> mycron
#install new cron file
crontab mycron
```

* **kafka2 table output**
```
   id    |   device_ip   |     peer_ip     | peer_as |     nexthub     |      prefix      |                                                                                                            comm                                                                                                             
---------+---------------+-----------------+---------+-----------------+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 3738781 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 2.56.36.0/23     | 49832 208293 50710 209173
 3738782 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 2.56.38.0/23     | 49832 208293 50710 209173
 3738783 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 5.62.131.0/24    | 49832 34929 208293 198589
 3738784 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 5.62.137.0/24    | 49832 34929 208293 198589
 3738785 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 5.62.141.0/24    | 49832 34929 208293 198589
 3738786 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 5.62.143.0/24    | 49832 34929 208293 198589
 3738787 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 5.62.148.0/24    | 49832 34929 208293 198589
 3738788 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 31.7.80.0/24     | 49832 34929 208293 198589
 3738789 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 31.7.81.0/24     | 49832 34929 208293 198589
 3738790 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 31.7.82.0/24     | 49832 34929 208293 198589
 3738791 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 31.7.84.0/24     | 49832 34929 208293 198589 198589 198589
 3738792 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 31.7.85.0/24     | 49832 34929 208293 198589
 3738793 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 31.7.87.0/24     | 49832 34929 208293 198589
 3738794 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 31.223.185.0/24  | 49832 208293 57324 212330
 3738795 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 31.223.186.0/24  | 49832 208293 50710 208365
 3738796 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.229  | 37.77.54.0/24    | 49832 34929 208293 198589
 3738797 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.0.0/16    | 49832 208293 50710
 3738798 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.7.0/24    | 49832 208293 50710
 3738799 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.8.0/24    | 49832 208293 50710
 3738800 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.12.0/24   | 49832 208293 50710
 3738801 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.13.0/24   | 49832 208293 50710
 3738802 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.16.0/23   | 49832 208293 50710
 3738803 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.19.0/24   | 49832 208293 50710
 3738804 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.31.0/24   | 49832 208293 50710
 3738805 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.40.0/24   | 49832 208293 50710
 3738806 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.48.0/24   | 49832 208293 50710
 3738807 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.51.0/24   | 49832 208293 50710
 3738808 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.53.0/24   | 49832 208293 50710
 3738809 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.58.0/24   | 49832 208293 50710
 3738810 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.62.0/24   | 49832 208293 50710
 3738811 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.71.0/24   | 49832 208293 50710
 3738812 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.72.0/24   | 49832 208293 50710
 3738813 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.73.0/24   | 49832 208293 50710
 3738814 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.75.0/24   | 49832 208293 50710
 3738815 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.76.0/24   | 49832 208293 50710
 3738816 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.77.0/24   | 49832 208293 50710
 3738817 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.79.0/24   | 49832 208293 50710
 3738818 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.80.0/24   | 49832 208293 50710
 3738819 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.89.0/24   | 49832 208293 50710
 3738820 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.90.0/24   | 49832 208293 50710
 3738821 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.97.0/24   | 49832 208293 50710
 3738822 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.98.0/24   | 49832 208293 50710
 3738823 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.101.0/24  | 49832 208293 50710
 3738824 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.103.0/24  | 49832 208293 50710
 3738825 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.108.0/24  | 49832 208293 50710
 3738826 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.111.0/24  | 49832 208293 50710
 3738827 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.115.0/24  | 49832 208293 50710
 3738828 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.120.0/24  | 49832 208293 50710
 3738829 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.133.0/24  | 49832 208293 50710
 3738830 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.140.0/24  | 49832 208293 50710
 3738831 | 78.128.78.123 | 72.14.204.116   | 15169   | 167.160.20.245  | 37.236.144.0/21  | 49832 208293 50710
 3738832 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.160.0/23  | 49832 208293 50710
 3738833 | 78.128.78.123 | 72.14.204.116   | 15169   | 172.17.17.4     | 37.236.176.0/23  | 49832 208293 50710
```
* **kafka table output**
```
   id   |     prefix      |      peer      |                                                                           as_path                                                                           |                                                   communities                                                   |                                                lcommunities                                                
--------+-----------------+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------
      1 | 1.0.0.0/24      | 167.160.20.255 | 49832 13335                                                                                                                                                 | 13335:10074 13335:19020 13335:20050 13335:20500 13335:20530 49832:2 49832:901 49832:902 49832:13335             | -
      2 | 1.0.4.0/22      | 167.160.20.255 | 49832 6939 4826 38803                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
      3 | 1.0.4.0/24      | 167.160.20.255 | 49832 6939 4826 38803                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
      4 | 1.0.5.0/24      | 167.160.20.255 | 49832 1299 4826 38803                                                                                                                                       | 1299:35000 49832:1 49832:901 49832:902 49832:1299                                                               | -
      5 | 1.0.6.0/24      | 167.160.20.255 | 49832 6939 4826 38803                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
      6 | 1.0.7.0/24      | 167.160.20.255 | 49832 1299 4826 38803                                                                                                                                       | 1299:35000 49832:1 49832:901 49832:902 49832:1299                                                               | -
      7 | 1.0.64.0/18     | 167.160.20.255 | 49832 1299 2497 7670 18144                                                                                                                                  | 1299:27000 49832:1 49832:901 49832:902 49832:1299                                                               | -
      8 | 1.0.128.0/17    | 167.160.20.255 | 49832 1299 38040 23969                                                                                                                                      | 1299:37000 49832:1 49832:901 49832:902 49832:1299                                                               | -
      9 | 1.0.128.0/18    | 167.160.20.255 | 49832 1299 38040 23969                                                                                                                                      | 1299:37000 49832:1 49832:901 49832:902 49832:1299                                                               | -
     10 | 1.0.128.0/19    | 167.160.20.255 | 49832 1299 38040 23969                                                                                                                                      | 1299:37000 49832:1 49832:901 49832:902 49832:1299                                                               | -
     11 | 1.0.128.0/24    | 167.160.20.255 | 49832 6939 4651 23969                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     12 | 1.0.129.0/24    | 167.160.20.255 | 49832 6939 4651 23969                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     13 | 1.0.130.0/23    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     14 | 1.0.132.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     15 | 1.0.133.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     16 | 1.0.136.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     17 | 1.0.137.0/24    | 167.160.20.255 | 49832 6939 4651 23969                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     18 | 1.0.138.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     19 | 1.0.139.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     20 | 1.0.141.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     21 | 1.0.144.0/20    | 167.160.20.255 | 49832 6939 4651 23969                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     22 | 1.0.160.0/19    | 167.160.20.255 | 49832 1299 38040 23969                                                                                                                                      | 1299:37000 49832:1 49832:901 49832:902 49832:1299                                                               | -
     23 | 1.0.160.0/22    | 167.160.20.255 | 49832 6939 4651 23969                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     24 | 1.0.164.0/24    | 167.160.20.255 | 49832 6939 4651 23969                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     25 | 1.0.165.0/24    | 167.160.20.255 | 49832 6939 4651 23969                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     26 | 1.0.166.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     27 | 1.0.167.0/24    | 167.160.20.255 | 49832 6939 4651 23969                                                                                                                                       | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     28 | 1.0.168.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     29 | 1.0.169.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939                                                                          | -
     30 | 1.0.170.0/24    | 167.160.20.255 | 49832 6939 38040 23969                                                                                                                                      | 49832:2 49832:901 49832:902 49832:6939          
```

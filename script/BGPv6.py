import psycopg2
import paramiko
import time
import re
from kafka import KafkaConsumer
import sys
import json
import time
import datetime
from threading import Thread, Event
from netmiko import ConnectHandler
from getpass import getpass


# t_c = 0

def A_DB(peer, peerasn, prefix, nexthop, device_ip, comm, cursor):
    postgres_insert_query = "INSERT INTO kafka2 (device_ip, peer_ip, peer_as, nexthub, prefix, comm) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (peer_ip, peer_as, nexthub, prefix, comm) DO NOTHING;"
    record_to_insert = (device_ip, peer, peerasn, nexthop, prefix, comm)
    cursor.execute(postgres_insert_query, record_to_insert)
    connection.commit()

def peer_state_set(device_ip, peer_ip, fl):
    psql_q = "INSERT INTO peer_state (device_ip, peer_ip, state) VALUES (%s,%s,%s) ON CONFLICT (device_ip, peer_ip) DO UPDATE SET state = EXCLUDED.state;"
    record_to_insert = (device_ip, peer_ip, fl)
    cursor.execute(psql_q, record_to_insert)
    connection.commit()


def peer_state(peer_ip, device_ip):
    psql_search = "SELECT state FROM peer_state WHERE peer_ip = %s AND device_ip = %s"
    cursor.execute(psql_search, (peer_ip, device_ip,))
    data = cursor.fetchall()
    for stat in data:
        return str(stat[0])


def drop_table(peer_ip, cursor):
    psql_s = "DELETE FROM kafka2 WHERE peer_ip = %s"
    cursor.execute(psql_s, (peer_ip,))
    connection.commit()


def ssh_param(device_ip, peer, conf_s, sleep_1, sleep_2):
    UN = "masoud"
    PW = "V5zViG4Uqw%"
    print("----------------------")
    network_devices = [str(device_ip)]
    peer = ''.join(peer)
    print(str(device_ip), str(peer))
    host_conf = [conf_s]
    for ip in network_devices:
        time.sleep(sleep_1)
        twrssh = paramiko.SSHClient()
        twrssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        twrssh.connect(ip, port=22, username=UN, password=PW, timeout=4)
        remote = twrssh.invoke_shell()
        remote.send('term len 0\n')
        time.sleep(sleep_2)

        stdin, stdout, stderr = twrssh.exec_command(' %s \n' % conf_s)
        opt = stdout.readlines()
        buf = "".join(opt)
        twrssh.close()
        return str(buf)


def ssh_netmiko(device_ip, peer, conf_s, sleep_1, sleep_2):
    UN = "masoud"
    PW = "V5zViG4Uqw%"
    print("----------------------")
    network_devices = [str(device_ip)]
    peer = ''.join(peer)
    print(str(device_ip), str(peer))
    host_conf = [conf_s]

    for ip in network_devices:
        time.sleep(sleep_1)
        cisco = {"device_type": "cisco_ios", "host": device_ip, "username": UN, "password": PW, "fast_cli": False, }

        for command in host_conf:
            with ConnectHandler(**cisco) as net_connect:
                output = net_connect.send_command('term len 0\n')
                time.sleep(sleep_2)
                buf = net_connect.send_command(' %s \n' % conf_s)
                time.sleep(sleep_2)
            net_connect.disconnect()
    return buf


def ssh_to_device(peer, as_num, device_ip, cursor):
    as_num_z = ''.join(as_num)
    peer_y = ''.join(peer)
    #buf = ssh_param(device_ip, peer, "sh bgp ipv6 unicast neighbors " + str(peer_y) + " advertised-routes", 6, 3)
    #print("---------------------1: "+buf)
    buf = ssh_netmiko(device_ip, peer, "sh bgp ipv6 unicast neighbors " + str(peer_y) + " advertised-routes", 6, 3)
    #print("----------------------2: "+buf)
    drop_table(peer, cursor)
    regex = r"((([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\/[0-9]+)[ |\n]+(.*?) +(([0-9a-fA-F]{0,4}:){1,7}[0-9a-fA-F]{0,4})[\n| ]+[0-9|:|a-z|A-Z]+[ |\n]+(.*)[i|?]"

    matches = re.finditer(regex, str(buf))

    for matchNum, match in enumerate(matches, start=1):
        prefix = match.group(1)
        nexthop = match.group(33)
        try:
            comm = match.group(35)
        except:
            comm = "-"
        #print("---", str(peer_y), str(as_num_z), prefix, str(nexthop), device_ip, comm)
        A_DB(str(peer_y), str(as_num_z), prefix, str(nexthop), device_ip, comm, cursor)

    peer_state_set(device_ip, peer, "1")
    print("CLOSE", peer)


def check_first_run(device_ip, peer_ip):
    psql_search = "SELECT count(*) FROM peer_state WHERE peer_ip = %s AND device_ip = %s"
    cursor.execute(psql_search, (peer_ip, device_ip,))
    data = cursor.fetchall()
    for row in data:
        count = row[0]
    if count == 0:
        return 0
    else:
        return 1


def get_bgp_summery(device_ip):
    threads = []
    conf_s = "sh bgp ipv6 unicast summary "
    host_conf = [conf_s]
    
    #x= input("OK3")
    for command in host_conf:
        buf = ssh_netmiko(device_ip, "-", "sh bgp ipv6 unicast summary ", 1, 1)
        #x= input("OK4")
        # regex = r"([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*) +[0-9]+ +([0-9]+) +"
        regex = r"((([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])).*?)\n +[0-9]+ +([0-9]+)"

        matches = re.finditer(regex, str(buf))

        con = 0
        #x= input("OK2")
        for matchNum, match in enumerate(matches, start=1):
            peer = match.group(1)
            as_num = match.group(32)
            if (peer != "2.189.3.153"):
                if (peer != "2.189.3.154"):
                    con = con + 1
                    #x= input("OK1")
                    if (check_first_run(device_ip, peer) == 0):
                        peer_state_set(device_ip, peer, "1")
                    print("ADD")
                    if (str(peer_state(peer, device_ip)) == "1"):
                        #x= input("OK")
                        peer_state_set(device_ip, peer, "0")
                        myt = Thread(target=ssh_to_device, args=(str(peer), str(as_num), str(device_ip), cursor,))
                        myt.start()
                        threads.append(myt)
                        time.sleep(10)
                        print("OK")
        for t in threads:
            t.join()


try:
    print(datetime.datetime.now())
    connection = psycopg2.connect(user="pmacct",
                                  password="admin@123456",
                                  host="localhost",
                                  port="5432",
                                  database="pmacct")
    cursor = connection.cursor()

    ###
    threads = []
    network_devices =  []#['78.128.78.123']

    check_list = 1
    plen = len(sys.argv)
    if (plen > 1):
        for input_peer in sys.argv:
            network_devices.append(str(input_peer))
    # For loop allows you to specify number of hosts
    for ip in network_devices:
        if (check_list > 0):
            myt1 = Thread(target=get_bgp_summery, args=(str(ip),))
            myt1.start()
            threads.append(myt1)
            time.sleep(15)
            print("OK --> " + str(ip))
        else:
            check_list = check_list + 1
    for t in threads:
        t.join()
    ###


except (Exception, psycopg2.Error) as error:
    print("Error while fetching data from PostgreSQL", error)

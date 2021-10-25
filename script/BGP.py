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

#t_c = 0
peer_except = ""
device_except = ""
def A_DB(peer, peerasn, prefix, nexthop, device_ip, comm, cursor):


    postgres_insert_query = "INSERT INTO kafka2 (device_ip, peer_ip, peer_as, nexthub, prefix, comm) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (peer_ip, peer_as, nexthub, prefix, comm) DO NOTHING;"
    record_to_insert = (device_ip, peer, peerasn, nexthop, prefix, comm)
    cursor.execute(postgres_insert_query, record_to_insert)
    connection.commit()

def peer_state_set(device_ip, peer_ip, fl):
    psql_q = "INSERT INTO peer_state (device_ip, peer_ip, state) VALUES (%s,%s,%s) ON CONFLICT (device_ip, peer_ip) DO UPDATE SET state = EXCLUDED.state;"
    record_to_insert = ( device_ip, peer_ip, fl)
    cursor.execute( psql_q, record_to_insert)
    connection.commit()

def peer_state(peer_ip, device_ip):
    psql_search = "SELECT state FROM peer_state WHERE peer_ip = %s AND device_ip = %s"
    cursor.execute(psql_search, (peer_ip, device_ip, ))
    data = cursor.fetchall()
    for stat in data:
        return str(stat[0])

def drop_table(peer_ip, cursor):
    
    psql_s = "DELETE FROM kafka2 WHERE peer_ip = %s"
    cursor.execute(psql_s, (peer_ip,))
    connection.commit()

def ssh_param(device_ip, peer, conf_s, sleep_1, sleep_2):
    UN = "..."  
    PW = "..."  
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
        return buf

def ssh_netmiko(device_ip, peer, conf_s, sleep_1, sleep_2):
    UN = "..."
    PW = "..."
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
    global peer_except
    global device_except
    peer_except = peer
    device_except = device_ip

    try:
        as_num_z = ''.join(as_num)
        peer_y = ''.join(peer)
        buf = ssh_param(device_ip, peer, "sh bgp ipv4 unicast neighbors " + str(peer_y) + " advertised-routes",6,3)
        drop_table(peer, cursor)
        regex = r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+) +[1-9]+\.[0-9]+\.[0-9]+\.[0-9]+ +([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) +([0-9]+.*)[i|?]"
        matches = re.finditer(regex, str(buf))

        for matchNum, match in enumerate(matches, start=1):
            prefix = match.group(1)
            nexthop = match.group(2)
            try:
                comm = match.group(3)  
            except:
                comm = "-"
            A_DB(str(peer_y), str(as_num_z), prefix, str(nexthop), device_ip, comm, cursor)
    except:
        peer_state_set(device_ip, peer,"1")
    peer_state_set(device_ip, peer,"1")
    print("CLOSE" , peer )

def check_first_run(device_ip, peer_ip):
    psql_search = "SELECT count(*) FROM peer_state WHERE peer_ip = %s AND device_ip = %s"
    cursor.execute(psql_search, (peer_ip, device_ip, ))
    data = cursor.fetchall()
    for row in data:
        count = row[0]
    if count == 0:
        return 0
    else:
        return 1

def get_bgp_summery(device_ip):
    threads = []
    conf_s = "sh ip bgp summ"
    host_conf = [conf_s]

    for command in host_conf:
        buf = ssh_netmiko(device_ip, "-", "sh ip bgp summ",1,1)

        regex = r"([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*) +[0-9]+ +([0-9]+) +"
        matches = re.finditer(regex, str(buf))

        con = 0
        for matchNum, match in enumerate(matches, start=1):
            peer = match.group(1)
            as_num = match.group(2)
            if ( peer != "2.189.3.153"):
                if(  peer != "2.189.3.154"):
                    con = con + 1
                    if (check_first_run(device_ip, peer) == 0):
                        peer_state_set(device_ip, peer,"1")
                    print("ADD")
                    if ( str(peer_state(peer,device_ip)) == "1" ):
                        peer_state_set(device_ip, peer,"0")
                        myt = Thread( target = ssh_to_device, args = ( str(peer), str(as_num), str(device_ip), cursor, ) )
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
    network_devices = []#['78.128.78.123']
    
    check_list = 0
    plen = len(sys.argv)
    if ( plen > 1 ):
        for input_peer in sys.argv:
            network_devices.append(str(input_peer))
    # For loop allows you to specify number of hosts
    for ip in network_devices:
        if ( check_list > 0 ):
            myt1 = Thread( target = get_bgp_summery, args = ( str(ip), ) )    
            myt1.start()
            threads.append(myt1)
            time.sleep(15)
            print("OK --> " +  str(ip))
        else:
            check_list = check_list + 1
    for t in threads:
        t.join()
    ###


except (Exception, psycopg2.Error) as error:
    peer_state_set(device_ip, peer,"1")
    print("Error while fetching data from PostgreSQL", error)

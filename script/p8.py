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


def A_DB(peer, peerasn, prefix, nexthop, device_ip, comm, cursor):


    #print("1: " + peer )
    #print("2: " + peerasn)
    #print("3: " + prefix)
    #print("4: " + nexthop)
    #print("5: " + device_ip)
    #q = input()
    #connection = psycopg2.connect(user="openbmp",
    #                              password="openbmp",
    #                              host="2.189.3.157",
    #                              port="5432",
    #                              database="openbmp")
    #cursor = connection.cursor()
    #postgres_insert_query = "DELETE FROM rib_out_v4"
    #cursor.execute(postgres_insert_query)
    #connection.commit()
    #print("Start")
#    print("QQQQQQQQQQQQQQQQQ")
#    k = input()
#    psql_search = "SELECT as_path, communities, lcommunities FROM kafka WHERE prefix = %s"
#    record = (prefix)
#    #print("Middle")
#    cursor.execute(psql_search, (prefix,))
#    #connection.commit()
#    data = cursor.fetchall()
#    #print("End")
#    aspath="9"
#    comm="9"
#    lcomm="9"
#    if ( str(prefix) == "0.0.0.0/0"):
#        aspath = "-"
#        comm = "-"
#        lcomm = "-"
    #print("1")
    #print(aspath)
    #print(comm)
#    for ro in data:
#        aspath = ro[0]
#        comm = ro[1]
#        lcomm = ro[2]

    #print ("AS_Path : " + str(aspath))
    #print ("Comm : " + str(comm))

    #q = input()
    #print("OK-2")    
    postgres_insert_query = "INSERT INTO kafka2 (device_ip, peer_ip, peer_as, nexthub, prefix, comm) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (peer_ip, peer_as, nexthub, prefix, comm) DO NOTHING;"
    record_to_insert = (device_ip, peer, peerasn, nexthop, prefix, comm)
    cursor.execute(postgres_insert_query, record_to_insert)
    connection.commit()
    #print("DONE")
    #print("Peer : " + peer + "          Prefix : " + prefix + "\n")

    #print("1")
#    consumer = KafkaConsumer('pmacct.bgp', bootstrap_servers=['localhost:9092'],
#                             value_deserializer=lambda m: json.loads(m.decode('utf-8')), enable_auto_commit=True, auto_offset_reset='earliest')
    #print("2")
#    for message in consumer:
#        try:
#            print("-----------------------")
#            #print(str(message[6]['ip_prefix']))
#            if ( str(message[6]['ip_prefix']) == str(prefix)):
#                print("YEEEEEEEEES")
#                comm = message[6]['comms']
#                as_path = message[6]['as_path']

#                print ( "DEVICE_IP : " + "78.128.78.123")
#                print ( "Peer : " + peer)
#                print ( "AS_NUM : " + peerasn)
#                print ( "PREFIX : " + str(comm) )
#                print ( "AS_PATH : " + as_path )
#                print ( "COMM : " + comm)
#        except:
#            xx = 1

#    print ( "DEVICE_IP : " + "78.128.78.123")
#    print ( "Peer : " + peer)
#    print ( "AS_NUM : " + peerasn)
#    print ( "PREFIX : " + str(comm) )
#    print ( "AS_PATH : " + as_path )
#    print ( "COMM : " + comm)

#    postgreSQL_select_Query = "select as_path, communities from v_ip_routes WHERE peername = %s AND prefix = %s"
#    record = (nexthop, prefix)
#    cursor.execute(postgreSQL_select_Query, record)
#    mobile_records = cursor.fetchall()

#    if(str(prefix) == "0.0.0.0/0"):
#        as_p = "-"
#        comm = "-"

#    for row in mobile_records:
#        as_p = row[0]
#        comm = row[1]

    #postgres_insert_query = "DELETE FROM nna_table_1"
    #cursor.execute(postgres_insert_query)
    #connection.commit()

#    postgres_insert_query = """ INSERT INTO nna_table_v4 (routername, peername, peerip, peerasn, prefix, aspath, communities) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
#    record_to_insert = (routername, peername, peer, peerasn, prefix, as_p, comm)
#    cursor.execute(postgres_insert_query, record_to_insert)
#   connection.commit()

def peer_state_set(peer_ip, fl):
    psql_q = "INSERT INTO peer_state (peer_ip, state) VALUES (%s,%s) ON CONFLICT (peer_ip) DO UPDATE SET state = EXCLUDED.state;"
    record_to_insert = ( peer_ip, fl)
    cursor.execute( psql_q, record_to_insert)
    connection.commit()

def peer_state(peer_ip):
    psql_search = "SELECT state FROM peer_state WHERE peer_ip = %s"
    #    #connection.commit()
    #    #connection.commit()
    cursor.execute(psql_search, (peer_ip,))
    #connection.commit()
    data = cursor.fetchall()
    for stat in data:
        #print("OK", stat[0])
        return str(stat[0])

def drop_table(peer_ip, cursor):
    
    psql_s = "DELETE FROM kafka2 WHERE peer_ip = %s"
    #record = (prefix)
    cursor.execute(psql_s, (peer_ip,))
    #data = cursor.fetchall()
    connection.commit()

def ssh_to_device(peer, as_num, device_ip, cursor):
    UN = "masoud"  # input("Username : ")
    PW = "V5zViG4Uqw%"  # getpass.getpass("Password : ")

    network_devices = [str(device_ip)]
    y = ''.join(peer)
    z = ''.join(as_num)
    conf_s = "sh bgp ipv4 unicast neighbors " + str(y) + " advertised-routes"
    host_conf = ['sh bgp ipv4 unicast neighbors advertised-routes']

    # For loop allows you to specify number of hosts
    for ip in network_devices:
        #print(peer)
        #q = input()
        time.sleep(2)
        twrssh = paramiko.SSHClient()
        twrssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        twrssh.connect(ip, port=22, username=UN, password=PW)
        remote = twrssh.invoke_shell()
        remote.send('term len 0\n')
        time.sleep(1)
        # This for loop allows you to specify number of commands  you want to enter
        # Dependent on the output of the commands you may want to tweak sleep time.
        for command in host_conf:
            #remote.send(' %s \n' % conf_s)
            stdin, stdout, stderr = twrssh.exec_command(' %s \n' % conf_s)
            opt = stdout.readlines()
            buf = "".join(opt)
            
            drop_table(peer, cursor)
            #print("1")
            #bb = input()
            #time.sleep(60)
            #buf = bytes(5)
            #buf = remote.recv(0)
            #while(1):
            #    if remote.recv_ready():
                    #print("1")
                    #print(buf)
            #        buf += remote.recv(9999990000)
                    #cc = input()
            #buf = remote.recv(6553500000)
            #print("1111111111111111111111111111111")
            #print("------------")
            #xx = input()
            #print("-----------------------------")
            #q= input()
            #regex = r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+) +[1-9]+\.[0-9]+\.[0-9]+\.[0-9]+ +([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"
            #regex = r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+) +([1-9]+\.[0-9]+\.[0-9]+\.[0-9]+) +[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"
            regex = r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+) +[1-9]+\.[0-9]+\.[0-9]+\.[0-9]+ +([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) +([0-9]+.*)[i|?]"
            matches = re.finditer(regex, str(buf))

            for matchNum, match in enumerate(matches, start=1):
                prefix = match.group(1)
                nexthop = match.group(2)
                try:
                    comm = match.group(3)  
                except:
                    comm = "-"
                #y=peer  z=is_num
                #print("OK-1")
                #print( str(y), str(z), prefix, str(nexthop), device_ip, comm)
                #q = input()
                A_DB(str(y), str(z), prefix, str(nexthop), device_ip, comm, cursor)
                #remote.close()
                #print("NO-1")
                #e = input()

        twrssh.close()
        peer_state_set(peer,"1")
        print("CLOSE" , peer )
        break

try:
    print(datetime.datetime.now())
    connection = psycopg2.connect(user="postgres",
                                  password="admin@123456",
                                  host="localhost",
                                  port="5432",
                                  database="postgres")
    cursor = connection.cursor()

    #postgres_insert_query = "DELETE FROM rib_out_v4"
    #cursor.execute(postgres_insert_query)
    #connection.commit()

    #postgres_insert_query = "DELETE FROM nna_table_v4"
    #cursor.execute(postgres_insert_query)
    #connection.commit()

    ###
    UN = "masoud"  # input("Username : ")
    PW = "V5zViG4Uqw%"  # getpass.getpass("Password : ")
    network_devices = ['78.128.78.123']
    device_ip = "78.128.78.123"
    #y = ''.join(n_ip)
    #z = ''.join(h_ip)
    #q = str(peerasn)
    #w = ''.join(r_n)
    conf_s = "sh ip bgp summ"
    host_conf = ['sh bgp ipv4 unicast neighbors advertised-routes']

    # For loop allows you to specify number of hosts
    for ip in network_devices:
        #print(ip)
        #peer_state_set(peer
        twrssh = paramiko.SSHClient()
        twrssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        twrssh.connect(ip, port=22, username=UN, password=PW)
        remote = twrssh.invoke_shell()
        remote.send('term len 0\n')
        time.sleep(1)
        # This for loop allows you to specify number of commands  you want to enter
        # Dependent on the output of the commands you may want to tweak sleep time.
        for command in host_conf:
            remote.send(' %s \n' % conf_s)
            time.sleep(1)
            buf = remote.recv(65000)
#            print(buf)

            # regex = r"([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*\/[0-9]*)"
            # subst = "\\2"
            # matches = re.finditer(regex, str(buf))

            regex = r"([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*) +[0-9]+ +([0-9]+) +"
            matches = re.finditer(regex, str(buf))

            con = 0
            for matchNum, match in enumerate(matches, start=1):
                peer = match.group(1)
                as_num = match.group(2)
                if ( peer != "2.189.3.153"):
                    if(  peer != "2.189.3.154"):
                        con = con + 1
                        peer_state_set(peer,"1")
                        print("ADD")
                       # q = input()
                        #ssh_to_device(str(peer), str(as_num), str(device_ip), cursor)
                        #if( con ==1 ):
                        if ( str(peer_state(peer)) == "1" ):
                            peer_state_set(peer,"0")
                            #print("ADD2")
                            #q = input()
                            myt = Thread( target = ssh_to_device, args = ( str(peer), str(as_num), str(device_ip), cursor, ) )
                            myt.start()
                        #if ( con%2 == 0):
                            time.sleep(10)
                            print("OK")
                        #q = input()
                        #time.sleep(3)
                        #if ( con %2 == 0 ):
                        #    time.sleep(3)
                        #print("OKKKKKKKKKKKKKKK")
                        #time.sleep(100000)
                        #print (con)
                        #con = con + 1
            # f = open('sshlogfile0001.txt', 'a')
            # f.write(buf)
            # f.close()
        twrssh.close()
        print("FINISH")
        print(datetime.datetime.now())
    ###


except (Exception, psycopg2.Error) as error:
    print("Error while fetching data from PostgreSQL", error)

#class MyThread(threading.Thread):
#    def run(self):
#        print ( self.getpeer() , self.getas_num(), self.device_ip() )
#        qqq = input()
#        ssh_to_device(self.getpeer(), self.getas_num(), self.device_ip(), self.getcursor())
                                    

#finally:
    # closing database connection.
#    if connection:
#        cursor.close()
#        connection.close()
#        print("PostgreSQL connection is closed")

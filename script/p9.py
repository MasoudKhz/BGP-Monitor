from kafka import KafkaConsumer
import datetime
import psycopg2
import paramiko
import json
import sys
import threading
import time
import os
flag = 1

#consumer = KafkaConsumer ('pmacct.bgp',bootstrap_servers = ['localhost:9092'], value_deserializer=lambda m: json.loads(m.decode('utf-8')), enable_auto_commit=True, auto_offset_reset='earliest', consumer_timeout_ms=10000 )
#consumer2 = KafkaConsumer ('pmacct.bgp',bootstrap_servers = ['localhost:9092'], value_deserializer=lambda m: json.loads(m.decode('utf-8')), enable_auto_commit=True, auto_offset_reset='lastest', consumer_timeout_ms=10000 )

os.system("systemctl restart kafka")
time.sleep(10)

connection = psycopg2.connect(user="postgres", password="admin@123456", host="localhost", port="5432", database="postgres")
cursor = connection.cursor()

##connection2 = psycopg2.connect(user="postgres", password="m1315458", host="localhost", port="5432", database="postgres")
##cursor2 = connection2.cursor()

#postgres_insert_query = "INSERT INTO kafka (PREFIX, AS_PATH, COMMUNITIES, LCOMMUNITIES) VALUES (%s,%s,%s,%s) ON CONFLICT (PREFIX) DO UPDATE SET AS_PATH = EXCLUDED.AS_PATH, COMMUNITIES = EXCLUDED.COMMUNITIES, LCOMMUNITIES = EXCLUDED.LCOMMUNITIES;"#, COMMUNITIES= %(COMMUNITIES)s"

postgres_insert_query = "INSERT INTO kafka (PREFIX, PEER, AS_PATH, COMMUNITIES, LCOMMUNITIES) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (PREFIX, PEER, AS_PATH, COMMUNITIES) DO UPDATE SET LCOMMUNITIES = EXCLUDED.LCOMMUNITIES;"

class MyThread1(threading.Thread):
    def run(self):
        con1 = 1
        consumer = KafkaConsumer ('pmacct.bgp',bootstrap_servers = ['localhost:9092'], value_deserializer=lambda m: json.loads(m.decode('utf-8')), enable_auto_commit=True, auto_offset_reset='earliest', consumer_timeout_ms=15000 )
        while(1):
            try:
                flag = 1
                check = 1
                print ("CON1 : ", con1)
                #con1 = 1
                if ( flag == 1 ):
                    for message in consumer:
                        try:
                            #print("aaa")
                            #con1 = con1 + 1
                            if ( check == 1 ):
                                postgres_in = "DELETE FROM kafka"
                                cursor.execute(postgres_in)
                                connection.commit()
                                check = 0;
                                print("DELETE")
                            #print("1")
                            #a = input()
                            x1 = str(message[6]['ip_prefix'])
                            x2 = str(message[6]['as_path'])
                            x3 = str(message[6]['comms'])
                            x4 = "-"
                            x5 = str(message[6]['peer_ip_src'])
                            try:
                                x4 = str(message[6]['lcomms'])
                            except:
                                q = 4
                            record_to_insert = (x1, x5, x2, x3, x4)
                            cursor.execute(postgres_insert_query, record_to_insert)
                            connection.commit()
                            #print("3")
                            #a = input()
                        except:
                            #print("E1")
                            q = 1
            except:
                #print("E2")
                q = 4

class MyThread2(threading.Thread):
    def run(self):
        con2 = 1
        consumer2 = KafkaConsumer ('pmacct.bgp',bootstrap_servers = ['localhost:9092'], value_deserializer=lambda m: json.loads(m.decode('utf-8')), enable_auto_commit=True, auto_offset_reset='lastest', consumer_timeout_ms=15000 )
        while(1):
            try:
                check2 = 1
                flag = 2
                #print("start-2")
                #a = input()
                #print ("CON2 : ",con2)
                #con2 = 1
                if ( flag == 2 ):
                    for message2 in consumer2:
                        #print("aaaaaaaaaa")
                        #a = input()
                        try:
                            #con2 = con2 + 1 
                            #if ( check2 == 1 ):
                            #    postgres_in2 = "DELETE FROM kafka"
                            #    cursor.execute(postgres_in2)
                            #    connection.commit()
                            #    check2 = 0;
                            #print("2")
                            #a = input()
                            xx1 = str(message2[6]['ip_prefix'])
                            xx2 = str(message2[6]['as_path'])
                            xx3 = str(message2[6]['comms'])
                            xx4 = "-"
                            xx5 = str(message[6]['peer_ip_src'])
                            try:
                                xx4 = str(message2[6]['lcomms'])
                            except:
                                 q = 4
                            record_to_insert2 = (xx1, xx5, xx2, xx3, xx4)
                            cursor2.execute(postgres_insert_query, record_to_insert2)
                            connection2.commit()
                            #print("4")
                            #a = input()
                        except:
                            q = 1
            except:
                #print("ERRRRR")
                q = 2

#for x in range(2):
mythread = MyThread1(name = "Thread-1")
mythread.start()
time.sleep(.9)

#mythread = MyThread2(name = "Thread-1")
#mythread.start()
#time.sleep(.9)




print(datetime.datetime.now())

##consumer = KafkaConsumer ('pmacct.bgp',bootstrap_servers = ['localhost:9092'], value_deserializer=lambda m: json.loads(m.decode('utf-8')), enable_auto_commit=True, auto_offset_reset='earliest', consumer_timeout_ms=10000 )
##consumer2 = KafkaConsumer ('pmacct.bgp',bootstrap_servers = ['localhost:9092'], value_deserializer=lambda m: json.loads(m.decode('utf-8')), enable_auto_commit=True, auto_offset_reset='lastest', consumer_timeout_ms=10000 )

##connection = psycopg2.connect(user="postgres", password="m1315458", host="localhost", port="5432", database="postgres")

##cursor = connection.cursor()
#print("3")
#postgres_insert_query = "INSERT INTO kafka (PREFIX, AS_PATH, COMMUNITIES) VALUES (%s,%s,%s)"
##postgres_insert_query = "INSERT INTO kafka (PREFIX, AS_PATH, COMMUNITIES, LCOMMUNITIES) VALUES (%s,%s,%s,%s) ON CONFLICT (PREFIX) DO UPDATE SET AS_PATH = EXCLUDED.AS_PATH, COMMUNITIES = EXCLUDED.COMMUNITIES, LCOMMUNITIES = EXCLUDED.LCOMMUNITIES;"#, COMMUNITIES= %(COMMUNITIES)s"
#print ("2")

#consumer = KafkaConsumer('pmacct.bgp', bootstrap_servers=['localhost:9092'], value_deserializer=lambda m: json.loads(m.decode('utf-8')))
#consumer = KafkaConsumer ('pmacct.bgp',bootstrap_servers = ['localhost:9092'],
#        value_deserializer=lambda m: json.loads(m.decode('utf-8')))



#print("2")
#while(1):
#    try:
#        check = 1
#        for message in consumer:
#            try:
#                if ( check == 1 ):
#                    postgres_in = "DELETE FROM kafka"
#                    cursor.execute(postgres_in)
#                    connection.commit()
#                    check = 0;
#        #print (message)
#        #x = input()
#        #print("1")
#        #con = con + 1
#        #if ( con == 10000 ):
#        #    print (datetime.datetime.now())
#        #    print ("--------------------------------------------")
#                x1 = str(message[6]['ip_prefix'])
#                x2 = str(message[6]['as_path'])
#                x3 = str(message[6]['comms'])
#                x4 = "-"
#                try:
#                    x4 = str(message[6]['lcomms'])
#                except:
#                    q = 4
#        #x4 = "1"
#        #x5 = "2"
#        #x4 = str("1")
#        #print("1")
#                record_to_insert = (x1, x2, x3, x4)
#        #print("2")
#                cursor.execute(postgres_insert_query, record_to_insert)
#        #print("3")
#                connection.commit()
#        #print("4")
#        #print ("Ok")
#            except:
#                q = 1
#    except:
#        q = 2

print ("Finish")
print(datetime.datetime.now())


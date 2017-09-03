import sys
import time
import datetime
import socket
import pickle
import select
import struct
import signal
import os
import timeit
import threading

from Packet import *

if len(sys.argv) != 6:
    print('python client.py <server-host-name> <server-port#> <file-name> <N> <MSS>')
    exit(0)



class Client:

    def __init__(self, ipAddress, portNumber, fileName, windowSize, mss):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ipAddress = socket.gethostbyname(ipAddress)
        self.portNumber = portNumber
        self.fileName = fileName
        self.sock.connect((self.ipAddress, self.portNumber))
        self.sock.setblocking(0)
        self.mss = mss
        
        self.packetList = list()
        self.window_start = 0
        self.window_end = windowSize
        self.request_number = 0
        self.unacked = 0
        self.total_unacked = 0
        self.timeout =0.2
        self.sequenceNumber = 0


    


    # Calculate the checksum of the data only. Return True or False
    # Checksum from https://github.com/adamgillfillan/go-back-n has been used as reference 
    def checksum(self,msg):
        """Compute and return a checksum of the given data"""
        msg = msg.decode('utf-8')
        if len(msg) % 2:
            msg += "0"
        
        s = 0
        for i in range(0, len(msg), 2):
            w = ord(msg[i]) + (ord(msg[i + 1]) << 8)
            
            c=s+w
            s=(c & 0xffff) + (c >> 16)
        return ~s & 0xffff
    
    #rdt_Send is invoked to transfer data to server
    def rdt_send(self):
        sendingData = self.divideFile(self.mss, self.fileName, self.sequenceNumber)
        self.unacked = 0
        self.total_unacked = 0
        while self.unacked < len(sendingData):
            if self.total_unacked < self.window_end and (self.total_unacked + self.unacked) < len(sendingData):
                #sendingPkt = None
                for i in sendingData:
                    sq = int(i.sequenceNumber, 2)
                    if sq == self.total_unacked + self.unacked:
                        sendingPkt = i
                self.sock.send(pickle.dumps(sendingPkt))
                self.total_unacked += 1
                continue
            else:
                ready = select.select([self.sock], [], [], self.timeout)
                if ready[0]:
                    ackData, address = self.sock.recvfrom(4096)
                    ackData = pickle.loads(ackData)
                    if ackData.ackField != 0b1010101010101010:             #check if ack is valid
                        continue
                    
                    if int(ackData.sequenceNumber,2) == self.unacked:
                        self.unacked += 1
                        self.total_unacked -= 1
                    else:
                        self.total_unacked = 0
                        continue
                else:
                    print('Timeout, sequence number = ', self.unacked) 
                    self.total_unacked = 0
                    continue

        print('Files are transmitted successfully.')
        self.sock.close()

       # try:
        #    for i in sendingData:
         #       self.sock.send(pickle.dumps(i))
          #      recvAck = self.sock.recv(1024)
           #     recv_ack = pickle.loads(recvAck)
            #    recv_ack.printAcknowledgement()
        #except IOError as err:
         #   print(err)

#divideFile is used to divide the file into packets of size mss
    def divideFile(self, mss, filename, sequenceNumber):
        
        sequenceNumber = format(sequenceNumber, '032b')
        with open(filename, "rb") as binary_file:
            # Read the whole file at once
            data = binary_file.read()
            # Seek position and read N bytes
            i = 0
            length = sys.getsizeof(data)
            while i <= length:
                binary_file.seek(i)  # Go to beginning
                couple_bytes = binary_file.read(mss)
                checksum = self.checksum(couple_bytes)
                if i + mss > length:
                    self.packetList.append(Packet(sequenceNumber, couple_bytes, checksum, 1))
                else:
                    self.packetList.append(Packet(sequenceNumber, couple_bytes, checksum, 0))
                i += mss
                temp=int(sequenceNumber, 2)+1
                sequenceNumber = format(temp, '032b')
        return self.packetList



def main():
    
    soc = Client(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    try:
        print('Run time:', timeit.timeit(soc.rdt_send, number = 1))    #print the delay in sending file
    except:
        print("Error occured while sending")

if __name__ == "__main__":
    main()

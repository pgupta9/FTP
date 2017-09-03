import sys
import time
import datetime
import socket
import random
import operator
import pickle
from Packet import *

if len(sys.argv) != 4:
    print("python sentiment.py <serverPort> <fileName> <p>")
    exit(1)

data = None
class Server:

    def __init__(self, port, filename, p):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = '127.0.0.1'
        self.sock.bind((self.host, port))
        self.sock.setblocking(0)
        print('Server Started on: ', self.host, port)
        self.filename = filename
        self.p = p     
        self.expected_seq = 0
        self.ack_seq = 0
        self.timeout = 2
        self.packet_loss = False

    


    # Calculate the checksum of the data only. Return True or False
    #Checksum at https://github.com/adamgillfillan/go-back-n has been used as reference
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
    
#server will start listening
    def startListener(self):
        global data
        file = open('data.txt', 'wb')
        try:
            receive_data = list()
            while True:
                try:
                    data, address = self.sock.recvfrom(4096)
                    data = pickle.loads(data)
                    prob = random.random()
                    if self.expected_seq != int(data.sequenceNumber, 2):
                            continue
                    elif data.checksum != self.checksum(data.packet):     #confirm checksum
                            continue
                        
                    elif prob <= self.p:                    #drop packet if r<=p
                            print('Packet Loss, Sequence Number = ', int(data.sequenceNumber, 2))
                            continue

                except socket.error:
                    continue
                except KeyboardInterrupt:
                    self.sock.close()
                    sys.exit(0)

                file.write(data.packet)
                sendACK = Acknowledgment(data.sequenceNumber)
                self.sock.sendto(pickle.dumps(sendACK), address)
                if data.eof == 1:                                           #eof=1 indicates end of file and last packet
                    print('File Received.')
                    sys.exit(0)
                self.expected_seq += 1
                
                
            file.close()
        except:
            pass

def main():
    server = Server(int(sys.argv[1]), sys.argv[2], float(sys.argv[3]))
    server.startListener()


if __name__ == "__main__":
    main()

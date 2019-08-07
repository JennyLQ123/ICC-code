import socket,threading
import time,random

SIZE=1024

def transfer(address,file):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(address)
    data=s.recv(SIZE)
    if data=='request':
        s.send('begin to send')
        fp=open('./client-data/%s.txt'%file,'rb')
        while True:
            data=fp.read(SIZE)
            if not data:
                break
            s.send(data)
        s.close()
        print 'connection closed'
    else:
        pass


class myThread(threading.Thread):
    def __init__(self,address,file):
        threading.Thread.__init__(self)
        self.address=address
        self.file=file
    def run(self):
        transfer(self.address,self.file)

def weight_choice(list,weight):
    new_list=[]
    for i,val in enumerate(list):
        new_list.extend([val]*weight[i])
    return random.choice(new_list)

if __name__=='__main__':
    dst=[3,8,5,19,14,9,10,6,13]
    addresses=(('10.0.3.1',5001),
                ('10.0.8.1',5001),
                ('10.0.5.1',5001),
                ('10.0.19.1',5001),
                ('10.0.14.1',5001),
                ('10.0.9.1',5001),
                ('10.0.10.1',5001),
                ('10.0.6.1',5001),
                ('10.0.13.1',5001))
    while(1):
        time.sleep(10)
        for addr in addresses[0:1]:
            file=weight_choice(["100K","1M","10M","100M"],[5,3,1,1])
            print file
            mythread=myThread(('127.0.0.1',5001),file)
            mythread.start()
            time.sleep(random.choice([1,2,3,4]))

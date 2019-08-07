import SocketServer,threading,os
import shutil,time

SIZE=1024
CONN_NUM=8

def checkdir():
    if os.path.exists('getdata'):
        shutil.rmtree('getdata')
    else:
        pass

class MySockServer(SocketServer.BaseRequestHandler):
    def handle(self):
        address,pid=self.client_address
        self.request.send('request')
        print 'sending a request for ', self.client_address
        while True:
            data=self.request.recv(SIZE)
            file_name=address[5:2]+time.strftime('%M-%S',time.localtime(time.time()))
            if data=='begin to send':
                print 'create file'
                with open('./server-data/%s.txt' % file_name, 'wb') as f:
                    while data:
                        data=self.request.recv(SIZE)
                        f.write(data)
                    f.close()
                print 'the end of file'
                break


if __name__=='__main__':
    address = ('', 5001)
    s=SocketServer.ThreadingTCPServer(address,MySockServer)
    s.serve_forever()

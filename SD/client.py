import Pyro4
import sys
import time
import pyaudio
import threading
import socket
import struct
import pickle
import os
from utils import (
    get_request_node_instance
)

@Pyro4.expose
class ClientNode:
    def __init__(self, address, r_address) -> None:
        self.address = address
        self.request_node_address = r_address
        self._request_node_list = []
    
    def run(self):
        r_node = None
        try:
            r_node = get_request_node_instance(self.request_node_address)
            if r_node.ping():
                self._request_node_list = r_node.requests_list
                print(f"Connected to {self.request_node_address}")
        except:
            print(f"Can't connect to server {self.request_node_address}")
            return
        
        while True:
            options = int(input("0. Play music.\n1. Upload music\n"))

            if options == 0:
                song_name = input("Enter song name: ")
                if song_name == '':
                    break
            
                responses_song = r_node.request_response(song_name)
                print(responses_song)
                count = 0
                if responses_song:
                    for s in responses_song.keys():
                        print(f"{count}. {s}")
                        count += 1
                    index = int(input("Enter song index: "))
                    self.recv_music(responses_song[list(responses_song.keys())[index]], list(responses_song.keys())[index])
            elif options == 1:
                path_song = input("Enter path of song: ")
                self.upload_song(path_song)
            
        
    def recv_music(self, md_add, music_name):
        # try:
            r_node = get_request_node_instance(self.request_node_address)
            if r_node is None:
                print(f"ERROR: Missing connection to server {self.request_node_address}")
                return
            port = r_node.play_song(md_add, music_name)
            # t1 = threading.Thread(target=r_node.play_song, args=([self.address, music_index]))
            # t1.setName("play song")
            # t1.start()

            p = pyaudio.PyAudio()
            CHUNK = 1024
            stream = p.open(format=p.get_format_from_width(2),
            				channels=2,
            				rate=44100,
            				output=True,
            				frames_per_buffer=CHUNK)

            # create socket		
            host_ip, _ = self.request_node_address.split(':')
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_address = (host_ip, port)

            print('server listening at', socket_address)
            client_socket.connect(socket_address) 
            print("CLIENT CONNECTED TO", socket_address)
            data = b""
            payload_size = struct.calcsize("Q")
            time.sleep(3)
            print("Now Playing")
            while True:
                try:
                    while len(data) < payload_size:
                        packet = client_socket.recv(4*1024) # 4K
                        if not packet: break
                        data+=packet


                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack("Q",packed_msg_size)[0]
                    
                    while len(data) < msg_size:
                        data += client_socket.recv(4*1024)
        
                    frame_data = data[:msg_size]
                    data  = data[msg_size:]
                    frame = pickle.loads(frame_data)
                    stream.write(frame)
        
                    if not len(data) < msg_size:
                        print('break')
                        break
                except:
                    client_socket.close()
                    print("Break")
                    break
                    
            client_socket.close()
            print('Audio closed')

    def upload_song(self, path):
        if os.path.exists(path):
            print("UPLOAD")
            send_up_song = threading.Thread(target=self.send_upload_song, args=([path]))
            send_up_song.start()
        else:
            print("ERROR: Invalid path")

    def send_upload_song(self, path):
        r_node = get_request_node_instance(self.request_node_address)
        if r_node is None:
            print(f"ERROR: Missing connection to server {self.request_node_address}")
            return

        host_ip, _ = self.address.split(':')
        CHUNK_SIZE = 5 * 1024
        print("SENT UPLOAD SONG")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host_ip, 0))
            print("PORT ASSIGNED")
            time.sleep(1)
            replicate_recv_thread = threading.Thread(target=r_node.put_song_in_music_data, args=([path.split('/')[-1], (host_ip, s.getsockname()[1])]))
            replicate_recv_thread.start()

            s.listen(1)
            conn, _ = s.accept()
            print("CONNECTED CLIENT WITH REQUEST")
            with conn:
                with open(path, 'rb') as f:
                    data = f.read(CHUNK_SIZE)
                    while data:
                        conn.sendall(data)
                        data = f.read(CHUNK_SIZE)
                        if data == b'':
                            conn.close()
                            break

            print('CLIENT FINISH SEND UPLOAD SONG TO REQUEST')
            s.close()

    def connect_to_server(self):
        for r_node in self._request_node_list:
            print(f"Trying connect to {r_node}")
            try:
                node = get_request_node_instance(r_node)
                if node.ping():
                    print(f"Connected to {r_node}")
                    self.request_node_address = r_node
                    break
            except:
                print(f"Can't connect to {r_node}")

    def check_connection(self):
        while True:
            try:
                node = get_request_node_instance(self.request_node_address)
                node.ping()
            except:
                print(f"Error: Missing connection to server {self.request_node_address}")
                self.connect_to_server(self.request_node_address)
            time.sleep(1)
    
            
        

def main(address, r_address, path=None):
    print("PATH", path)
    node = ClientNode(address, r_address)
    print("RUN...")
    node.run()
    print("RUNNING")
    check_connetion_thread = threading.Thread(target=node.check_connection)
    check_connetion_thread.start()

    upload_song = threading.Thread(target=node.upload_song, args=([path]))
    upload_song.start()

    # host_ip, host_port = address.split(':')
    # try:
    #     daemon = Pyro4.Daemon(host=host_ip, port=int(host_port))
    # except:
    #     print('Error: There is another node in the system with that address, please try another')
    #     return
    
    # uri = daemon.register(node)
    # ns = Pyro4.locateNS()
    # ns.register(f'CLIENT{address}', uri)

# ? <MY_ADD> <R_ADD>

if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print('Error: Missing arguments')
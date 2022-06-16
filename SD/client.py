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
            song_name = input("Enter song name: ")
            ##
            responses_song = r_node.request_response(song_name)
            count = 0
            for s in responses_song[1]:
                print(f"{count}. {s}")
                count += 1
            index = int(input("Enter song index: "))
            ##
            # r_node.play_song(responses_song[index])
            self.recv_music(responses_song[0],responses_song[1][index])
            pass
        
    def recv_music(self, md_add, music_index):
        # try:
            r_node = get_request_node_instance(self.request_node_address)
            if r_node is None:
                print(f"ERROR: Missing connection to server {self.request_node_address}")
                return
            port = r_node.play_song(md_add, music_index)
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
    
            
        

def main(address, r_address):
    node = ClientNode(address, r_address)
    node.run()

    check_connetion_thread = threading.Thread(target=node.check_connection)
    check_connetion_thread.start()

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
    else:
        print('Error: Missing arguments')
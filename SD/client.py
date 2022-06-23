import Pyro4
import sys
import time
import pyaudio
import threading
import socket
import struct
import pickle
from pynput import keyboard as kb
import os
from utils import (
    get_request_node_instance,
    TAG
)



@Pyro4.expose
class ClientNode:
    def __init__(self, address, r_address) -> None:
        self.address = address
        self.request_node_address = r_address
        self._request_node_list = []
        self.is_paused = False
    
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
                try:
                    tag = int(input("Select search form\n0. Name\n1. Genre\n2. Artist\n"))
                    
                    song_name = input(f"Enter {TAG[tag]}: ")
                    print("TAG", tag)
                    responses_song = r_node.request_response(song_name, tag)
                    print(responses_song)
                    count = 0
                    if responses_song:
                        for s in responses_song.keys():
                            print(f"{count}. {s}")
                            count += 1
                        index = int(input("Enter song index: "))
                        self.recv_music(responses_song[list(responses_song.keys())[index]], list(responses_song.keys())[index])
                except:
                    print("Somenthig went wrong! :/")
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
            current_duration = 0
            time.sleep(3)
            print("Now Playing")
            is_done = False
            escuchador = kb.Listener(self.stopped)
            escuchador.start()
            end_recv = False
            while True:
                # while not self.is_paused:
                    try:
                        try:
                            r_node.ping()
                        except:
                            if self.connect_to_server():
                                client_socket.close()
                                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                r_node = get_request_node_instance(self.request_node_address)
                                port = r_node.play_song(md_add, music_name, current_duration)
                                client_socket.connect((self.request_node_address.split(':')[0], port)) 
                            else:
                                print("ERROR: Missing connection with server.")
                                return


                        while len(data) < payload_size:
                            packet = client_socket.recv(4*1024) # 4K
                            current_duration += CHUNK/44100
                            if not packet: 
                                break
                            data+=packet


                        packed_msg_size = data[:payload_size]
                        data = data[payload_size:]
                        msg_size = struct.unpack("Q",packed_msg_size)[0]
                        
                        while len(data) < msg_size and not end_recv:
                            data += client_socket.recv(4*1024)
                            current_duration += CHUNK/44100
                            if data == b'':
                                end_recv = True
                                break

                        if not self.is_paused:
                            frame_data = data[:msg_size]
                            data  = data[msg_size:]
                            frame = pickle.loads(frame_data)
                            stream.write(frame)
            
                            if not len(data) < msg_size:
                                print('break')
                                is_done = True
                                break
                        
                        if self.is_paused and end_recv:
                            time.sleep(3)
                    except Exception as e:
                        is_done = True
                        client_socket.close()
                        print(f"Break {e}")
                        break
                # if is_done:
                #     break
                # time.sleep(3)
                    
            client_socket.close()
            print('Audio closed')

    def upload_song(self, path):
        if os.path.exists(path):
            print("UPLOAD")
            send_up_song = threading.Thread(target=self.send_upload_song, args=([path]))
            send_up_song.start()
        else:
            print("ERROR: Invalid path")

    def stopped(self, tecla):
        if str(tecla) == 'Key.space':
            self.is_paused = not self.is_paused
            print('Se ha pulsado la tecla ' + str(tecla))

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
                    # ! hacer un merge
                    self._request_node_list = node.requests_list
                    print("A")
                    return True
            except Exception as e:
                print(f"ERROR: Can't connect to {r_node}\n{e}")
        print("ERROR: Can't connect to any requests node.")
        return False

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
    # print("PATH", path)
    node = ClientNode(address, r_address)
    # print("RUN...")
    node.run()
    print("RUNNING")
    check_connetion_thread = threading.Thread(target=node.check_connection)
    check_connetion_thread.start()

    connect_to_server_thread = threading.Thread(target=node.connect_to_server)
    connect_to_server_thread.start()

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
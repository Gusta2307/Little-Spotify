import Pyro4
import threading
import pyaudio
import time
import wave
import socket
import struct
import pickle
import sys
from utils import (
    get_request_node_instance, 
    get_music_data_instance,
)

@Pyro4.expose
class RequestNode:
    def __init__(self, address, md_address) -> None:
        self.address = address
        self.music_data_address = md_address
        self.music_data_list = []
        
    @property
    def requests_list(self):
        return self._requests_list
    
    
    def ping(self):
        return True
    
    def add_requests(self, address):
        if address not in self._requests_list:
            self._requests_list.append(address)
    
    def join(self, request_address):
        self._requests_list = [self.address]
        if request_address is not None:
            node = get_request_node_instance(request_address)
            if node is not None:
                try:
                    list = node.requests_list
                    for addr in list:
                        if addr == self.address:
                            continue
                        self._requests_list.append(addr)
                        node = get_request_node_instance(addr)
                        if node is not None:
                            node.add_requests(self.address)
                except:
                    return False
            else:
                return False
        return True
    

    # ! VERIFICAR TODOS LOS MUSIC DATA
    
    def request_response(self, music_name):
        result = dict()
        for md_add in self.music_data_list:
            try:
                print(self.music_data_list)
                print(md_add)
                music_node = get_music_data_instance(md_add)
                song = music_node.get_music_by_name(music_name)
                print(song)
                if song is not None and song != []:
                    for s in song:
                        if s in result.keys():
                            result[s].append(md_add)  
                        else:
                            result[s] = [md_add]
                    
                    #return md_add, song
            except:
                continue
        return result
                
        
    def play_song(self, md_add, music_name):
        for md in md_add:
            try: 
                
                music_node = get_music_data_instance(md)

                port = music_node.send_music_data(music_name)

                server_socket = socket.socket()
                c_host_ip, _ = self.address.split(':')
                server_socket.bind((self.address.split(':')[0], 0))
                print('server client listening at',(c_host_ip, server_socket.getsockname()[1]))

                t2 = threading.Thread(target=self._recv_song_frames, args=([md, port, server_socket, music_node, music_name]))
                t3 = threading.Thread(target=music_node.replicate_song, args=([music_name]))

                t2.start()
                t3.start()

                return server_socket.getsockname()[1]
            except:
                continue
        
        raise Exception("ERROR: Can't connect with any music data")


    def _recv_song_frames(self, md_add, port, server_socket, music_node, music_name):
        host_ip, _ = md_add.split(':')

        CHUNK = 1024
        # create socket
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        socket_address = (host_ip, port)
        print('server listening at',socket_address)
        client_socket.connect(socket_address) 
        print("CLIENT CONNECTED TO",socket_address)

        server_socket.listen(5)
        
        data = b""
        payload_size = struct.calcsize("Q")
        c,_ = server_socket.accept()
        current_duration = 0 #+= CHUNK/44100
        while True:
            # try:
                try:
                    music_node.ping()
                except:
                    temp_music_node = None
                    for md in self.music_data_list:
                        print(md)
                        try:
                            temp_music_node = get_music_data_instance(md)
                            if temp_music_node.contain_song(music_name):
                                print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG")
                                _port = temp_music_node.send_music_data(music_name, int(current_duration))
                                print("PORT:", _port)
                                print((md.split(':')[0], _port))
                                client_socket.close()
                                client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                                client_socket.connect((md.split(':')[0], _port))
                                music_node = temp_music_node
                                print("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
                                break

                        except:
                            continue
                    if temp_music_node is  None:
                        print("ERROR: Trying connect to other music data.")
                        return

                while len(data) < payload_size:
                    packet = client_socket.recv(4*1024) # 4K
                    current_duration += CHUNK/44100
                    if not packet: break
                    data+=packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q",packed_msg_size)[0]
                while len(data) < msg_size:
                    data += client_socket.recv(4*1024)
                    current_duration += CHUNK/44100
                frame_data = data[:msg_size]
                data  = data[msg_size:]
                frame = pickle.loads(frame_data)
                print(current_duration)
                if frame == b'':
                    server_socket.close()
                    client_socket.close()
                    break

                if c:
                    a = pickle.dumps(frame)
                    message = struct.pack("Q",len(a))+a
                    c.sendall(message)
                    

                # stream.write(frame)

            # except:
            #     server_socket.close()
            #     client_socket.close()
            #     break

        print('Audio closed')

    def update_music_data_list(self):
        while True:
            node = get_music_data_instance(self.music_data_address)
            if node is not None:
                try:
                    self.music_data_list = node.music_data_list
                except:
                    pass
            else:
                for md in self.music_data_list[1:]:
                    node = get_music_data_instance(md)
                    if node is not None:
                        self.music_data_address = md
                        self.music_data_list = node.music_data_list
                        break
            time.sleep(1)  
    
    def update_requests_list(self):
        while True:
            list = self._requests_list
            for addr in list:
                node = get_request_node_instance(addr)
                if node is None:
                    self._requests_list.remove(addr)
            time.sleep(1) 

    def put_song_in_music_data(self, path, client_conn):
        print("PUT SONG IN MUSIC DATA REQUEST")
        # host_ip_client, _ = client_address.split(':')
        request_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # socket_address = (host_ip_client, port_client)
        # print('server listening at', client_address)

        request_socket.connect(client_conn)        
        print("REQUEST CONNECTED TO CLIENT WITH ADDRESS", client_conn)

        music_data_node = get_music_data_instance(self.music_data_address)
        
        if music_data_node is None:
            print(f"ERROR: Missing connection to server {self.music_data_address}")
            return
        
        if music_data_node.contain_song(path):
            print(f"ERROR: The song {path} is already exist")
            return 

        host_ip, _ = self.music_data_address.split(':')
        CHUNK_SIZE = 5 * 1024

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host_ip, 0))
            
            time.sleep(1)
            replicate_recv_thread = threading.Thread(target=music_data_node.put_upload_song, args=([path, (host_ip, s.getsockname()[1])]))
            replicate_recv_thread.start()

            s.listen(1)
            conn, _ = s.accept()

            if conn:
                print("BBBBBBBBBBBBBBBBBBBBBBBBBBB")
                data = request_socket.recv(CHUNK_SIZE)

                while data:
                    conn.sendall(data)
                    data = request_socket.recv(CHUNK_SIZE)
                    print(data)
                    if data == b'':
                        print('FINISH RECV UPLOAD SONG TO RESEND TO MUSIC DATA')
                        request_socket.close()
                        break

            print(f'REQUEST FINISH SEND UPLOAD SONG TO MUSIC DATA {self.music_data_address}')
            s.close()
    

    def print_node_info(self):
        while True:
            print(f'\nAddress: {self.address}\
                    \nMusic Data Node: {self.music_data_address}\
                    \nMusic Data Node List: {self.music_data_list}\
                    \nRequests Node list: {self.requests_list}')
            time.sleep(10)  

def main(address, r_address, md_address):
    host_ip, host_port = address.split(':')
    try:
        daemon = Pyro4.Daemon(host=host_ip, port=int(host_port))
    except:
        print('Error: There is another node in the system with that address, please try another')
        return
    
    node = RequestNode(address, md_address)
    uri = daemon.register(node)
    ns = Pyro4.locateNS()
    ns.register(f'REQUEST{address}', uri)
    
    if node.join(r_address):
        request_thread = threading.Thread(target=daemon.requestLoop)
        request_thread.start()
        
        music_data_list_thread = threading.Thread(target=node.update_music_data_list)
        music_data_list_thread.start()
        
        request_list_thread = threading.Thread(target=node.update_requests_list)
        request_list_thread.start()
        
        # print_thread = threading.Thread(target = node.print_node_info)
        # print_thread.start()
    
    else:
        print(f'Error: Could not connect to the network, no music data node with address: {md_address}')



# ? <ADD> <MD_ADD> 

if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], None, sys.argv[2])
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3]) 
    else:
        print('Error: Missing arguments')

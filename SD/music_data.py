import Pyro4
import threading
import os
import sys
import time
import wave
import re
import pickle
import struct
import socket
import stagger
import pyaudio
import wave
# from tinytag import TinyTag
from pydub import AudioSegment
from utils import (
    hashing, 
    get_music_data_instance, 
    get_chord_node_instance,
    TAG
)
from random import randint


@Pyro4.expose
class MusicDataNode:
    def __init__(self, address, chord_address, m, path):
        self.address = address
        self.chord_id = hashing(m, chord_address)
        self.chord_successors_list = []
        self.m = m
        self.path = path
    
    @property
    def music_data_list(self):
        return self._music_data_list 
    
    def ping(self):
        return True

    def add_music_data(self, address):
        if address not in self._music_data_list:
            self._music_data_list.append(address)
        
    def join(self, music_address):
        self._music_data_list = [self.address]
        if music_address is not None:
            node = get_music_data_instance(music_address)
            print(node)
            if node is not None:
                try:
                    list = node.music_data_list
                    print(list)
                    for addr in list:
                        if addr == self.address:
                            continue
                        self._music_data_list.append(addr)
                        node = get_music_data_instance(addr)
                        if node is not None:
                            node.add_music_data(self.address)
                except:
                    return False
            else:
                return False
        return True

    def update_chord_successors_list(self):
        while True:
            node = get_chord_node_instance(self.chord_id)
            if node is not None:
                try:
                    self.chord_successors_list = node.successors_list
                except:
                    pass
            time.sleep(1)  

    def update_music_data_list(self):
        while True:
            list = self._music_data_list
            for addr in list:
                node = get_music_data_instance(addr)
                if node is None:
                    self._music_data_list.remove(addr)
            time.sleep(1) 
    
    def print_node_info(self):
        while True:
            print(f'\nAddress: {self.address}\
                    \nChord node: {self.chord_id}\
                    \nChord node successors list: {self.chord_successors_list}\
                    \nMusic_Data list: {self.music_data_list}')
            time.sleep(10)   
    
    def get_music(self, tag, type_tag):
        songs = []
        while True:
            chord_node = get_chord_node_instance(self.chord_id)
            if chord_node is None:
                chord_node = self.change_chord_node()
                
            try:
                query_hash = hashing(self.m, tag)
                if query_hash is None:
                    print("ERROR")
                    return songs
                #songs = chord_node.get_value(query_hash, genre)
                songs= None
                if songs is None:
                    songs = self.find_song(tag, type_tag)
                    if songs != []:
                        chord_node.save_key(query_hash, (tag, songs))
                    else:
                        print("No se encontro la cancion solicitada")
                        return songs
                    
                return songs
            except Exception as e:
                print(e)
                break
                # if not self.chord_successors_list:
                #     print(f'Error: Could not connect with chord node {self.chord_id}')
                #     break
        return songs


    def find_song(self, tag, type_tag):
        _songs = []
        print(tag, type_tag)
        for mn in os.listdir(self.path):
            mp3 = stagger.read_tag(os.path.join(self.path, mn))
            print("ABC", getattr(mp3, TAG[type_tag]))
            if re.search(str(tag).lower(), str(getattr(mp3, TAG[type_tag])).lower()):
                _songs.append(mn)
        return _songs

    def send_music_data(self, music_name, _start=0):
        host_ip, _ = self.address.split(":")
        server_socket = socket.socket()
        server_socket.bind((host_ip, 0))
        port = server_socket.getsockname()[1]
        t1 = threading.Thread(target=self._send_frames, args=([server_socket, music_name, host_ip, port, _start]))
        t1.start()
        return port

    def _send_frames(self, server_socket, music_name, r_ip, port, _start=0):
        server_socket.listen(5)
        CHUNK = 1024
        # wf = wave.open(os.path.join(self.path, music_name), 'rb')

        music_file = AudioSegment.from_file(os.path.join(self.path, music_name))

        _slice = 10
        start = _start
        end = start + _slice

        print('server listening at',(r_ip, port))

        client_socket,_ = server_socket.accept()
    
        data = None
        while True:
            if client_socket:
                while True:
                    try:
                        data = music_file[start*1000:end*1000]._data#.decode('UTF-8')
                        # print(data)
                        a = pickle.dumps(data)
                        message = struct.pack("Q",len(a))+a
                        client_socket.sendall(message)
                        print(f'Sent song {end}')
                        if data == b'':
                            client_socket.close()
                            break

                        start = end
                        end += _slice
                    except:
                        client_socket.close()
                        break
                client_socket.close()
                break
    
    def replicate_song(self, music_name):
        for address in  self.music_data_list[1:]:
            node = get_music_data_instance(address)
            if not node.contain_song(music_name):
                print(f'Replicando: {address}')
                replicate_send_thread = threading.Thread(target=self.send_replicate_song, args=([music_name, node]))
                replicate_send_thread.start() 
            else:
                print("REPLICA: El archivo ya se ha replicado")

    def contain_song(self, music_name):
        return music_name in os.listdir(path=self.path)

    def send_replicate_song(self, music_name, node):
        host_ip, _ = self.address.split(':')
        CHUNK_SIZE = 5 * 1024
        FILE = os.path.join(self.path, music_name)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host_ip, 0))

            replicate_recv_thread = threading.Thread(target=node.recv_replicate_song, args=([music_name, self.address, s.getsockname()[1]]))
            replicate_recv_thread.start()

            s.listen(1)
            conn, addr = s.accept()
            with conn:
                with open(FILE, 'rb') as f:
                    data = f.read(CHUNK_SIZE)
                    while data:
                        conn.sendall(data)
                        data = f.read(CHUNK_SIZE)
                        if data == b'':
                            f.close()
                            break
            s.close()

    def recv_replicate_song(self, music_name, md_add, port):
        host_ip, _ = md_add.split(':')
        CHUNK_SIZE = 5 * 1024
        FILE = os.path.join(self.path, music_name)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((host_ip, int(port)))

            with open(FILE, "wb") as f:        
                chunk = s.recv(CHUNK_SIZE)

                while chunk:
                    f.write(chunk)
                    chunk = s.recv(CHUNK_SIZE)
                    if chunk == b'':
                        f.close()
                        break
                
            print(f'Replicacion Completada: {music_name} {self.address}')
            s.close()

    def put_upload_song(self, song_name, request_conn):
        # host_ip, _ = request_address.split(':')
        CHUNK_SIZE = 5 * 1024

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(request_conn)

            with open(os.path.join(self.path, song_name), "wb") as f:        
                data = s.recv(CHUNK_SIZE)

                while data:
                    f.write(data)
                    data = s.recv(CHUNK_SIZE)

                    if data == b'':
                        break
                f.close()

            print(f'SONG {song_name} UPLOADED TO {self.address}')
            s.close()

def main(address, md_address, chord_address, bits, path):
    host_ip, host_port = address.split(':')
    try:
        daemon = Pyro4.Daemon(host=host_ip, port=int(host_port))
    except:
        print('Error: There is another node in the system with that address, please try another')
        return
    
    node = MusicDataNode(address, chord_address, bits, path)
    uri = daemon.register(node)
    ns = Pyro4.locateNS()
    ns.register(f'MUSIC_DATA{address}', uri)
    
    if node.join(md_address):
        request_thread = threading.Thread(target=daemon.requestLoop)
        request_thread.start()
        
        chord_sucessor_list_thread = threading.Thread(target=node.update_chord_successors_list)
        chord_sucessor_list_thread.start()
        
        musicdata_node_list_thread = threading.Thread(target=node.update_music_data_list)
        musicdata_node_list_thread.start()
        
        # print_thread = threading.Thread(target = node.print_node_info)
        # print_thread.start()
    
    else:
        print(f'Error: Could not connect to the network, no music data with address: {md_address}')



# ? <ADD> <MD_ADD> <CHORD_ADD> <BITS> <PATH>

if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) == 5:
        main(sys.argv[1], None, sys.argv[2], int(sys.argv[3]), sys.argv[4])
    elif len(sys.argv) == 6:
        main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]) 
    else:
        print('Error: Missing arguments')
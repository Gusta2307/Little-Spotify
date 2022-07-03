import Pyro4, socket
import threading, os, sys, time, re, pickle, struct, eyed3
from pydub import AudioSegment
from utils import (
    get_node_instance, 
    TAG,
    get_duration
)

sys.path.insert(1, '../ML')

from genre_clasification import (
    Genre_Clasf,
    extract_carcteristics
)

@Pyro4.expose
class MusicDataNode:
    def __init__(self, address, path):
        self.address = address
        self.path = path
        self.genre_classifier = Genre_Clasf()
    
    @property
    def music_data_list(self):
        """
            Obtiene la lista de music data conocidos
        """
        return self._music_data_list 
    
    def ping(self):
        """
            Ping para verificar la conexion
        """
        return True

    def add_music_data(self, address):
        """
            Agrega la direccion de un music data a la lista de music data conocidos

            address: direccion del music data
        """
        if address not in self._music_data_list:
            self._music_data_list.append(address)
        
    def join(self, music_address):
        """
            Agrega un nuevo nodo music data a la red

            music_address: direccion del nuevo nodo
        """
        self._music_data_list = [self.address]
        if music_address is not None:
            node = get_node_instance(music_address, 'MUSIC_DATA')
            if node is not None:
                try:
                    list = node.music_data_list
                    for addr in list:
                        if addr == self.address:
                            continue
                        self._music_data_list.append(addr)
                        node = get_node_instance(addr, 'MUSIC_DATA')
                        if node is not None:
                            node.add_music_data(self.address)
                except:
                    return False
            else:
                return False
        return True

    def update_music_data_list(self):
        """
            Actualiza constantemente la lista de music data conocidos
        """
        while True:
            list = self._music_data_list
            for addr in list:
                node = get_node_instance(addr, 'MUSIC_DATA')
                if node is None:
                    self._music_data_list.remove(addr)
            time.sleep(1)
    
    def print_node_info(self):
        """
            Imprime la informacion del nodo
        """
        while True:
            print(f'\nAddress: {self.address}\
                    \nMusic_Data list: {self.music_data_list}')
            time.sleep(10)   
    
    def get_music(self, tag, type_tag):
        """
            Obtiene la lista de canciones que cumplan con el filtro

            tag: busqueda del usuario
            type_tag: tipo de filtrado
        """

        songs = []
        try:
            if songs == []:
                songs = self.find_song(tag, type_tag)
                if songs == []:
                    print(f"WARNING: No se encontro la cancion solicitada -> {(tag, type_tag)}")
                    return songs
            return songs
        except Exception as e:
            print(e)

    def find_song(self, tag, type_tag):
        '''
            Dado una cadena y un tipo de filtrado de busca por todas las canciones que cumplan con la pedicion del cliente y devuelve una lista con ellas.

            tag: busqueda del usuario
            type_tag: tipo de filtrado
        '''
        _songs = []
        if type_tag == 3: #See all
            return os.listdir(self.path)
        for mn in os.listdir(self.path):
            mp3 = eyed3.load(os.path.join(self.path, mn))
            if TAG[type_tag] == TAG[1] and getattr(mp3.tag, TAG[type_tag]) == None:
                print(f'{mn} no tiene genero')
                mp3.tag.genre = self.genre_classifier.predict(extract_carcteristics(os.path.join(self.path, mn)))
                mp3.tag.save()
                print(f'{mn} genero: {mp3.tag.genre}')
            if re.search(str(tag).lower(), str(getattr(mp3.tag, TAG[type_tag])).lower()):
                _songs.append(mn)
        return _songs

    def send_music_data(self, music_name, _start=0):
        """
            Crea un socket para enviar la cancion al request y retorna el puerto de escucha y la duracion de la cancion

            music_name: nombre de la cancion
            _start: punto de inicio de la cancion
        """

        host_ip, _ = self.address.split(":")
        server_socket = socket.socket()
        server_socket.bind((host_ip, 0))
        port = server_socket.getsockname()[1]
        t1 = threading.Thread(target=self._send_frames, args=([server_socket, music_name, _start]))
        t1.start()
        return port, get_duration(os.path.join(self.path, music_name))

    def _send_frames(self, server_socket, music_name, _start=0):
        """
            Envia los frames de la cancion al request

            server_socket: server socket
            music_name: nombre de la cancion
            _start: punto de inicio de la cancion
        """


        server_socket.listen(5)

        music_file = AudioSegment.from_file(os.path.join(self.path, music_name))
        _slice = 10
        start = _start
        end = start + _slice

        client_socket,_ = server_socket.accept()
    
        data = None
        while True:
            if client_socket:
                while True:
                    try:
                        data = music_file[start*1000:end*1000]._data
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
        """
            Replica la cancion en todos los music data conocidos

            music_name: nombre de la cancion
        """

        for address in  self.music_data_list[1:]:
            node = get_node_instance(address, 'MUSIC_DATA')
            if not node.contain_song(music_name):
                print(f'Replicando: {address}')
                replicate_send_thread = threading.Thread(target=self.send_replicate_song, args=([music_name, node]))
                replicate_send_thread.start() 
            else:
                print("REPLICA: El archivo ya se ha replicado")

    def contain_song(self, music_name):
        """
            Verifica si la cancion ya se encuentra en el music data
        """

        return music_name in os.listdir(path=self.path)

    def send_replicate_song(self, music_name, node):
        """
            Envia una replica de la cancion al music data

            music_name: nombre de la cancion
            node: music data al que se envia la cancion
        """

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
        """
            Recibe una replica de la cancion del music data

            music_name: nombre de la cancion
            md_add: direccion del music data que envia la cancion
            port: puerto de escucha del music data
        """

        host_ip, _ = md_add.split(':')
        CHUNK_SIZE = 5 * 1024
        FILE = os.path.join(self.path, music_name)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((host_ip, int(port)))

            with open(FILE, "wb") as f:
                try:     
                    chunk = s.recv(CHUNK_SIZE)
                    while chunk:
                        f.write(chunk)
                        chunk = s.recv(CHUNK_SIZE)
                        if chunk == b'':
                            f.close()
                            break
                except:
                    f.close()
                    s.close()
                    os.remove(FILE)
                
            print(f'Replicacion Completada: {music_name} {self.address}')
            s.close()

    def put_upload_song(self, song_name, request_conn):
        """
            Recibe una cancion del request y la guarda en el music data

            song_name: nombre de la cancion
            request_conn: tupla con ip y puerto del socket del request
        """

        CHUNK_SIZE = 5 * 1024
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(request_conn)

            with open(os.path.join(self.path, song_name), "wb") as f:   
                try:     
                    data = s.recv(CHUNK_SIZE)

                    while data:
                        f.write(data)
                        data = s.recv(CHUNK_SIZE)
                        if data == b'':
                            break
                    f.close()
                except:
                    f.close()
                    s.close()
                    os.remove(os.path.join(self.path, song_name))

            print(f'SONG {song_name} UPLOADED TO {self.address}')
            s.close()

def main(address, md_address, path):
    host_ip, host_port = address.split(':')
    try:
        daemon = Pyro4.Daemon(host=host_ip, port=int(host_port))
    except:
        print('Error: There is another node in the system with that address, please try another')
        return
    
    node = MusicDataNode(address, path)
    uri = daemon.register(node)
    ns = Pyro4.locateNS()
    ns.register(f'MUSIC_DATA{address}', uri)
    
    if node.join(md_address):
        request_thread = threading.Thread(target=daemon.requestLoop)
        request_thread.start()
        
        musicdata_node_list_thread = threading.Thread(target=node.update_music_data_list)
        musicdata_node_list_thread.start()
        
        print_thread = threading.Thread(target = node.print_node_info)
        print_thread.start()
    
    else:
        print(f'Error: Could not connect to the network, no music data with address: {md_address}')


# ? <ADD> <MD_ADD> <PATH>

if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], None, sys.argv[2])
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print('Error: Missing arguments')

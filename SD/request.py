import Pyro4, socket, struct, pickle
import sys, threading, time
from utils import (
    get_node_instance, 
)

@Pyro4.expose
class RequestNode:
    def __init__(self, address, md_address) -> None:
        self.address = address
        self.music_data_address = md_address
        self.music_data_list = []
        
    @property
    def requests_list(self):
        """
            Lista de request conocidos
        """
        return self._requests_list
    
    
    def ping(self):
        """
            Ping para verificar la conexion
        """
        return True
    
    def add_requests(self, address):
        """
            Agrega un nuevo request a la lista de conocidos

            address: direccion del request
        """

        if address not in self._requests_list:
            self._requests_list.append(address)
    
    def join(self, request_address):
        """
            Agrega un nuevo nodo request a la red

            request_address: direccion del request
        """

        self._requests_list = [self.address]
        if request_address is not None:
            node = get_node_instance(request_address, 'REQUEST')
            if node is not None:
                try:
                    list = node.requests_list
                    for addr in list:
                        if addr == self.address:
                            continue
                        self._requests_list.append(addr)
                        node = get_node_instance(addr, 'REQUEST')
                        if node is not None:
                            node.add_requests(self.address)
                except:
                    return False
            else:
                return False
        return True
    

    def request_response(self, tag, _type):
        """
            Dada respuesta a una consulta del usuario

            tag: consulta del usuario
            _type: tipo de la consulta
        """

        result = dict()
        for md_add in self.music_data_list:
            try:
                music_node = get_node_instance(md_add, 'MUSIC_DATA')
                song = music_node.get_music(tag, _type)
                if song is not None and song != []:
                    for s in song:
                        if s in result.keys():
                            result[s].append(md_add)  
                        else:
                            result[s] = [md_add]
            except:
                continue
        return result


    def play_song(self, md_add, music_name, duration=0):
        """
        Busca la cancion en el music_data y la reproduce.
        
        Ordena crear una replica de la misma en los demas music_data que no la contengan

        md_add: La direccion de music_data que se va leer la cancion
        music_name: El nombre de la cancion 
        duration: A partir de que instante se va a empezar a reproducir.
        
        """
        for md in md_add:
            try: 
                
                music_node = get_node_instance(md, 'MUSIC_DATA')

                port, duration = music_node.send_music_data(music_name, duration)

                server_socket = socket.socket()
                server_socket.bind((self.address.split(':')[0], 0))

                t2 = threading.Thread(target=self._recv_song_frames, args=([md, port, server_socket, music_node, music_name]))
                t3 = threading.Thread(target=music_node.replicate_song, args=([music_name]))

                t2.start()
                t3.start()

                return server_socket.getsockname()[1], int(duration)
            except:
                continue
        
        raise Exception("ERROR: Can't connect with any music data")


    def _recv_song_frames(self, md_add, port, server_socket, music_node, music_name):
        """
            Recibe y envia los frames de la cancion

            md_add: direccion del music data
            port: puerto de escucha del music data
            server_socket: server socket del request por donde se envia la cancion al usuario
            music_node: nodo del music data
            music_name: nombre de la cancion
        """
        
        host_ip, _ = md_add.split(':')

        CHUNK = 1024
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        socket_address = (host_ip, port)
        client_socket.connect(socket_address) 

        server_socket.listen(5)
        
        data = b""
        payload_size = struct.calcsize("Q")
        c,_ = server_socket.accept()
        current_duration = 0 
        while True:
            try:
                try:
                    music_node.ping()
                except:
                    temp_music_node = None
                    for md in self.music_data_list:
                        try:
                            temp_music_node = get_node_instance(md, 'MUSIC_DATA')
                            if temp_music_node.contain_song(music_name):
                                _port = temp_music_node.send_music_data(music_name, int(current_duration))
                                client_socket.close()
                                client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                                client_socket.connect((md.split(':')[0], _port))
                                music_node = temp_music_node
                                data = b""
                                payload_size = struct.calcsize("Q")
                                time.sleep(2)
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
                if frame == b'':
                    server_socket.close()
                    client_socket.close()
                    break

                if c:
                    a = pickle.dumps(frame)
                    message = struct.pack("Q",len(a))+a
                    c.sendall(message)
            except:
                server_socket.close()
                client_socket.close()
                break
        server_socket.close()
        client_socket.close()

    
    def join_music_data(self, md_add):
        """
            Agrega un music data a la lista de music data

            md_add: direccion del music data
        """
        music_node = get_node_instance(self.music_data_address, 'MUSIC_DATA')
        music_node.join(md_add)
    
    def update_music_data_list(self):
        """
            Mantiene actualizados el music data al que esta conectado
        """

        while True:
            node = get_node_instance(self.music_data_address, 'MUSIC_DATA')
            if node is not None:
                try:
                    self.music_data_list = node.music_data_list
                except:
                    pass
            else:
                for md in self.music_data_list[1:]:
                    node = get_node_instance(md, 'MUSIC_DATA')
                    if node is not None:
                        self.music_data_address = md
                        self.music_data_list = node.music_data_list
                        break
            time.sleep(1)  
    
    def update_requests_list(self):    
        """
            Actualiza la lista de request eliminando todos los nodos que se hayan desconectado
        """
        while True:
            list = self._requests_list
            for addr in list:
                node = get_node_instance(addr, 'REQUEST')
                if node is None:
                    self._requests_list.remove(addr)
            time.sleep(1) 

    def check_if_exist(self, path):
        """ 
        Verifica si el nodo el music_data esta conectado y contiene la cancion que se quiere
        
        path: ruta de la cancion
        """
        music_data_node = get_node_instance(self.music_data_address, 'MUSIC_DATA')
        
        if music_data_node is None:
            print(f"ERROR: Missing connection to server {self.music_data_address}")
            return False
        
        if music_data_node.contain_song(path):
            print(f"ERROR: The song {path} is already exist")
            return True

        return False

    def put_song_in_music_data(self, path, client_conn):
        """
            Recibe la nueva cancion que el cliente quiere subir y la guarda en el music_data correspondiente

            path: ruta de la cancion
            client_conn: ip y puerto por el cual el request recibe la cancion
        """
        request_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        request_socket.connect(client_conn)        

        music_data_node = get_node_instance(self.music_data_address, 'MUSIC_DATA')
        
        if music_data_node is None:
            print(f"ERROR: Missing connection to server {self.music_data_address}")
            return

        host_ip, _ = self.music_data_address.split(':')
        CHUNK_SIZE = 5 * 1024

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host_ip, 0))
            
            time.sleep(1)
            replicate_recv_thread = threading.Thread(target=music_data_node.put_upload_song, args=([path, (host_ip, s.getsockname()[1])]))
            replicate_recv_thread.start()

            s.listen(1)
            conn, _ = s.accept()

            if conn:
                data = request_socket.recv(CHUNK_SIZE)

                while data:
                    conn.sendall(data)
                    data = request_socket.recv(CHUNK_SIZE)
                    if data == b'':
                        print('FINISH RECV UPLOAD SONG TO RESEND TO MUSIC DATA')
                        request_socket.close()
                        break

            print(f'REQUEST FINISH SEND UPLOAD SONG TO MUSIC DATA {self.music_data_address}')
            s.close()
    

    def print_node_info(self):
        """
        Imprime en la consola la informacion del nodo
        """
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
        
        print_thread = threading.Thread(target = node.print_node_info)
        print_thread.start()
    
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

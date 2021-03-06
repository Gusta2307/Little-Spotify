import Pyro4, socket, pyaudio
import os, sys, time, threading, struct, pickle
from pynput import keyboard as kb
from rich.progress import Progress
from utils import (
    get_node_instance,
    TAG,
    view_console,
    py_error_handler
)


@Pyro4.expose
class ClientNode:
    def __init__(self, address, r_address) -> None:
        self.address = address
        self.request_node_address = r_address
        self._request_node_list = []
        self.is_paused = False

    def run(self):
        """
            Run the client node.
        """

        r_node = None
        try:
            r_node = get_node_instance(self.request_node_address, 'REQUEST')
            if r_node.ping():
                self._request_node_list = r_node.requests_list
                print(f"Connected to {self.request_node_address}")
        except:
            print(f"Can't connect to server {self.request_node_address}")
            return

        while True:
            view_console("Welcome! What do you want to do?",
                         ['Play music', 'Upload music'])

            try:
                options = int(input())
                if options == 0:
                    view_console("Select search form:", [
                        'Name', 'Genre', 'Artist', 'See all'])
                    tag = int(input())
                    song_name = ''
                    if tag != 3:
                        view_console(f"Enter {TAG[tag]}: ")
                        song_name = input()
                    view_console("Loading...")
                    responses_song = r_node.request_response(song_name, tag)
                    if responses_song:
                        view_console("Enter song index: ",
                                    list(responses_song.keys()))
                        index = int(input())
                        self.recv_music(responses_song[list(responses_song.keys())[
                                        index]], list(responses_song.keys())[index])
                elif options == 1:
                    view_console("Enter path of song: ")
                    path_song = input()
                    self.upload_song(path_song)
            except:
                print("Somenthig went wrong! :/")

    def recv_music(self, md_add, music_name):
        """
            Recibe la musica del request

            md_add: lista de direcciones donde esta almacenada la cancion
            music_name: nombre de la cancion
        """

        # try:
        r_node = get_node_instance(self.request_node_address, 'REQUEST')
        if r_node is None:
            print(
                f"ERROR: Missing connection to server {self.request_node_address}")
            return

        port, duration = r_node.play_song(md_add, music_name)

        view_console("Loading...")
        self.is_paused = False
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

        client_socket.connect(socket_address)
        data = b""
        payload_size = struct.calcsize("Q")
        current_duration = 0
        time.sleep(3)
        view_console(music_name)
        with Progress() as progress:
            song_progress = progress.add_task(
                "[green]Playing...", total=duration)
            is_done = False
            escuchador = kb.Listener(on_press=self.stopped)
            escuchador.start()
            while True:
                while not self.is_paused:
                    try:
                        try:
                            r_node.ping()
                        except:
                            progress.update(song_progress, advance=0,
                                    description="[yellow]Reconnecting...")
                            if self.connect_to_server():
                                client_socket.close()
                                client_socket = socket.socket(
                                    socket.AF_INET, socket.SOCK_STREAM)
                                r_node = get_node_instance(
                                    self.request_node_address, 'REQUEST')
                                port, _ = r_node.play_song(
                                    md_add, music_name, current_duration)
                                client_socket.connect(
                                    (self.request_node_address.split(':')[0], port))
                                data = b""
                            else:
                                print("ERROR: Missing connection with server.")
                                return

                        progress.update(song_progress, advance=0,
                                        description="[green]Playing...")
                        while len(data) < payload_size:
                            packet = client_socket.recv(4*1024)  
                            current_duration += CHUNK/44100
                            if not packet:
                                client_socket.close()
                                escuchador.stop()
                                return
                            data += packet

                        _packed_msg_size = data[:payload_size]
                        msg_size = struct.unpack("Q", _packed_msg_size)[0]
                        data = data[payload_size:]

                        while len(data) < msg_size:
                            _data = client_socket.recv(4*1024)
                            data += _data
                            current_duration += CHUNK/44100
                            if _data == b'':
                                client_socket.close()
                                escuchador.stop()
                                return

                        frame_data = data[:msg_size]
                        data = data[msg_size:]
                        if frame_data == b'':
                            stream.close()
                            client_socket.close()
                            escuchador.stop()
                            return
                        frame = pickle.loads(frame_data)
                        stream.write(frame)

                        progress.update(song_progress, advance=10,
                                        description="[green]Playing...")

                        if not len(data) < msg_size:
                            is_done = True
                            break

                    except Exception as e:
                        is_done = True
                        stream.close()
                        client_socket.close()
                        escuchador.stop()
                        print(f"Break {e}")
                        break
                progress.update(song_progress, advance=0,
                                description="[red]Stopping...")
                if is_done:
                    break
                time.sleep(2)

            client_socket.close()
            escuchador.stop()


    def upload_song(self, path):
        """
            Sube una cancion al sistema

            path: direccion de la cancion
        """

        if os.path.exists(path):
            self.send_upload_song(path)
        else:
            print("ERROR: Invalid path")


    def stopped(self, tecla):
        """
            Pausa la cancion utilizando la tecla del espacio
        """
        if str(tecla) == 'Key.space':
            self.is_paused = not self.is_paused

    def send_upload_song(self, path):
        """
            Envia la cancion al request

            path: direccion de la cancion
        """

        try:
            r_node = get_node_instance(self.request_node_address, 'REQUEST')
            if r_node is None:
                print(
                    f"ERROR: Missing connection to server {self.request_node_address}")
                return

            host_ip, _ = self.address.split(':')
            CHUNK_SIZE = 5 * 1024
            size = os.path.getsize(path)
            view_console(str(path).split('/')[-1])
            with Progress() as progress:
                song_progress = progress.add_task(
                    "[green]Preparing...", total=size)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind((host_ip, 0))
                    time.sleep(1)
                    if not r_node.check_if_exist(path.split('/')[-1]):
                        replicate_recv_thread = threading.Thread(target=r_node.put_song_in_music_data, args=(
                            [path.split('/')[-1], (host_ip, s.getsockname()[1])]))
                        replicate_recv_thread.start()
                    else:
                        progress.update(song_progress, advance=0, description="[red]ERROR: Song already exists...")
                        time.sleep(3)
                        return

                    s.listen(1)
                    conn, _ = s.accept()
                    with conn:
                        with open(path, 'rb') as f:
                            
                            data = f.read(CHUNK_SIZE)
                            while data:
                                progress.update(song_progress, advance=CHUNK_SIZE, description="[green]Uploading...")
                                conn.sendall(data)
                                data = f.read(CHUNK_SIZE)
                                if data == b'':
                                    conn.close()
                                    f.close()
                                    progress.update(song_progress, advance=CHUNK_SIZE, description="[green]Finish...")
                                    time.sleep(2)
                                    break
                    s.close()
        except:
            view_console("ERROR: Uploading song", style="red")
            progress.update(song_progress, advance=0, description="[red]Error...")
            time.sleep(3)


    def connect_to_server(self):
        """
            Conecta al cliente con el request
        """

        for r_node in self._request_node_list:
            print(f"Trying connect to {r_node}")
            try:
                node = get_node_instance(r_node, 'REQUEST')
                if node.ping():
                    print(f"Connected to {r_node}")
                    self.request_node_address = r_node
                    self._request_node_list = node.requests_list
                    return True
            except Exception as e:
                print(f"ERROR: Can't connect to {r_node}. {e}")
        print("ERROR: Can't connect to any requests node.")
        return False

    def check_connection(self):
        """
            Comprueba si el cliente esta conectado con el request
        """

        while self.is_running:
            try:
                node = get_node_instance(self.request_node_address, 'REQUEST')
                node.ping()
            except:
                print(
                    f"Error: Missing connection to server {self.request_node_address}")
                self.connect_to_server(self.request_node_address)
            time.sleep(1)


def main(address, r_address):
    node = ClientNode(address, r_address)
    node.run()
    check_connetion_thread = threading.Thread(target=node.check_connection, name="check_connection")
    check_connetion_thread.start()


# ? <MY_ADD> <R_ADD>

if __name__ == '__main__':
    if len(sys.argv) == 3:
        # Ignore warnings
        from ctypes import *
        ERROR_HANDLER_FUNC = CFUNCTYPE(
            None, c_char_p, c_int, c_char_p, c_int, c_char_p)
        c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
        asound = cdll.LoadLibrary('libasound.so')
        # Set error handler
        asound.snd_lib_error_set_handler(c_error_handler)
        
        main(sys.argv[1], sys.argv[2])
    else:
        print('Error: Missing arguments')

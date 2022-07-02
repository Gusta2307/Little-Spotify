import Pyro4, os
from pydub import AudioSegment
from rich import console
from cfonts import render


# Este tag se utiliza para trabajar de forma más cómoda con las posibles opciones de filtrado para las canciones que tiene el cliente
TAG = {
    0: "title",
    1: "genre",
    2: "artist",
    3: "see_all"
}


def get_node_instance(id, node_type):
    """
        Obtiene la intancia de un nodo en la red

        id: ip y puerto del nodo
        node_type: tipo de nodo que se quiere obtener
    """
    return get_proxy(f'{node_type}{id}')

def get_proxy(id):
    """
        Dado un identificador de un nodo, obtiene la instancia de ese nodo

        id: identificar del nodo en la red
    """
    with Pyro4.Proxy(f'PYRONAME:{id}') as p:
        try:
            p._pyroBind()
            return p
        except:
            return None


def init_client():
    """
        Printea el cartel de LITTLE SPOTIFY
    """
    output1 = render('LITTLE SPOTIFY', colors=['green', 'cyan'], align='center', font='block')
    print(output1)


def get_duration(file):
    """
        Devuelve la duracion de una cancion en segundos

        file: ruta del archivo
    """
    return int(AudioSegment.from_file(file).duration_seconds)


def view_console(msg, list=None, style="green"):
    """
        Dado un mensaje printea las vistas del cliente

        msg: mensaje a printear
        list: lista mensajes a mostrar
        style: color del mensaje
    """
    os.system('clear')
    init_client()
    _console = console.Console()
    _console.print(f'{msg}', style=style)

    if list is not None:
        for i in range(len(list)):
            _console.print(f'{i}. {list[i]}', style=style)


def py_error_handler(filename, line, function, err, fmt):
    return

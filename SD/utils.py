import Pyro4
import hashlib
import rich
from pydub import AudioSegment
from rich import console
from cfonts import render

TAG = {
    0: "title",
    1: "genre",
    2: "artist",
    3: "see_all"
}


def get_chord_node_instance(id):
    return get_proxy(f'CHORD{id}')


def get_music_data_instance(id):
    return get_proxy(f'MUSIC_DATA{id}')


def get_request_node_instance(id):
    return get_proxy(f'REQUEST{id}')


def get_client_node_instance(id):
    return get_proxy(f'CLIENT{id}')


def get_proxy(id):
    with Pyro4.Proxy(f'PYRONAME:{id}') as p:
        try:
            p._pyroBind()
            return p
        except:
            return None


def hashing(bits, string):
    try:
        hash = hashlib.sha256(string.encode('utf-8', 'ignore')).hexdigest()
        hash = int(hash, 16) % pow(2, bits)
        return hash
    except:
        return None


def init_client():
    output1 = render('LITTLE SPOTIFY', colors=['green', 'cyan'], align='center', font='block')
    print(output1)

def get_duration(file):
    return int(AudioSegment.from_file(file).duration_seconds)

import os
def view_console(msg, list=None, style="green"):
    # rich.console.Console().
    # os.system('clear')
    init_client()
    _console = console.Console()
    _console.print(f'{msg}', style=style)

    if list is not None:
        for i in range(len(list)):
            _console.print(f'{i}. {list[i]}', style=style)

def py_error_handler(filename, line, function, err, fmt):
    return


abc = 'páááp'
print(abc)

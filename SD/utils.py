import Pyro4
import hashlib


def get_chord_node_instance(id):
    return get_proxy(f'CHORD{id}')


def get_music_data_instance(id):
    return get_proxy(f'MUSIC_DATA{id}')


def get_request_node_instance(id):
    return get_proxy(f'REQUEST{id}')


def get_client_node_instance(id):
    return get_proxy(f'CLIENT{id}')


def get_proxy(id):
    # Pyro4.Proxy(f'PYRONAME:{id}')
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

# convert mp3 to wav
# from pydub import AudioSegment

# s = AudioSegment.from_mp3("Glass Animals - Heat Waves.mp3")
# s.export("Glass Animals - Heat Waves.wav", format="wav")

# import wave
# wf = wave.open('./MD1/Glass Animals - Heat Waves.wav', 'rb')
# print(wf.getnframes())

import os, re, stagger
def find_song_by_genre(genre, path):
    print("GENRE")
    _songs = []
    for mn in os.listdir(path):
        print(os.path.join(path, mn))
        mp3 = stagger.read_tag(os.path.join(path, mn))
        print(mp3.title, mp3.genre)
        if re.search(genre, mp3.genre):
            _songs.append(mn)
    return _songs

# find_song_by_genre('pop', '/home/gustavo/Desktop/Little-Spotify/SD/MD1')
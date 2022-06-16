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

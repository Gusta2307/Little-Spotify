import os
import csv
import librosa
import numpy as np
from pydub import  AudioSegment
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler



def create_data(path: str, name: str):
    """
    Crea el dataset
    """
    name += '.csv'
    genres = 'Hip-Hop_-_Rap Pop R&B_-_Soul Rock Country Blues KPOP'.split()
    header = 'filename chroma_freq rms spectral_centroid spectral_bandwidth rolloff zero_crossing_rate dbfs'
    genres = genres[:5]

    for i in range(1, 21):
        header += f' mfcc{i}'

    header += ' genre'
    header = header.split()

    file_csv = open(name, 'w', newline='')

    with file_csv:
        writer = csv.writer(file_csv)
        writer.writerow(header)

    for g in genres:
        count = 0
        dirs = os.path.join(path, g)

        for filename in os.listdir(dirs):
            if count == 100:
                break

            count += 1
            songname = os.path.join(path, g, filename)
            y, sr = librosa.load(songname, mono=True, duration=90)
            chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
            spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)
            spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
            rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            zcr = librosa.feature.zero_crossing_rate(y)
            mfcc = librosa.feature.mfcc(y=y, sr=sr)
            S, _ = librosa.magphase(librosa.stft(y))
            rms = librosa.feature.rms(S=S)

            audio = AudioSegment.from_file(songname, duration=90)
            dbfs = audio.dBFS
            to_append = f'{filename} {np.mean(chroma_stft)} {np.mean(rms)} {np.mean(spec_cent)} {np.mean(spec_bw)} {np.mean(rolloff)} {np.mean(zcr)} {np.mean(dbfs)}'

            for e in mfcc:
                to_append += f' {np.mean(e)}'

            to_append += f' {g}'
            file_csv = open(name, 'a', newline='')

            with file_csv:
                writer = csv.writer(file_csv)
                writer.writerow(to_append.split())


def get_X_y(data):
    """
    Separa las caracteristicas del target
    """
    FEATURES = [        
        'chroma_freq',
        'rms',
        'spectral_centroid',
        'spectral_bandwidth',
        'rolloff',
        'zero_crossing_rate',
        'mfcc1',
        'mfcc2',
        'mfcc3',
        'mfcc4',
        'mfcc5',
        'mfcc6',
        'mfcc7',
        'mfcc8',
        'mfcc9',
        'mfcc10',
        'mfcc11',
        'mfcc12',
        'mfcc13',
        'mfcc14',
        'mfcc15',
        'mfcc16',
        'mfcc17',
        'mfcc18',
        'mfcc19',
        'mfcc20',
        'dbfs',
    ]


    TARGET = 'genre'

    X = data[FEATURES]
    y = data[TARGET]
    return X, y


def scaler_data(X):
    """
    Escala los datos
    """
    scaler = StandardScaler()
    return scaler.fit_transform(X)


def encode_names(y):
    """
    Codifica los targets 
    """
    lb = LabelEncoder()
    y = lb.fit_transform(y)
    return y


def encode_features(data, features):
    """
    Codifica los features
    """
    for feat in features:
        le = LabelEncoder()
        data[feat] = le.fit_transform(data[feat])



import copy
import librosa
import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedShuffleSplit
from process_datas import (
    get_X_y,
    scaler_data,
    encode_names
)



class Genre_Clasf:
    def __init__(self) -> None:
        self.model = None
        self.genre_dict = None
        self.__initialize()
    
    def __initialize(self):
        data = pd.read_csv('../ML/datasets/data-15 genres-wav.csv')
        
        X, y, groups = get_X_y(data)
        X = scaler_data(X)
        y, self.genre_dict = encode_names(y)
        
        st = StratifiedShuffleSplit(n_splits=3)
        splits = st.split(X, y, groups)
        model = SVC(kernel='rbf', decision_function_shape='ovo', class_weight='balanced')
        
        best_model = None
        best_value = 0

        X = pd.DataFrame(X)
        y = pd.DataFrame(y)
        for train_idx, val_idx in splits:
            X_tr = X.loc[train_idx]
            y_tr = y.loc[train_idx]
            
            X_val = X.loc[val_idx]
            y_val = y.loc[val_idx]

            y_tr = np.ravel(y_tr)

            model.fit(X_tr, y_tr)
            score = model.score(X_val, y_val)

            if best_value < score:
                best_value = score
                best_model = copy.deepcopy(model)
        
        self.model = best_model
    

    def predict(self, X):
        p = self.model.predict(X)
        return self.genre_dict[p[0]]


def extract_carcteristics(path):
    y, sr = librosa.load(path, mono=True)
    chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    S, _ = librosa.magphase(librosa.stft(y))
    rms = librosa.feature.rms(S=S)

    _mfcc = []
    for e in mfcc:
        _mfcc.append(np.mean(e))

    _mfcc.pop(0)
    _mfcc.pop(1)
    _mfcc.pop(7)
    _mfcc.pop(9)
    

    X = [np.mean(chroma_stft), np.mean(rms), np.mean(zcr)] + _mfcc

    return [X]

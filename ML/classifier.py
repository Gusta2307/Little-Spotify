import numpy as np
from sklearn.svm import SVC
from sklearn import metrics
from sklearn.cluster import KMeans
from sklearn.naive_bayes import GaussianNB
from sklearn_extra.cluster import KMedoids
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from tensorflow.keras import Sequential, layers
from sklearn.model_selection import StratifiedShuffleSplit

    

def KNN(X, y, groups, n_splits=3, n_neighbors=5, weights='distance'):
    values = []
    best_value = 0
    best_partition = None
    
    st = StratifiedShuffleSplit(n_splits=n_splits)
    splits = st.split(X, y, groups)
    model = KNeighborsClassifier(n_neighbors=n_neighbors, weights=weights)
    
    for train_idx, val_idx in splits:
        X_tr = X.loc[train_idx]
        y_tr = y.loc[train_idx]

        X_val = X.loc[val_idx]
        y_val = y.loc[val_idx]
        
        model.fit(X_tr, y_tr)
        score = model.score(X_val, y_val)
        values.append(score)
        
        if best_value < score:
            best_value = score
            best_partition = (X_tr, y_tr)

    return best_value, best_partition, np.mean(values)


def Naive_Bayer(X, y, groups, n_splits=3):    
    values = []
    best_value = 0
    best_partition = None

    st = StratifiedShuffleSplit(n_splits=n_splits)
    splits = st.split(X, y, groups)
    model = GaussianNB()
    
    for train_idx, val_idx in splits:
        X_tr = X.loc[train_idx]
        y_tr = y.loc[train_idx]
        
        X_val = X.loc[val_idx]
        y_val = y.loc[val_idx]

        model.fit(X_tr, y_tr)
        score = model.score(X_val, y_val)
        values.append(score)

        if best_value < score:
            best_value = score
            best_partition = (X_tr, y_tr)

    
    return best_value, best_partition, np.mean(values)


def ID3(X, y, groups, n_splits=3, clf=DecisionTreeClassifier):
    values = []
    best_value = 0
    best_partition = None

    st = StratifiedShuffleSplit(n_splits=n_splits)
    splits = st.split(X, y, groups)
    model = clf(criterion='entropy')
    
    for train_idx, val_idx in splits:
        X_tr = X.loc[train_idx]
        y_tr = y.loc[train_idx]
        
        X_val = X.loc[val_idx]
        y_val = y.loc[val_idx]

        model.fit(X_tr, y_tr)
        score = model.score(X_val, y_val)
        values.append(score)

        if best_value < score:
            best_value = score
            best_partition = (X_tr, y_tr)

    return best_value, best_partition, np.mean(values)


def SVM(X, y, groups, n_splits=3, kernel='rbf', decision='ovo', weight='balanced'):
    values = []
    best_value = 0
    best_partition = None

    st = StratifiedShuffleSplit(n_splits=n_splits)
    splits = st.split(X, y, groups)
    model = SVC(kernel=kernel, decision_function_shape=decision, class_weight=weight)
    
    for train_idx, val_idx in splits:
        X_tr = X.loc[train_idx]
        y_tr = y.loc[train_idx]
        
        X_val = X.loc[val_idx]
        y_val = y.loc[val_idx]

        model.fit(X_tr, y_tr)
        score = model.score(X_val, y_val)
        values.append(score)

        if best_value < score:
            best_value = score
            best_partition = (X_tr, y_tr)

    return best_value, best_partition, np.mean(values)


class Keras:
    def __init__(self) -> None:
        self.history = None


    def evaluate(self, X, y, groups, n_splits=3):
        values = []
        best_value = 0
        best_partition = None
        best_curve = None

        st = StratifiedShuffleSplit(n_splits=n_splits)
        splits = st.split(X, y, groups)

        for train_idx, val_idx in splits:
            X_tr = X.loc[train_idx]
            y_tr = y.loc[train_idx]

            X_val = X.loc[val_idx]
            y_val = y.loc[val_idx]
            
            accuray, _ = self.classification(X_tr, X_val, y_tr, y_val)
            values.append(accuray)

            if best_value < accuray:
                best_value = accuray
                best_partition = (X_tr, y_tr)
                best_curve = self.history
        
        return best_value, best_partition, np.mean(values), best_curve

    
    def classification(self, X_train, X_test, y_train , y_test, epochs=20, validation=0.2, rate=0.5, batch=128):
        model = Sequential()
        model.add(layers.Dense(1600, activation='relu', input_shape=(X_train.shape[1],)))
        model.add(layers.Dropout(rate=rate))
        model.add(layers.Dense(800, activation='relu'))
        model.add(layers.Dropout(rate=rate))
        model.add(layers.Dense(400, activation='relu'))
        model.add(layers.Dropout(rate=rate))
        model.add(layers.Dense(15, activation='softmax'))
        model.summary()
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',
                      metrics=['accuracy'])
                
        self.history = model.fit(X_train, y_train, validation_split=validation, epochs=epochs, batch_size=batch, verbose=0)
        p = model.predict(X_test)
        print("Predict: ", p)
        loss, accuracy = model.evaluate(X_test, y_test)
        return accuracy, loss


class KMeansClustering:
    def __init__(self, n_clusters=15) -> None:
        self.n_clusters = n_clusters
        self.clusters = {}  # dict <key=cluster, value=song>


    def kmeans(self, X, n_init=3, init='random', tol=1e-4, random_state=170, verbose=False):
        model = KMeans(n_clusters=self.n_clusters,
                        n_init=n_init,
                        init=init,
                        tol=tol, 
                        random_state=random_state,
                        verbose=verbose).fit(X)

        self.y_pred = model.predict(X)
        self.build_clusters(model.labels_)


    def evaluate(self, X, y):
        homogeneity = metrics.homogeneity_score(y, self.y_pred)
        completeness = metrics.completeness_score(y, self.y_pred)
        s_mean = metrics.silhouette_score(X, self.y_pred)
        return homogeneity, completeness, s_mean


    def build_clusters(self, list_clusters):
        for i in range(self.n_clusters):
            self.clusters[i + 1] = []

        for i in range(len(list_clusters)):
            cluster = list_clusters[i] + 1
            self.clusters[cluster].append(i + 1)


class KMedoidsClustering:
    def __init__(self, n_clusters=15) -> None:
        self.clusters = {}
        self.n_clusters = n_clusters


    def kmedoids(self, X, init='random', random_state=127, verbose=False):
        kmedoids = KMedoids(self.n_clusters, init=init, random_state=random_state).fit(X)
        self.y_pred = kmedoids.predict(X)
        self.build_clusters(kmedoids.labels_)


    def evaluate(self, X, y):
        homogeneity = metrics.homogeneity_score(y, self.y_pred)
        completeness = metrics.completeness_score(y, self.y_pred)
        s_mean = metrics.silhouette_score(X, self.y_pred)
        return homogeneity, completeness, s_mean


    def build_clusters(self, list_clusters):
        for i in range(self.n_clusters):
            self.clusters[i + 1] = []

        for i in range(len(list_clusters)):
            cluster = list_clusters[i] + 1
            self.clusters[cluster].append(i + 1)

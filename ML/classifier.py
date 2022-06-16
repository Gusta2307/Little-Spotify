# from tensorflow.keras import Sequential, layers
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier



def knn(X_train, X_test, y_train , y_test):
    """
    Algoritmo de KNN
    """
    model = KNeighborsClassifier(n_neighbors=5, weights='distance')
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    return score


def naive_bayes(X_train, X_test, y_train , y_test):
    """
    Algoritmo Naive Bayes 
    """
    model = GaussianNB()
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    return score


def id3(X_train, X_test, y_train , y_test):
    """
    Algoritmo de Árboles de decisión
    """
    model = DecisionTreeClassifier()
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    return score


def svm(X_train, X_test, y_train , y_test):
    """"
    Algoritmo de Support Vector Classification
    """
    model = SVC(kernel='rbf', decision_function_shape='ovo', class_weight='balanced')
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    return score



class Keras:
    """
    Algotitmo de Keras
    """
    def __init__(self) -> None:
        self.model = Sequential()

    
    def evaluate(self, X_train, X_test, y_train , y_test, epochs=20):
        """
        Evaluación del modelo 
        """
        self.model.add(layers.Dense(512, activation='relu', input_shape=(X_train.shape[1],)))
        self.model.add(layers.Dense(256, activation='relu'))
        self.model.add(layers.Dense(128, activation='relu'))
        self.model.add(layers.Dense(5, activation='softmax'))
        self.model.summary()
        self.model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',
                           metrics=['accuracy'])
        
        self.model.fit(X_train, y_train, validation_split=0.1, epochs=epochs, batch_size=128)
        test_loss , test_acc = self.model.evaluate(X_test, y_test)
        return test_acc, test_loss


    def prediction(self, X_test, y_test):
        pred = self.model.predict(X_test)
        report = classification_report(y_test, pred)
        cf = confusion_matrix(y_test, pred)
        return report, cf

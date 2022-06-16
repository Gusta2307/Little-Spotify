import pandas as pd
from colorama import Fore, Style
from process_datas import  get_X_y, scaler_data, encode_names, create_data
from classifier import naive_bayes, id3, svm, Keras, knn
from sklearn.model_selection import train_test_split



if __name__ == '__main__':
    # path = '/home/gustavo/Downloads/archive/Data/genres_original'
    # create_data(path, 'dataset GTZA')
 
    data = pd.read_csv('GTZAN.csv')    
    X, y = get_X_y(data)
    X = scaler_data(X)
    y = encode_names(y)

    # keras = Keras()
    X_train, X_test, y_train , y_test = train_test_split(X, y, train_size=0.8)

    print("Resultados:")
    # test_acc, test_loss = keras.evaluate(X_train, X_test, y_train , y_test)
    # print(f"{Fore.GREEN} Keras: accuracy={test_acc} loss={test_loss} {Style.RESET_ALL} epoch={20}")
    print(f"{Fore.GREEN} Naive Bayer: {naive_bayes(X_train, X_test, y_train , y_test)} {Style.RESET_ALL}")
    print(f"{Fore.GREEN} ID3: {id3(X_train, X_test, y_train , y_test)} {Style.RESET_ALL}")
    print(f"{Fore.GREEN} KNN: {knn(X_train, X_test, y_train , y_test)} {Style.RESET_ALL}")
    print(f"{Fore.GREEN} SVM: {svm(X_train, X_test, y_train , y_test)} {Style.RESET_ALL}")
    print("")
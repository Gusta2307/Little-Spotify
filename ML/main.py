import pandas as pd
from colorama import Fore, Style
from classifier import Naive_Bayer, ID3, KNN, SVM, Keras
from process_datas import  create_dataset, get_X_y, scaler_data, encode_names



if __name__ == '__main__':
    # path = input()
    # create_data(path, 'dataset')
 
    data = pd.read_csv('dataset-genres15.csv')
    
    X, y, groups = get_X_y(data)
    X = scaler_data(X)
    y = encode_names(y)

    Xdf = pd.DataFrame(X)
    ydf = pd.DataFrame(y)
    
    keras = Keras()
    nb_score, nb_partition, nb_mean = Naive_Bayer(Xdf, ydf, groups)
    id3_score, id3_partition, id3_mean = ID3(Xdf, ydf, groups)
    knn_score, knn_partition, knn_mean = KNN(Xdf, ydf, groups)
    svm_score, svm_partition, svm_mean = SVM(Xdf, ydf, groups)
    keras_score, keras_partition, keras_mean, history = keras.evaluate(Xdf, ydf, groups)

    print("Resultados de los modelos")
    print(f"{Fore.GREEN} Naive Bayer: best_score={nb_score} mean={nb_mean} {Style.RESET_ALL}")
    print(f"{Fore.GREEN} ID3: best_score={id3_score} mean={id3_mean} {Style.RESET_ALL}")
    print(f"{Fore.GREEN} KNN: best_score={knn_score} mean={knn_mean} {Style.RESET_ALL}")
    print(f"{Fore.GREEN} SVM: best_score={svm_score} mean={svm_mean} {Style.RESET_ALL}")
    print(f"{Fore.GREEN} Keras: best_score={keras_score} mean={keras_mean} {Style.RESET_ALL}")
    print("")
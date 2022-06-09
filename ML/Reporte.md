# Reporte del Proyecto

## Primera Idea : ID3 y Naive Bayes
La primera idea que tuvimos para darle solución al problema fue usar Naive Bayes o Árboles de decisión con las extracción de las siguientes caracteristicas en solo los primeros 30 segundos de las canciones en formato mp3: 

- **Chroma Feature**: Es una poderosa herramienta para analizar características musicales cuyos tonos se pueden categorizar significativamente y cuya afinación se aproxima a la escala de temperamento igual. 
- **Spectral Bandwidth**: Calcule el ancho de banda espectral de orden p.
- **RMS**: Calcula root-mean-square (RMS) para cada frame, ya sea de las muestras de audio o de un espectrograma.
- **Spectral Centroid**: El centroide espectral indica dónde se encuentra el "centroide" del sonido y se calcula de 
acuerdo con el promedio ponderado de la frecuencia del sonido
- **Rolloff espectral**: La derivación espectral (Spectral Rolloff) es una medida de la forma de la señal, que representa 
la frecuencia en un porcentaje específico de la energía espectral (como el 85%).
- **Zero crossing** rate (Taza de Cruce Cero): La velocidad de cruce por cero es la velocidad a la que cambia un signo de señal, es decir, el número de veces que una señal de voz cambia de positivo a negativo o de negativo a positivo en cada cuadro.
- **Mel-Frequency Cepstral Coefficients (MFCCs)**:  El coeficiente cepstral de frecuencia de mel (MFCC) de una señal es un conjunto generalmente compuesto de 10-20 características, que pueden describir de manera concisa la forma general  de la envoltura del espectro y modelar las características del habla.
- **dbfs**: Significa "decibelios a escala completa". Es una abreviatura utilizada para definir los niveles de amplitud en decibelios en sistemas digitales en base al máximo nivel disponible. Actualmente el término "dBFS" se utiliza con referencia a la definición del estándar AES-17. 

### Efectividad obtenida en promedio

|Algoritmo  |Valor Obtenido|
|-----------|:------------:|
|Naive Bayes|0.356      |
|ID3        |0.347      |


## Refinando las ideas que se tienen hasta el momento

Se decidió comprobar si el intervalo de tiempo que se toma de la canción para la extracción de sus características afecta notablemente la efectividad de los algoritmos, para ello se realizaron varias corridas tomando 90 segundos y toda la canción.

Al mismo tiempo por contenido dado en clases aprendimos que es buena idea escalar los datos para normalizarlos. 

Además luego de realizar una búsqueda nos percatamos que para el trabajo con canciones y especifícamente para la extración de sus características se utiliza con frecuencia el formato .wav pues este no presenta compresión de sonido. Para la conversión de las canciones de formato .mp3 a .wav utilizamos la librería de python `pydub`, específicamente la función `AudioSegment`.

Con todo esto se probó las ideas que se tenían hasta el momento y estos fueron los resultados. 

### Efectividad obtenida en promedio

|Algoritmo  |90 s | Completa|
|-----------|:---:|:-------:|
|Naive Bayes|0.52 | 0.52|
|ID3        |0.55 | 0.58|

Por estos resultados es preferible analizar la canción en su totalidad. 

## Segunda Idea : Keras

Pensamos en utilizar este algoritmo antes de verlo en conferencias por lo que no definimos los parámetros de la forma más correcta para el problema en cuestión, los primeros valores que se utilizaron fueron:

- epoch: 100
- capa inicial: 256
- capa oculta1: 128
- capa oculta2: 64
- capa salida (softmax): 5

El valor de la capa de salida si es correcta pues el dataset contiene solo 5 géneros musicales. 

Los valores de la capa inicial y epoch no son los más adecuados para nuestro problema: 

- Para la capa inicial lo mejor es escoger la potencia de 2 mayor que la cantidad de datos que se tienen, como tenemos un dataset de 492 canciones este valor sería 512.

- Por otro lado al tener un valor para epoch tan elevado, sucede que la red neuronal se aprende el conjunto de datos de memoria, específicamente en nuestro caso era a partir de la etapa 30. 

Durante el entrenamiento, el modelo entrenará solo en el conjunto de entrenamiento y validará evaluando los datos en el conjunto de validación. Por lo que el modelo está aprendiendo las características de los datos en el conjunto de entrenamiento, tomando lo que aprendió de estos datos y luego prediciendo en el conjunto de validación. Durante cada época, se podrá observar no solo los resultados de pérdida y precisión para el conjunto de entrenamiento, sino también para el conjunto de validación. 

Se probó tomando validation_split=0.2 y validation_split=0.1, estos son los resultados:

|Validacion  |Resultado | 
|----------- |:---:|
|0.2|0.75 |
|0.1|0.78 |

En este punto podemos dar por desechada la primera idea pues el porciento de efectividad con el algoritmo de keras es mucho más alto que los alcanzaddo por ID3 y Naive Bayes.  

## Tercera idea: KNN

Se encontró un artículo donde, para darle solución a un problema muy similar al que se presenta, utilizaban KNN por lo que decidimos probar esta vía para comparar los resultados con los que teníamos hasta al momento. 

Se toma `n_neighbors=5`, como igual que la solución de la que se habla anteriormente y `weights='distance'` pues los puntos que esten más cercanos al que se quiere clasificar tendrán mayor influencia sobre el veredicto de a qué género pertenece. Luego por esta vía obtenemos un 0.75 de efectividad. 

## Cuarta idea: SVC

Ya para agotar todas las las vías posibles para resolver el problema se probó SVC con el que se obtuvo un 0.74 de efectividad. 

Se tomó para los parámetros los siguientes valores:

- `decision_function_shape='ovo'` : Para poder usar eel algoritmo de vector de soporte para n clases pues por defecto solo se utiliza para valores binarios.

- `kernel = 'rbf'`: Para especificar el tipo del kernel que utilizará el algoritmo, se utiliza 'rbf' pues los datos no son linealmente separables.

- `class_weight='balanced'`: Este modo utiliza los valores de Y para ajustar automáticamente los pesos inversamente proporcionales a las frecuencias de clase en los datos de entrada como .n_samples / (n_classes * np.bincount(y)).

Luego se obtienen mejores resultados con: Keras, KNN y SVC. Ahora analicemos a más detalle estos resultados.


## Análisis de las curvas de aprendizajes 


## Bibliograf

- [Procesando audio con Python](https://programmerclick.com/article/4979571746/)

- [Clasificar géneros de canciones a partir de datos de audio con Python](https://gusintasusilowati.medium.com/classify-song-genres-from-audio-data-4d5f9982c9e)

- [Conozca la extracción de funciones de audio en Python](https://towardsdatascience.com/get-to-know-audio-feature-extraction-in-python-a499fdaefe42)

- [Clasificación de géneros musicales usando CNN (Convolutional Neural Networks)](https://www.clairvoyant.ai/blog/music-genre-classification-using-cnn)

- [Documentación de sklearn.svm](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html)

- [Cómo seleccionar núcleos de máquinas de vectores de soporte](https://www-kdnuggets-com.translate.goog/2016/06/select-support-vector-machine-kernels.html?_x_tr_sl=en&_x_tr_tl=es&_x_tr_hl=es&_x_tr_pto=sc)

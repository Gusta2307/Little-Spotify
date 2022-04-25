# Little-Spotify

Como su nombre lo indica, la idea del proyecto es implementar una versión a menor escala del conocido Spotify. Este proyecto será en conjunto entre las asignaturas Aprendizaje de Máquinas y Sistemas Distribuidos, por lo que cumplirá con los aspectos requeridos por cada una de las asignaturas que se menciona; próximamente, en una actualización del reporte, se darán más detalles acerca de la parte que le corresponde a Sistemas Distribuidos. 

El sistema contará con las funcionalidades básicas de Spotify tales como buscar una canción en particular y permitir reproducirla. Además, cuando el usuario se registre en el sistema, podrá elegir los géneros musicales de su preferencia, luego con esta información en conjunto con las canciones que escucha el usuario en la plataforma, el sistema le recomendará canciones similares.

Para que el sistema pueda realizar dichas recomendaciones es necesario poder clasificar las canciones según el género musical al cual pertenecen, para ello se utilizará los conocimientos de Aprendizaje de Máquinas. La idea que se tiene es que, dado un conjunto de canciones, obtener de cada una las siguientes características: intensidad, zero crossing rate y tempo e implementar con esta información un árbol de decisión. También estamos pensando la idea de usar Naive Bayes, a este punto aún no hemos pensado tan profundidad como para tener criterio de que sería mejor. 

Para obtener dichas características, las librerías que utilizaremos son librosa y pydub; esta primera para extraer las características de tempo y zcr (zero crossing rate) y la última para la intensidad. 

Luego para evaluar el clasificador utilizaremos un conjunto de canciones, obviamente diferente al que se utilizaría para entrenar. En caso de que el clasificador no obtenga buenos resultados lo modificaríamos hasta obtener un mejor clasificador, tentativamente una modificación sería agregar más características a tener en cuenta.

**Aclaración:**
zero crossing rate, en español, la velocidad de cruce por cero, es la velocidad a la que cambia un signo de señal, es decir, el número de veces que una señal de voz cambia de positivo a negativo o de negativo a positivo en cada cuadro. Esta característica se ha utilizado ampliamente en el campo del reconocimiento de voz y la recuperación de información musical, y generalmente es de mayor valor para sonidos de alto impacto como el metal y el rock.

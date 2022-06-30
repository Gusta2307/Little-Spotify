# Little Spotify

## Funcionalidades del sistema 

Little Spotify permite a cualquier usuario conectarse y tener acceso a una interfaz que cuenta con las funcionalidades de subir, listar, buscar y reproducir música; las búsquedas esta orientadas a los metadatos que contienen las canciones. 

El sistema cuenta con diferentes tipos de nodos donde cada uno tiene un rol o funcionalidad específica, por lo cual es sistema siempre estará en funcionamiento siempre y cuando exista conexion entre al menos un nodo de cada tipo. 

## Tipos de nodos

- **Music Data Node:** Los nodos de este tipo son los encargados de almacenar canciones; además tiene como función realizar una búsqueda entre todas estas, para devolver las que cumplan con las peticiones de filtrado de los clientes de acuerdo a los metadatos de las canciones, dígase, título, género y artista. 
- **Request Node:** Este nodo es el intermediario entre le cliente y los nodos de almacenamiento; por lo cual es el encargado de recibir las peticiones de los clientes y enviarlas a todos los nodos de almacenamiento conectados, estas petiones pueden ser:
    1.  Búsqueda de canciones de acuerdo a los metadatos de las estas. 
    2. Listar todas las canciones que se encuentran en el sistema.
    3. Subir una canción al sistema.
    4. Reproducir una canción.
- **Client Node:** Este es el que contiene todo lo relacionado con la experiencia como usuario del sistema. Posee las funcionalidades de  buscar canciones, reproducir/detener una canción y subir una canción.

## Conectividad y Estabilidadad

El sistema consta con un mecanismo de reconexión automática en el cual al instante de desconectarse un nodo, se busca un nodo del mismo tipo de este que estuviera o no conectado a este, y se conecta con él. 

Además el sistema posee una estructura que permite que al conectarse un nuevo nodo a la red este sea reconocido facilmente por los demas nodos de la misma red, pues cada nodo contiene una lista donde se guarda los nodos que conoce.

Al usuario decidir la reproducción de una canción específica, el nodo de almacenamiento que le da respuesta a esta petición, se encarga de crea una réplica de la misma en todos los nodos de almacenamiento conectados a el, siempre y cuando este no contenga dicha canción.

Existen dos posibles fallas en el sistema por desconexión de nodos, para los cuales el momento más crítico sería si se estuviera reproduciendo una canción en ese instante, veamos como el sistema actúa en cada caso:
1. En caso de que se desconecte un `music_data`, el request corespondiente se reconecta con otro `music_data` que estuviera conectado a este y le realiza el pedido necesario para que continue la reproducción.
2. En caso de que el `request` se desconecte, el cliente de inmediato de conecta a otro request que estuviera conectado a este y nuevamente realiza el pedido necesario para que continue la reproducción.

## Parte de ML

Adicionalmente se cuenta con un clasificador de canciones según su género que se realizó como proyecto de la asignatura de Aprendizaje de Máquinas. Luego cuando un cliente quiera filtrar canciones por su género, las que no contengan el metadato correspondiente se le asigna con la predicción de nuestro clasificador. 
Para ver los detalles de la implementación y las características del clasificador diríjase [aquí]("https://github.com/Gusta2307/Little-Spotify/blob/main/ML/README.md").


## Instrucciones para ejecutar el proyecto

Lo primero que se debe hacer es crear un servidor de Pyro4 para ello es necesario ejecutar la siguiente instrucción:

```
pyro4-ns -n <ip>
```

En caso de que se quiera probar el proyecto localmente la ip sería `127.0.0.1` y en caso contrario, o sea, con varios dispositivos, la ip sería `0.0.0.0`.


Luego de esto, ya estamos listos para agregar nodos a la red. En caso de un `music_data` se realizaría de la siguiente manera:

```
python3 music_data.py <md_ip:md_port> <md2_ip:md2_port> <path>
```

A la hora de crear un nodo de tipo `music_data` podemos, opcionalmente, conectarlo directo a otro nodo de almacenamiento, para ello se utiliza el parámetro `<md2_ip:md2_port>` o simplemente agregarlo a red. 

El parámetro `<path>` es la ruta donde encuentran las canciones que va almacenar el nodo. 

Para crear un nodo de tipo `request` se realizaría de la siguiente manera:


```
python3 request.py <r_ip:r_port> <r2_ip:r2_port> <md_ip:md_port>
```

Con este nodo sucede algo similar al nodo anterior, por lo que es opcional el segundo parámetro.

Es necesario definir a que nodo de almacenamiento se va a conectar, para ello se utiliza `<md_ip:md_port>`. 


Por último, para que un cliente se conecte a la red es necesario utilizar la siguiente línea:

```
python3 client.py <c_ip:c_port> <r_ip:r_port>
```

Al ejecutar esta instrucción, el cliente podrá visualizar la interfaz del sistema destinada para el usuario. 









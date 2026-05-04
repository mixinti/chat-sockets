import socket    
import select    
import sys       

HOST = "127.0.0.1"  
PORT = 5555       

# crear el socket del servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # ipv4 TCP

# SO_REUSEADDR = evita el error "puerto en uso" al reiniciar el servidor rapidamente
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # al nivel del socket, 1=activado

try:
    servidor.bind((HOST, PORT))   # ata el servidor a esa IP y puerto
    servidor.listen()             # empieza a escuchar conexiones entrantes
    print(f"Servidor escuchando en {HOST}:{PORT} ...")
except OSError as e:
    print(f"No se pudo iniciar el servidor: {e}")
    sys.exit()   # si no puede iniciar, no tiene sentido seguir

sockets = [servidor]   # lista con todos los sockets activos, arranca solo con el servidor
nombres = {}           # diccionario socket -> nombre solo los clientes que ya mandaron su nombre
pendientes = []        # lista de clientes conectados que todavia NO mandaron su nombre

def broadcast(mensaje, emisor):
    for s in sockets:                          # recorre todos los sockets activos
        if s != servidor and s != emisor:      # se salta al servidor y al emisor
            try:
                s.send(mensaje.encode())       # encode() convierte texto a bytes
            except:
                desconectar(s)                 # si falla, el cliente probablemente se cayo

def desconectar(s):
    nombre = nombres.get(s, "Anonimo")         # obtiene el nombre si lo tiene, sino pone "Anonimo"
    print(f"{nombre} se desconecto.")
    broadcast(f"{nombre} se fue del chat.", s) # avisa a todos que se fue
    if s in sockets:                           # verifica antes de eliminar para no tirar error
        sockets.remove(s)
    if s in nombres:
        del nombres[s]
    if s in pendientes:                        # tambien lo saca de pendientes si estaba ahi
        pendientes.remove(s)     
    s.close()                                  # cierra la conexion

print("Esperando conexiones...")

try:
    while True:    # bucle infinito, el servidor corre hasta que aprietes Ctrl+C
        try:
            # select monitorea: sockets activos + pendientes (para saber cuando mandan el nombre)
            # los juntamos con + para monitorear ambas listas a la vez
            listos, _, con_error = select.select(sockets + pendientes, [], sockets + pendientes)
        except Exception as e:
            print(f"Error en select: {e}")
            break

        for s in con_error:                    # sockets que tuvieron algun error
            print("Un socket tuvo un error.")
            desconectar(s)

        for s in listos:                       # sockets que tienen algo para leer

            if s == servidor:
                # nuevo cliente golpeando la puerta
                try:
                    cliente, direccion = servidor.accept()   # acepta la conexion
                    pendientes.append(cliente)               # lo pone en espera hasta que mande su nombre
                    print(f"Nueva conexion desde {direccion[0]}:{direccion[1]}, esperando nombre...")
                except Exception as e:
                    print(f"Error al aceptar conexion: {e}")

            elif s in pendientes:
                # este cliente todavia no mando su nombre, este mensaje ES el nombre
                try:
                    datos = s.recv(1024)       # recibe el nombre

                    if datos:
                        nombre = datos.decode()            # convierte bytes a texto
                        nombres[s] = nombre                # lo registra en el diccionario
                        pendientes.remove(s)               # ya no esta pendiente
                        sockets.append(s)                  # ahora si entra a la lista oficial

                        print(f"{nombre} se conecto.")
                        broadcast(f"{nombre} entro al chat!", s)              # avisa a todos
                        s.send("Conectado! Ya podes escribir.".encode())      # confirma al cliente
                    else:
                        # se fue antes de mandar el nombre
                        pendientes.remove(s)
                        s.close()
                except Exception as e:
                    print(f"Error al recibir nombre: {e}")
                    pendientes.remove(s)
                    s.close()

            else:
                # cliente ya registrado mandando un mensaje normal
                try:
                    mensaje = s.recv(1024)     # recibe el mensaje

                    if mensaje:
                        texto = mensaje.decode()
                        nombre = nombres.get(s, "Desconocido")

                        if texto == "/exit":              # comando para salir
                            desconectar(s)
                        else:
                            print(f"[{nombre}]: {texto}")
                            broadcast(f"[{nombre}]: {texto}", s)   # lo manda a todos
                    else:
                        # mensaje vacio = el cliente cerro la conexion
                        desconectar(s)

                except Exception as e:
                    print(f"Error al recibir mensaje: {e}")
                    desconectar(s)

except KeyboardInterrupt:
    print("\nCerrando el servidor...")

    for s in list(sockets) + list(pendientes):   # recorre clientes activos y pendientes
        if s != servidor:
            try:
                s.send("El servidor se cerro.".encode())   # avisa a cada cliente
            except:
                pass       # si falla el aviso, igual cerramos
            s.close()

    servidor.close()       # cierra el socket del servidor
    print("Servidor cerrado. Hasta luego!")
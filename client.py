import socket     
import threading 
import sys        # cerrar el programa
import time       # reintentos

HOST = "127.0.0.1"  
PORT = 5555         

MAX_REINTENTOS = 3   

nombre = input("Ingresa tu nombre de usuario: ").strip()   # strip() saca espacios al inicio y final
if not nombre:        # si no escribio nada
    nombre = "Anonimo"

# crear el socket del cliente
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Reintentos de conexion
# si el servidor no responde, reintenta varias veces antes de rendirse
conectado = False    # para saber si logro conectarse

for intento in range(1, MAX_REINTENTOS + 1):   # intenta MAX_REINTENTOS veces
    try:
        cliente.connect((HOST, PORT))   # intenta conectarse al servidor
        conectado = True                # si llego hasta aca, funciono
        break                           # sale del for, no necesita seguir reintentando
    except Exception as e:
        print(f"Intento {intento}/{MAX_REINTENTOS} fallido: {e}")
        if intento < MAX_REINTENTOS:             # si quedan intentos
            print("Reintentando en 2 segundos...")
            time.sleep(2)                        # espera antes de reintentar

if not conectado:    # si agoto todos los intentos sin exito
    print("No se pudo conectar. Asegurate de que servidor.py este corriendo.")
    sys.exit()       # cierra el programa

print(f"Conectado al servidor como '{nombre}'!")
print("Escribe tus mensajes. Usa /exit para salir.\n")

# mandamos el nombre al servidor (es lo primero que espera recibir)
cliente.send(nombre.encode())   # encode() convierte texto a bytes

# esperamos la confirmacion del servidor
confirmacion = cliente.recv(1024).decode()   # decode() convierte bytes a texto
print(f"[Servidor]: {confirmacion}\n")

def recibir():
    while True:
        try:
            mensaje = cliente.recv(1024)   # espera mensaje (bloqueante, se queda parado hasta que llega algo)
            if mensaje:
                print(mensaje.decode())    # muestra el mensaje en pantalla
            else:
                # bytes vacios = el servidor cerro la conexion
                print("El servidor se desconecto.")
                cliente.close()
                sys.exit()
        except:
            # cualquier error de red = perdimos la conexion
            print("Se perdio la conexion con el servidor.")
            cliente.close()
            sys.exit()

# crear y arrancar el hilo que escucha mensajes
hilo = threading.Thread(target=recibir)   # target indica que funcion ejecuta el hilo
hilo.daemon = True                        # si el programa principal cierra, este hilo cierra tambien
hilo.start()                              # arranca el hilo, desde aca recibir() corre en paralelo

# bucle principal: leer lo que escribe el usuario y mandarlo al servidor
while True:
    try:
        texto = input()        # espera que el usuario escriba algo y presione Enter

        if not texto:          # si presiono Enter sin escribir nada
            continue           # vuelve al inicio del while sin mandar nada

        cliente.send(texto.encode())   # manda el mensaje al servidor

        if texto == "/exit":           # si escribio el comando de salida
            print("Saliendo del chat...")
            cliente.close()            # cierra el socket
            break                      # termina el bucle y el programa

    except KeyboardInterrupt:
        print("\nSaliendo...")
        try:
            cliente.send("/exit".encode())   # avisa al servidor que nos vamos
        except:
            pass          # si falla el aviso, igual cerramos
        cliente.close()
        break

    except Exception as e:
        print(f"Error al enviar mensaje: {e}")
        break
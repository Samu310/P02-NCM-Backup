from netmiko import ConnectHandler
from getpass import getpass


usuario = input("Usuario SSH: ")
password = getpass("Password SSH: ")


router_r1 = {
    "device_type": "cisco_ios",
    "host": "1.1.1.1",
    "username": usuario,
    "password": password,
}


print("\nConectando a R1...")


conexion = ConnectHandler(**router_r1)


print("Conexion establecida correctamente.\n")


salida = conexion.send_command("show running-config")


print(salida)


conexion.disconnect()


print("\nConexion cerrada.")

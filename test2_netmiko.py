from netmiko import ConnectHandler
from getpass import getpass


usuario = input("Usuario SSH: ")
password = getpass("Password SSH: ")


routers = [
    {
        "name": "R1",
        "device_type": "cisco_ios",
        "host": "1.1.1.1",
        "username": usuario,
        "password": password,
    },
    {
        "name": "R2",
        "device_type": "cisco_ios",
        "host": "2.2.2.2",
        "username": usuario,
        "password": password,
    },
    {
        "name": "R3",
        "device_type": "cisco_ios",
        "host": "3.3.3.3",
        "username": usuario,
        "password": password,
    }
]


for router in routers:

    print(f"\nConectando a {router['name']} ({router['host']})...")

    conexion = ConnectHandler(
        device_type=router["device_type"],
        host=router["host"],
        username=router["username"],
        password=router["password"],
    )

    salida = conexion.send_command(
        "show ip interface brief"
    )

    print(salida)

    conexion.disconnect()

    print(f"Conexion con {router['name']} cerrada.")

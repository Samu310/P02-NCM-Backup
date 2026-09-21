from netmiko import ConnectHandler
from getpass import getpass
from pathlib import Path
from datetime import datetime


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


# Carpeta principal donde se guardarán los respaldos
BASE_DIR = Path("backups")

def guardar_backup(nombre, configuracion):

    # Carpeta individual del router
    carpeta_router = BASE_DIR / nombre

    carpeta_router.mkdir(
        parents=True,
        exist_ok=True
    )

    # Buscar backups existentes
    backups_existentes = list(
        carpeta_router.glob("*.txt")
    )

    # Si ya existe un backup...
    if backups_existentes:

        # Obtener el backup más reciente
        backup_anterior = max(
            backups_existentes,
            key=lambda archivo: archivo.stat().st_mtime
        )

        # Leer configuración anterior
        configuracion_anterior = (
            backup_anterior.read_text()
        )

        # Comparar configuraciones
        if configuracion_anterior.strip() == configuracion.strip():

            print(
                f"[SIN CAMBIOS] {nombre}: "
                f"se conserva el backup anterior."
            )

            return False

        print(
            f"[CAMBIO DETECTADO] {nombre}"
        )

        # Eliminar backups anteriores
        for archivo in backups_existentes:
            archivo.unlink()

    else:

        print(
            f"[PRIMER BACKUP] {nombre}"
        )

    # Generar fecha/hora
    fecha = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    # Crear nuevo nombre
    nuevo_backup = (
        carpeta_router /
        f"{nombre}_{fecha}.txt"
    )

    # Guardar configuración
    nuevo_backup.write_text(
        configuracion
    )

    print(
        f"[OK] Backup guardado en: "
        f"{nuevo_backup}"
    )

    return True

for router in routers:

    print(
        f"\nConectando a {router['name']} "
        f"({router['host']})..."
    )

    try:

        conexion = ConnectHandler(
            device_type=router["device_type"],
            host=router["host"],
            username=router["username"],
            password=router["password"],
        )

        # Obtener running-config
        configuracion = conexion.send_command(
            "show running-config"
        )

        conexion.disconnect()

        print(
            f"[OK] Configuración obtenida de "
            f"{router['name']}"
        )

        # Crear carpeta individual del router
        carpeta_router = BASE_DIR / router["name"]

        carpeta_router.mkdir(
            parents=True,
            exist_ok=True
        )

        # Fecha y hora
        fecha = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        # Nombre del archivo
        archivo = (
            carpeta_router /
            f"{router['name']}_{fecha}.txt"
        )

        # Guardar configuración
        archivo.write_text(configuracion)

        print(
            f"[OK] Backup guardado en: {archivo}"
        )

    except Exception as error:

        print(
            f"[ERROR] {router['name']}: "
            f"{error}"
        )

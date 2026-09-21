from netmiko import ConnectHandler
from getpass import getpass
from pathlib import Path
from datetime import datetime
import time


# ============================================================
# CREDENCIALES SSH
# ============================================================

usuario = input("Usuario SSH: ")
password = getpass("Password SSH: ")


# ============================================================
# DISPOSITIVOS
# ============================================================

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


# ============================================================
# DIRECTORIO DE BACKUPS
# ============================================================

BASE_DIR = Path("backups")


# ============================================================
# OBTENER RUNNING-CONFIG
# ============================================================

def obtener_configuracion(router):

    conexion = None

    try:

        conexion = ConnectHandler(
            device_type=router["device_type"],
            host=router["host"],
            username=router["username"],
            password=router["password"],
        )

        configuracion = conexion.send_command(
            "show running-config"
        )

        return configuracion.strip()

    finally:

        if conexion:
            conexion.disconnect()


# ============================================================
# GUARDAR Y COMPARAR BACKUP
# ============================================================

def guardar_backup(nombre, configuracion):

    # Crear carpeta individual del dispositivo
    carpeta_router = BASE_DIR / nombre

    carpeta_router.mkdir(
        parents=True,
        exist_ok=True
    )

    # Buscar backups existentes
    backups_existentes = list(
        carpeta_router.glob("*.txt")
    )

    # --------------------------------------------------------
    # SI YA EXISTE UN BACKUP
    # --------------------------------------------------------

    if backups_existentes:

        # Encontrar el archivo más reciente
        backup_anterior = max(
            backups_existentes,
            key=lambda archivo: archivo.stat().st_mtime
        )

        # Leer configuración anterior
        configuracion_anterior = backup_anterior.read_text(
            encoding="utf-8"
        )

        # Comparar
        if configuracion_anterior.strip() == configuracion.strip():

            print(
                f"[SIN CAMBIOS] {nombre}: "
                f"se conserva el backup anterior."
            )

            return False

        # Si llegamos aquí, la configuración cambió
        print(
            f"[CAMBIO DETECTADO] {nombre}"
        )

        # Eliminar respaldo anterior
        for archivo in backups_existentes:
            archivo.unlink()

    # --------------------------------------------------------
    # SI NO EXISTE BACKUP
    # --------------------------------------------------------

    else:

        print(
            f"[PRIMER BACKUP] {nombre}"
        )


    # ========================================================
    # CREAR NUEVO BACKUP
    # ========================================================

    fecha = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    nuevo_backup = (
        carpeta_router /
        f"{nombre}_{fecha}.txt"
    )

    nuevo_backup.write_text(
        configuracion,
        encoding="utf-8"
    )

    print(
        f"[OK] Backup guardado en: "
        f"{nuevo_backup}"
    )

    return True


# ============================================================
# CICLO PRINCIPAL DEL SISTEMA NCM
# ============================================================

try:

    while True:

        print("\n========================================")
        print("       CICLO DE RESPALDO NCM")
        print("========================================")

        print(
            "Fecha:",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        # ----------------------------------------------------
        # RECORRER TODOS LOS ROUTERS
        # ----------------------------------------------------

        for router in routers:

            print(
                f"\nConectando a "
                f"{router['name']} "
                f"({router['host']})..."
            )

            try:

                # Obtener running-config
                configuracion = obtener_configuracion(
                    router
                )

                print(
                    f"[OK] Configuración obtenida de "
                    f"{router['name']}"
                )

                # Comparar y guardar
                guardar_backup(
                    router["name"],
                    configuracion
                )

            except Exception as error:

                print(
                    f"[ERROR] No fue posible procesar "
                    f"{router['name']}"
                )

                print(
                    f"Detalle: {error}"
                )


        # ----------------------------------------------------
        # ESPERA ENTRE CICLOS
        # ----------------------------------------------------

        print("\n========================================")
        print("Esperando 5 segundos...")
        print("========================================\n")

        time.sleep(5)


# ============================================================
# CTRL + C
# ============================================================

except KeyboardInterrupt:

    print("\n========================================")
    print("Sistema NCM detenido por el usuario.")
    print("========================================")

from netmiko import ConnectHandler
from getpass import getpass
from pathlib import Path
from datetime import datetime
import subprocess
import time


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

INTERVALO = 5

# Directorio donde se encuentra este script/repositorio Git
REPO_DIR = Path(__file__).resolve().parent

# Directorio donde se almacenarán los backups
BASE_DIR = REPO_DIR / "backups"


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
# OBTENER RUNNING-CONFIG DEL ROUTER
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
# COMPARAR Y GUARDAR BACKUP
# ============================================================

def guardar_backup(nombre, configuracion):

    # Crear carpeta propia para cada router
    carpeta_router = BASE_DIR / nombre

    carpeta_router.mkdir(
        parents=True,
        exist_ok=True
    )

    # Buscar backups existentes
    backups_existentes = list(
        carpeta_router.glob("*.txt")
    )

    # ========================================================
    # YA EXISTE UN BACKUP
    # ========================================================

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

        # Comparar configuración nueva contra anterior
        if configuracion_anterior.strip() == configuracion.strip():

            print(
                f"[SIN CAMBIOS] {nombre}: "
                f"se conserva el backup anterior."
            )

            return False

        # Si llegamos aquí significa que hubo un cambio
        print(
            f"[CAMBIO DETECTADO] {nombre}"
        )

        # Eliminar el respaldo anterior
        for archivo in backups_existentes:
            archivo.unlink()

    # ========================================================
    # PRIMER BACKUP
    # ========================================================

    else:

        print(
            f"[PRIMER BACKUP] {nombre}"
        )


    # ========================================================
    # CREAR NUEVO ARCHIVO
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
        f"{nuevo_backup.relative_to(REPO_DIR)}"
    )

    return True


# ============================================================
# GIT + GITHUB
# ============================================================

def subir_github():

    fecha = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    try:

        print("\n[GIT] Preparando cambios...")

        # Registrar archivos nuevos y eliminados de backups/
        subprocess.run(
            [
                "git",
                "add",
                "-A",
                "backups"
            ],
            cwd=REPO_DIR,
            check=True
        )

        # Comprobar si Git detectó algún cambio
        estado = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--",
                "backups"
            ],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            check=True
        )

        # Si no hay cambios, no hacemos commit
        if not estado.stdout.strip():

            print(
                "[GIT] No hay cambios para registrar."
            )

            return False

        # Crear commit
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"Backup NCM - {fecha}"
            ],
            cwd=REPO_DIR,
            check=True
        )

        print(
            "[GIT] Commit creado correctamente."
        )

        # Subir a GitHub
        subprocess.run(
            [
                "git",
                "push",
                "origin",
                "main"
            ],
            cwd=REPO_DIR,
            check=True
        )

        print(
            "[GITHUB] Backup subido correctamente."
        )

        return True

    except subprocess.CalledProcessError as error:

        print(
            f"[ERROR GIT] Falló la integración "
            f"con GitHub: {error}"
        )

        return False


# ============================================================
# CICLO PRINCIPAL DEL NCM
# ============================================================

try:

    while True:

        inicio_ciclo = time.monotonic()

        print("\n========================================")
        print("       CICLO DE RESPALDO NCM")
        print("========================================")

        print(
            "Fecha:",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        # Indica si al menos un router cambió
        hubo_cambios = False


        # ====================================================
        # RECORRER LOS ROUTERS
        # ====================================================

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

                # Comparar contra backup anterior
                cambio = guardar_backup(
                    router["name"],
                    configuracion
                )

                # Si cambió al menos uno
                if cambio:
                    hubo_cambios = True

            except Exception as error:

                print(
                    f"[ERROR] No fue posible procesar "
                    f"{router['name']}"
                )

                print(
                    f"Detalle: {error}"
                )


        # ====================================================
        # ACTUALIZAR GITHUB
        # ====================================================

        if hubo_cambios:

            print(
                "\nSe detectaron cambios."
                "\nActualizando repositorio..."
            )

            subir_github()

        else:

            print(
                "\nNo hubo cambios en este ciclo."
                "\nNo se realizará commit."
            )


        # ====================================================
        # CONTROL DEL INTERVALO
        # ====================================================

        tiempo_transcurrido = (
            time.monotonic() - inicio_ciclo
        )

        tiempo_espera = max(
            0,
            INTERVALO - tiempo_transcurrido
        )

        print("\n========================================")

        if tiempo_espera > 0:

            print(
                f"Esperando {tiempo_espera:.1f} segundos..."
            )

            time.sleep(
                tiempo_espera
            )

        else:

            print(
                "El ciclo tardó más de 5 segundos."
            )

            print(
                "Iniciando el siguiente inmediatamente."
            )

        print("========================================")


# ============================================================
# DETENER CON CTRL + C
# ============================================================

except KeyboardInterrupt:

    print("\n========================================")
    print("Sistema NCM detenido por el usuario.")
    print("========================================")

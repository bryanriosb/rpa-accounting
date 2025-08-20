import os
import shutil


def cleanup_directories(base_dir: str):
    """Limpia los subdirectorios de ejecuciones anteriores."""
    print(f"--- Limpiando el directorio de descargas: '{base_dir}' ---")
    os.makedirs(base_dir, exist_ok=True)
    for item_name in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item_name)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
            print(f"  - Directorio anterior eliminado: {item_name}")
    print("--- Limpieza completada. ---\n")
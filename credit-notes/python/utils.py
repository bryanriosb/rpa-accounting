import os
import shutil


def cleanup_directories(base_dir: str):
    """Limpia completamente el directorio de ejecuciones anteriores."""
    print(f"--- Limpiando el directorio de descargas: '{base_dir}' ---")
    
    if os.path.exists(base_dir):
        # Eliminar todo el contenido del directorio
        for item_name in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item_name)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"  - Directorio eliminado: {item_name}")
                else:
                    os.remove(item_path)
                    print(f"  - Archivo eliminado: {item_name}")
            except Exception as e:
                print(f"  - Error eliminando {item_name}: {e}")
    
    # Crear el directorio si no existe
    os.makedirs(base_dir, exist_ok=True)
    print("--- Limpieza completada. ---\n")


def cleanup_base_download_directory(base_download_directory: str):
    """Limpia el contenido del directorio base de descargas (compatible con volúmenes Docker)."""
    print(f"🧹 Limpiando contenido del directorio base: '{base_download_directory}'")
    
    # Crear el directorio si no existe
    os.makedirs(base_download_directory, exist_ok=True)
    
    if os.path.exists(base_download_directory):
        # Eliminar solo el contenido, no el directorio en sí (para compatibilidad con Docker volumes)
        for item_name in os.listdir(base_download_directory):
            item_path = os.path.join(base_download_directory, item_name)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"  ✅ Directorio eliminado: {item_name}")
                else:
                    os.remove(item_path)
                    print(f"  ✅ Archivo eliminado: {item_name}")
            except Exception as e:
                print(f"  ❌ Error eliminando {item_name}: {e}")
    
    print(f"  ✅ Limpieza del directorio base completada\n")
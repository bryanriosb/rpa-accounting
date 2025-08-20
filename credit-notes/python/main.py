import multiprocessing
import os
import asyncio
from datetime import datetime

from playwright.async_api import async_playwright
from portal_processor import AsyncPortalProcessor  # Importar la clase mejorada
from utils import cleanup_directories


async def _async_worker(client_data, target_date, client_download_dir):
    """
    Función ASÍNCRONA que contiene la lógica de Playwright con manejo mejorado de errores.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=50)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        try:
            credentials = {
                "nit": client_data["nit"],
                "password": client_data["password"],
            }

            processor = AsyncPortalProcessor(
                page=page,
                main_url=client_data["url"],
                credentials=credentials,
                target_date=target_date,
                base_download_dir=client_download_dir
            )

            # Ahora run() retorna un diccionario con PDFs y errores
            results = await processor.run()

            # Determinar el estado basado en los resultados
            if results["errores"]:
                if results["pdfs_descargados"]:
                    status = "partial_success"
                    print(
                        f"⚠️ Completado parcialmente: {client_data['name']} - {len(results['pdfs_descargados'])} PDFs descargados, {len(results['errores'])} errores")
                else:
                    status = "failed"
                    print(f"❌ Falló: {client_data['name']} - {len(results['errores'])} errores")
            else:
                status = "success"
                print(
                    f"✅ Completado exitosamente: {client_data['name']} - {len(results['pdfs_descargados'])} PDFs descargados")

            return {
                "url": client_data['url'],
                "name": client_data['name'],
                "results": results,
                "status": status
            }

        except Exception as e:
            print(f"❌ ERROR crítico con {client_data['name']}: {e}")
            return {
                "url": client_data['url'],
                "name": client_data['name'],
                "results": {
                    "pdfs_descargados": [],
                    "errores": [{
                        "tipo": "ERROR_CRITICO_GENERAL",
                        "mensaje": str(e)
                    }]
                },
                "status": "critical_error"
            }
        finally:
            # Asegurarse de cerrar todo correctamente
            await page.close()
            await context.close()
            await browser.close()


def process_single_client(client_data, target_date, base_download_directory):
    """
    Función SÍNCRONA que se ejecutará en paralelo.
    """
    client = client_data
    client_download_dir = os.path.join(base_download_directory, client['dir_name'])

    print(f"🚀 Iniciando procesamiento de {client['name']} en proceso {os.getpid()}")

    try:
        # Tareas síncronas
        cleanup_directories(client_download_dir)

        # Ejecutar el worker asíncrono
        return asyncio.run(_async_worker(client, target_date, client_download_dir))

    except Exception as e:
        url = client["url"]
        print(f"❌ ERROR crítico con {client['name']}: {e}")
        return {
            "url": url,
            "name": client['name'],
            "results": {
                "pdfs_descargados": [],
                "errores": [{
                    "tipo": "ERROR_CRITICO_PROCESO",
                    "mensaje": str(e)
                }]
            },
            "status": "critical_error"
        }


def print_detailed_summary(results_list):
    """
    Imprime un resumen detallado y formateado de los resultados.
    """
    print("\n\n" + "=" * 80)
    print("                    RESUMEN DETALLADO DE EJECUCIÓN")
    print("=" * 80)
    print(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    total_pdfs = 0
    total_errors = 0
    successful_portals = 0
    failed_portals = 0
    partial_portals = 0

    for result in results_list:
        portal_name = result["name"]
        status = result["status"]
        pdfs = result["results"]["pdfs_descargados"]
        errors = result["results"]["errores"]

        print(f"\n📊 Portal: {portal_name}")
        print(f"   URL: {result['url']}")
        print(f"   Estado: ", end="")

        if status == "success":
            print("✅ EXITOSO")
            successful_portals += 1
        elif status == "partial_success":
            print("⚠️ PARCIALMENTE EXITOSO")
            partial_portals += 1
        elif status == "failed":
            print("❌ FALLIDO")
            failed_portals += 1
        else:
            print("💀 ERROR CRÍTICO")
            failed_portals += 1

        print(f"   PDFs descargados: {len(pdfs)}")
        total_pdfs += len(pdfs)

        if pdfs:
            print("   Archivos:")
            for pdf in pdfs[:5]:  # Mostrar máximo 5 PDFs
                print(f"      - {pdf['centro']}/{pdf['archivo']}")
            if len(pdfs) > 5:
                print(f"      ... y {len(pdfs) - 5} más")

        if errors:
            print(f"   ⚠️ Errores encontrados: {len(errors)}")
            total_errors += len(errors)
            for error in errors:
                print(f"      - Tipo: {error['tipo']}")
                if 'centro' in error:
                    print(f"        Centro: {error['centro']}")
                print(f"        Mensaje: {error['mensaje']}")
                print()

    print("\n" + "=" * 80)
    print("                         RESUMEN GLOBAL")
    print("=" * 80)
    print(f"Total de portales procesados: {len(results_list)}")
    print(f"  - Exitosos: {successful_portals}")
    print(f"  - Parcialmente exitosos: {partial_portals}")
    print(f"  - Fallidos: {failed_portals}")
    print(f"\nTotal de PDFs descargados: {total_pdfs}")
    print(f"Total de errores: {total_errors}")
    print("=" * 80)


def main():
    # --- Configuración General ---
    target_date = "2025/04/25"
    base_download_directory = "notes_downloads"
    MAX_CONCURRENT_CLIENTS = 4  # Máximo de clientes en paralelo

    # Lista de portales a procesar
    portal_clients = [
        {
            "nit": "891303109",
            "password": "Cartera2023",
            "name": "Surtifamiliar",
            "url": "https://portalproveedores.surtifamiliar.com",
            "dir_name": "SURTIFAMILIAR",
        },
        {
            "nit": "891303109",
            "password": "2023",
            "name": "Megatiendas",
            "url": "https://proveedores.megatiendas.co/megatiendas",
            "dir_name": "MEGATIENDAS",
        },
        {
            "nit": "891303109",
            "password": "l18mr7",
            "name": "Mercar",
            "url": "http://190.85.196.187",
            "dir_name": "MERCAR",
        },
        {
            "nit": "891303109",
            "password": "Cartera2023",
            "name": "La Montaña",
            "url": "https://proveedores.lamontana.co",
            "dir_name": "LAMONTANA",
        },
        # {
        #     "nit": "891303109",
        #     "password": "Toning2020$",
        #     "name": "El Jardin",
        #     "url": "https://proveedores.eljardin.co",
        #     "dir_name": "ELJARDIN",
        # },
    ]

    print(
        f"🎯 Procesando {len(portal_clients)} portales con máximo {MAX_CONCURRENT_CLIENTS} en paralelo usando multiprocessing.Pool")
    print(f"📅 Fecha objetivo: {target_date}\n")

    # Preparar los argumentos para cada tarea
    tasks = [(client, target_date, base_download_directory) for client in portal_clients]

    # --- EJECUCIÓN PARALELA CON MULTIPROCESSING ---
    with multiprocessing.Pool(processes=MAX_CONCURRENT_CLIENTS) as pool:
        results_list = pool.starmap(process_single_client, tasks)

    # Mostrar resumen detallado
    print_detailed_summary(results_list)

    # Guardar resultados en un archivo para referencia
    import json
    results_file = f"logs/resultados_scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_list, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Resultados guardados en: {results_file}")


if __name__ == "__main__":
    main()
import multiprocessing
import os
import asyncio
from datetime import datetime
import json
import re
import uuid

from email_sender import send_email_with_attachments
from logger import Logger
from playwright.async_api import async_playwright
from portal_processor import AsyncPortalProcessor
from s3_uploader import S3Uploader
from utils import cleanup_directories, cleanup_base_download_directory
from dotenv import load_dotenv
from sqs_poller import SQSPoller
import logging

load_dotenv()

console_logger = logging.getLogger(__name__)

APP_ENV = os.getenv("APP_ENV", "production")

async def _async_worker(client_data, target_date, client_download_dir, app_env, execution_id):
    """
    Función ASÍNCRONA que contiene la lógica de Playwright con manejo mejorado de errores.
    """
    logger = Logger(client_data['name'], execution_id)

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
                portal_name=client_data["name"],
                credentials=credentials,
                target_date=target_date,
                base_download_dir=client_download_dir,
                app_env=app_env,
                logger=logger
            )

            results = await processor.run()

            if results["errores"]:
                if results["pdfs_descargados"]:
                    status = "partial_success"
                    logger.warn(f"Completado parcialmente: {len(results['pdfs_descargados'])} PDFs descargados, {len(results['errores'])} errores")
                else:
                    status = "failed"
                    logger.error(f"Falló: {len(results['errores'])} errores")
            else:
                status = "success"
                logger.info(f"Completado exitosamente: {len(results['pdfs_descargados'])} PDFs descargados")

            return {
                "url": client_data['url'],
                "name": client_data['name'],
                "results": results,
                "status": status
            }

        except Exception as e:
            logger.error(f"ERROR crítico: {e}")
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
            await page.close()
            await context.close()
            await browser.close()


def process_single_client(client_data, target_date, base_download_directory, app_env):
    """
    Función SÍNCRONA que se ejecutará en paralelo.
    """
    client = client_data
    client_download_dir = os.path.join(base_download_directory, client['dir_name'])
    execution_id = client['execution_id']
    print(f"🎯 Iniciando ejecución con ID: {execution_id}")

    logger = Logger(client['name'], execution_id)
    logger.info(f"Iniciando procesamiento en proceso {os.getpid()}")

    try:
        cleanup_directories(client_download_dir)

        return asyncio.run(_async_worker(client, target_date, client_download_dir, app_env, execution_id))

    except Exception as e:
        logger.error(f"ERROR crítico en el proceso: {e}")
        return {
            "url": client["url"],
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

def print_and_get_summary(results_list):
    """
    Imprime un resumen detallado y formateado de los resultados y retorna el resumen.
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
                file_info = pdf.get('s3_url', pdf.get('archivo', 'N/A'))
                print(f"      - {file_info}")
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

    return {
        "total_portals_processed": len(results_list),
        "successful_portals": successful_portals,
        "partial_portals": partial_portals,
        "failed_portals": failed_portals,
        "total_pdfs_downloaded": total_pdfs,
        "total_errors": total_errors,
    }


def save_results_to_dynamodb(results_list, summary_data):
    """
    Guarda los resultados del procesamiento en DynamoDB.
    """
    from dynamodb_uploader import save_portal_report, save_global_summary

    print("\n" + "=" * 80)
    print("              GUARDANDO RESULTADOS EN DYNAMODB")
    print("=" * 80)

    # Guardar reportes individuales
    for result in results_list:
        portal_name = result["name"]
        status = result["status"]
        pdfs = result["results"]["pdfs_descargados"]
        errors = result["results"]["errores"]

        if status in ["success", "partial_success"]:
            dynamo_status = "EXITOSO" if status == "success" else "PARCIALMENTE EXITOSO"
        else:
            dynamo_status = "FALLIDO"

        report_data = {
            "portal_name": portal_name,
            "url": result["url"],
            "status": dynamo_status,
            "pdfs_downloaded": len(pdfs),
            "files": [pdf.get('s3_url', pdf.get('archivo')) for pdf in pdfs],
            "errors": errors,
            "target_date": result.get("target_date"),
        }
        save_portal_report(report_data)

    # Guardar resumen global
    save_global_summary(summary_data)

def main():
    # Required to reload table in client
    logger = Logger('client', 'a821585f-4891-4a5d-80d4-c3414190c09b')

    sqs_queue_url = os.getenv("SQS_QUEUE_URL")
    if not sqs_queue_url:
        print("SQS_QUEUE_URL environment variable not set. Exiting.")
        return

    poller = SQSPoller(queue_url=sqs_queue_url)

    while True:
        target_date = poller.poll_for_message()
        valid_date_format = re.fullmatch(r"\d{4}/\d{2}/\d{2}", target_date)
        if not target_date or not valid_date_format:
            # poller will log errors, continue polling
            continue

        # --- Configuración General ---
        base_download_directory = "notes_downloads"
        MAX_CONCURRENT_CLIENTS = 4

        portal_clients = [
            {
            "nit": "891303109",
            "password": "Cartera2023",
            "name": "Surtifamiliar",
            "url": "https://portalproveedores.surtifamiliar.com",
            "dir_name": "SURTIFAMILIAR",
            "execution_id": "a57b5c52feaa4e3a8718ab4c4b0a01c6"
        },
        # {
        #     "nit": "891303109",
        #     "password": "2023",
        #     "name": "Megatiendas",
        #     "url": "https://proveedores.megatiendas.co/megatiendas",
        #     "dir_name": "MEGATIENDAS",
        #     "execution_id": "3587e34b30ad4f609b6caafce9308496"
        # },
        {
            "nit": "891303109",
            "password": "l18mr7",
            "name": "Mercar",
            "url": "http://190.85.196.187",
            "dir_name": "MERCAR",
            "execution_id": "286707d82bcf45a1999f2ab4b4f832e8"
        },
        {
            "nit": "891303109",
            "password": "Cartera2023",
            "name": "La Montaña",
            "url": "https://proveedores.lamontana.co",
            "dir_name": "LAMONTANA",
            "execution_id": "fa48558d5cfe46f79ab0ab54010fb579"
        },
        ]

        print(f"🔄 Procesando {len(portal_clients)} portales con máximo {MAX_CONCURRENT_CLIENTS} en paralelo.")
        print(f"📅 Fecha objetivo: {target_date}\n")
        print(f"⚙️ Modo de ejecución: {APP_ENV.upper()}\n")
        
        # Limpiar completamente el directorio base antes de iniciar
        cleanup_base_download_directory(base_download_directory)

        tasks = [(client, target_date, base_download_directory, APP_ENV) for client in portal_clients]

        with multiprocessing.Pool(processes=MAX_CONCURRENT_CLIENTS) as pool:
            results_list = pool.starmap(process_single_client, tasks)
        
        for result in results_list:
            result["target_date"] = target_date

        summary_data = print_and_get_summary(results_list)

        if APP_ENV == 'production':
            save_results_to_dynamodb(results_list, summary_data)

        results_file_name = f"resultados_scraping_{datetime.now().strftime('%Y%m%d')}.json"
        results_content = json.dumps(results_list, ensure_ascii=False, indent=2)

        if APP_ENV == 'development':
            path_dir = f'logs/{results_file_name}'
            with open(path_dir, 'w', encoding='utf-8') as f:
                f.write(results_content)
            print(f"\n💾 Resultados guardados localmente en: {results_file_name}")
        elif APP_ENV == 'production':
            s3_uploader = S3Uploader()
            try:
                s3_url = asyncio.run(s3_uploader.upload_log_to_s3(results_content, results_file_name))
                print(f"\n☁️ Resultados de log subidos a S3: {s3_url}")
            except Exception as e:
                print(f"❌ Error al subir el log a S3: {e}")

        
        email_recipients = os.getenv("EMAIL_RECIPIENTS")
        target_date_formatted = target_date.replace("/", "-")  # Formatear fecha para el asunto del correo
        if email_recipients:
            recipients = [e.strip() for e in email_recipients.split(',')]
            subject = f"Reporte de Notas de Crédito - {datetime.now().strftime('%Y-%m-%d')} para fecha objetivo {target_date_formatted}"
            body = f"Se adjuntan las notas de crédito descargadas correspondientes a la fecha objetivo {target_date}.\n\n"
            send_email_with_attachments(recipients, subject, body, base_download_directory)
        else:
            print("⚠️ La variable de entorno EMAIL_RECIPIENTS no está definida. No se enviará correo.")

        logger.info("Finished")
if __name__ == "__main__":
    main()
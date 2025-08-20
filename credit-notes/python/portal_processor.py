import asyncio
from datetime import datetime
from typing import Optional, Callable, Any, re
import traceback
from playwright.async_api import Page, expect, TimeoutError as PlaywrightTimeout
import os
import base64
from s3_uploader import S3Uploader
from logger import Logger


class AsyncPortalProcessor:
    """
    Versión ASÍNCRONA de PortalProcessor con lógica de reintento mejorada.
    """
    JS_BLOB_TO_BASE64 = "async u => (await fetch(u).then(r=>r.blob()).then(b=>new Promise((s,j)=>{const r=new FileReader();r.onload=()=>s(r.result.split(',',2)[1]);r.onerror=j;r.readAsDataURL(b)})))"

    def __init__(self, page: Page, main_url: str, credentials: dict, target_date: str, base_download_dir: str, app_env: str, logger: Logger):
        self.page = page
        self.main_url = main_url
        self.credentials = credentials
        self.target_date = target_date
        self.base_download_dir = base_download_dir
        self.downloaded_pdfs_summary = []
        self.errors_summary = []  # Para almacenar errores después de reintentos fallidos
        self.max_retries = 3
        self.retry_delay = 5
        self.s3_uploader = S3Uploader()
        self.app_env = app_env
        self.logger = logger

    async def _retry_with_reload(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """
        Ejecuta una función con reintentos y recarga de página en caso de timeout.
        """
        func_name = func.__name__ if hasattr(func, '__name__') else str(func)

        for attempt in range(self.max_retries):
            try:
                print(f"   🔄 Ejecutando {func_name} - Intento {attempt + 1}/{self.max_retries}")
                result = await func(*args, **kwargs)
                print(f"   ✅ {func_name} completado exitosamente")
                return result
            except (PlaywrightTimeout, TimeoutError) as e:
                print(f"⚠️ Timeout en {func_name} - Intento {attempt + 1}/{self.max_retries}: {str(e)}")
                print(f"   URL actual: {self.page.url}")

                if attempt < self.max_retries - 1:
                    print(f"   -> Recargando página y reintentando en {self.retry_delay} segundos...")
                    try:
                        await self.page.reload(wait_until="networkidle", timeout=30000)
                        print(f"   -> Página recargada exitosamente")
                    except Exception as reload_error:
                        print(f"   ❌ Error al recargar: {reload_error}")
                        # Si la recarga falla, intentamos navegar de nuevo
                        current_url = self.page.url
                        print(f"   -> Navegando de nuevo a: {current_url}")
                        try:
                            await self.page.goto(current_url, wait_until="networkidle", timeout=30000)
                            print(f"   -> Navegación exitosa")
                        except Exception as nav_error:
                            print(f"   ❌ Error al navegar: {nav_error}")

                    await asyncio.sleep(self.retry_delay)
                else:
                    print(f"❌ {func_name} falló después de {self.max_retries} intentos")
                    raise e
            except Exception as e:
                print(f"❌ Error inesperado en {func_name}: {str(e)}")
                raise e

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normaliza diferentes formatos de fecha a un formato común YYYY/MM/DD.

        Formatos soportados:
        - 2025/06/11
        - 20250611
        - 2025-06-11
        - 11/06/2025
        - 11-06-2025
        """
        if not date_str:
            return None

        # Limpiar espacios en blanco
        date_str = date_str.strip()

        # Intentar parsear diferentes formatos
        formats_to_try = [
            ('%Y/%m/%d', 'YYYY/MM/DD'),
            ('%Y-%m-%d', 'YYYY-MM-DD'),
            ('%Y%m%d', 'YYYYMMDD'),
            ('%d/%m/%Y', 'DD/MM/YYYY'),
            ('%d-%m-%Y', 'DD-MM-YYYY'),
        ]

        for date_format, format_name in formats_to_try:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                # Retornar en formato YYYY/MM/DD
                return parsed_date.strftime('%Y/%m/%d')
            except ValueError:
                continue

        # Si no se pudo parsear con los formatos estándar, intentar con regex
        # Para formato YYYYMMDD sin separadores
        match = re.match(r'^(\d{4})(\d{2})(\d{2})$', date_str)
        if match:
            year, month, day = match.groups()
            try:
                # Validar que sea una fecha válida
                datetime(int(year), int(month), int(day))
                return f"{year}/{month}/{day}"
            except ValueError:
                pass

        print(f"⚠️ No se pudo parsear la fecha: '{date_str}'")
        return None

    def _dates_match(self, date1: str, date2: str) -> bool:
        """
        Compara si dos fechas son iguales, independientemente del formato.
        """
        normalized_date1 = self._normalize_date(date1)
        normalized_date2 = self._normalize_date(date2)

        if normalized_date1 is None or normalized_date2 is None:
            # Si alguna fecha no se puede parsear, hacer comparación directa
            return date1.strip() == date2.strip()

        return normalized_date1 == normalized_date2

    async def run(self) -> dict:
        """
        Ejecuta el procesamiento y retorna un diccionario con PDFs descargados y errores.
        """
        print(f"\n>>> Iniciando procesamiento para: {self.main_url} <<<")
        print(f"    Fecha objetivo: {self.target_date}")
        try:
            await self._login()
            await self._navigate_to_notes()
            await self._process_centers()
        except Exception as e:
            print(f"❌ Error crítico durante el procesamiento: {str(e)}")
            self.errors_summary.append({
                "tipo": "ERROR_CRITICO",
                "mensaje": str(e),
                "traceback": traceback.format_exc()
            })

        print(f"\n>>> Procesamiento completado para: {self.main_url} <<<")
        self.logger.info(f"Procesamiento completado.")
        print(f"    Total PDFs descargados: {len(self.downloaded_pdfs_summary)}")
        self.logger.info(f"Total PDFs descargados: {len(self.downloaded_pdfs_summary)}")
        print(f"    Total errores: {len(self.errors_summary)}")
        self.logger.info(f"Total errores: {len(self.errors_summary)}")

        return {
            "pdfs_descargados": self.downloaded_pdfs_summary,
            "errores": self.errors_summary
        }

    async def _login(self):
        print("Paso 1: Iniciando proceso de login...")
        await self.page.goto(self.main_url)
        await self.page.get_by_role("link", name="Ya tiene una cuenta de proveedor? Ingrese aqui").click()
        await self.page.locator('input[name="nit"]').fill(self.credentials["nit"])
        await self.page.locator('input[name="password"]').fill(self.credentials["password"])
        await self.page.get_by_role("button", name="Ingresar").click()
        await expect(self.page).to_have_url(f"{self.main_url}/portal", timeout=15000)
        print("Login exitoso.")

    async def _navigate_to_notes(self):
        print("Paso 2: Navegando a la sección de 'Notas'...")
        current_url = self.page.url
        print(f"   URL actual: {current_url}")

        # Hacer clic en Notas
        # await self.page.locator(".menu-option-wrapper:has-text('Notas')").get_by_role("link").click()

        # Esperar un momento para que la navegación ocurra
        await self.page.wait_for_load_state("networkidle")

        # Verificar la URL después del clic
        new_url = self.page.url
        print(f"   URL después del clic: {new_url}")

        # Verificar si estamos en la página correcta
        if "/portal/co-notas" not in new_url:
            print(f"⚠️ Advertencia: Se esperaba navegar a /portal/co-notas pero estamos en {new_url}")
            # Intentar navegar directamente
            expected_url = f"{self.main_url}/portal/co-notas"
            print(f"   Intentando navegar directamente a: {expected_url}")
            await self.page.goto(expected_url)
            await self.page.wait_for_load_state("networkidle")
            print(f"   URL final: {self.page.url}")

        # Cerrar panel lateral si existe
        try:
            await self.page.locator(".page-body").click()
            print("Panel lateral cerrado.")
        except:
            print("No se encontró panel lateral para cerrar.")

    async def _wait_for_centers(self):
        """Espera a que los centros estén visibles con reintentos."""
        centers_selector = ".co-container"

        # Verificar primero qué elementos hay en la página
        print(f"   Verificando presencia de centros en: {self.page.url}")

        # Intentar cerrar panel lateral si existe
        try:
            await self.page.locator(".page-body").click()
        except:
            pass

        # Verificar si hay centros
        try:
            # Primero verificar si estamos en la página correcta
            if "/portal/co-notas" not in self.page.url:
                print(f"⚠️ No estamos en la página de centros. URL actual: {self.page.url}")
                # Intentar navegar a la página correcta
                await self.page.goto(f"{self.main_url}/portal/co-notas")
                await self.page.wait_for_load_state("networkidle")

            # Esperar a que aparezcan los centros
            await expect(self.page.locator(centers_selector).first).to_be_visible(timeout=30000)
            count = await self.page.locator(centers_selector).count()
            print(f"   ✓ Se encontraron {count} elementos con selector '{centers_selector}'")
        except Exception as e:
            # Si no hay centros, verificar si hay otra estructura
            print(f"   ❌ No se encontraron centros con selector '{centers_selector}'")

            # Intentar diagnosticar qué hay en la página
            try:
                # Verificar si hay tabla de notas directamente
                if await self.page.locator("table.info-table").count() > 0:
                    print("   ℹ️ Se encontró una tabla de notas directamente (sin centros)")
                    raise Exception("La página muestra notas directamente sin centros de operación")

                # Verificar otros posibles selectores
                possible_selectors = [".co-list", ".center-container", ".operation-center", ".nota-container"]
                for selector in possible_selectors:
                    count = await self.page.locator(selector).count()
                    if count > 0:
                        print(f"   ℹ️ Se encontraron {count} elementos con selector '{selector}'")

                # Mostrar algo del contenido para debug
                body_text = await self.page.locator("body").inner_text()
                print(f"   ℹ️ Primeros 200 caracteres del body: {body_text[:200]}...")

            except Exception as debug_error:
                print(f"   Error durante diagnóstico: {debug_error}")

            raise e

    async def _process_centers(self):
        print("Paso 3: Procesando centros de operación...")

        centers_selector = ".co-container"
        documents_table_selector = "table.info-table"
        center_list_url = f"{self.main_url}/portal/co-notas"

        # Primero verificar si hay centros o si las notas se muestran directamente
        try:
            # Verificar si ya hay una tabla de notas visible (sin centros)
            if await self.page.locator(documents_table_selector).count() > 0:
                print("ℹ️ Detectado: Las notas se muestran directamente sin centros de operación")
                print("   Procesando notas directamente...")

                # Procesar como un único "centro" virtual
                center_code = "UNICO"
                center_name = "Centro_Único"

                try:
                    await self._process_documents_for_center(center_code, center_name)
                    print(f"✅ Notas procesadas exitosamente")
                except Exception as e:
                    error_msg = f"Error procesando notas directas: {str(e)}"
                    print(f"❌ {error_msg}")
                    self.errors_summary.append({
                        "tipo": "ERROR_PROCESAMIENTO_NOTAS_DIRECTAS",
                        "centro": f"{center_code}_{center_name}",
                        "mensaje": error_msg,
                        "detalles": str(e)
                    })
                return
        except:
            pass

        # Si no hay tabla directa, intentar con centros
        try:
            await self._retry_with_reload(self._wait_for_centers)
        except Exception as e:
            # Verificar una vez más si es porque las notas están directamente
            if "/portal/notas" in self.page.url and await self.page.locator(documents_table_selector).count() > 0:
                print("ℹ️ Confirmado: Portal muestra notas directamente sin dividir por centros")
                center_code = "GENERAL"
                center_name = "Todas_Las_Notas"

                try:
                    await self._process_documents_for_center(center_code, center_name)
                    print(f"✅ Notas procesadas exitosamente")
                except Exception as e:
                    error_msg = f"Error procesando notas: {str(e)}"
                    print(f"❌ {error_msg}")
                    self.errors_summary.append({
                        "tipo": "ERROR_PROCESAMIENTO_NOTAS",
                        "centro": f"{center_code}_{center_name}",
                        "mensaje": error_msg,
                        "detalles": str(e)
                    })
                return

            # Si definitivamente no hay ni centros ni tabla, es un error
            error_msg = f"No se pudieron cargar los centros después de {self.max_retries} intentos"
            print(f"❌ {error_msg}")
            self.errors_summary.append({
                "tipo": "ERROR_CARGA_CENTROS",
                "mensaje": error_msg,
                "detalles": str(e)
            })
            return

        # Procesar centros normally si existen
        num_centers = await self.page.locator(centers_selector).count()
        print(f"Se encontraron {num_centers} centros de operación.")

        for i in range(num_centers):
            center_name = "Desconocido"
            center_code = "Desconocido"

            try:
                # Obtener información del centro actual
                current_center = self.page.locator(centers_selector).nth(i)

                # Intentar obtener el código y nombre del centro
                try:
                    center_code = await current_center.locator("span.co-title:has-text('CODIGO:') + span").inner_text()
                    center_name = await current_center.locator("span.co-title:has-text('NOMBRE:') + span").inner_text()
                except:
                    print(f"⚠️ No se pudo obtener información del centro {i + 1}")

                print(f"\n--- Procesando Centro {i + 1}/{num_centers}: {center_name} ({center_code}) ---")

                # Intentar procesar el centro con reintentos
                success = False
                for attempt in range(self.max_retries):
                    try:
                        print(f"   Intento {attempt + 1}/{self.max_retries}")

                        # Asegurarse de estar en la página de centros
                        if self.page.url != center_list_url:
                            await self.page.goto(center_list_url)
                            await self._retry_with_reload(self._wait_for_centers)

                        # Re-obtener el centro después de posible navegación
                        current_center = self.page.locator(centers_selector).nth(i)

                        # Hacer clic en el centro
                        await current_center.click()

                        # Esperar a que la tabla aparezca (con timeout personalizado)
                        try:
                            await expect(self.page.locator(documents_table_selector)).to_be_visible(timeout=30000)
                            print(f"   -> Tabla de documentos cargada para '{center_name}'.")
                        except PlaywrightTimeout:
                            if attempt < self.max_retries - 1:
                                print(f"   -> Timeout esperando tabla. Recargando página...")
                                await self.page.reload(wait_until="networkidle", timeout=30000)
                                continue
                            else:
                                raise

                        # Procesar documentos
                        await self._process_documents_for_center(center_code, center_name)

                        # Volver a la lista de centros
                        print(f"   -> Regresando a la lista de centros...")
                        await self.page.goto(center_list_url)
                        await self._retry_with_reload(self._wait_for_centers)

                        print(f"✅ Centro '{center_name}' procesado exitosamente.")
                        success = True
                        break

                    except Exception as e:
                        print(f"⚠️ Error en intento {attempt + 1}: {str(e)}")
                        if attempt < self.max_retries - 1:
                            print(f"   -> Navegando de vuelta a la lista de centros...")
                            await self.page.goto(center_list_url)
                            await asyncio.sleep(self.retry_delay)
                        else:
                            # Último intento fallido
                            error_msg = f"Error procesando centro {center_name} después de {self.max_retries} intentos"
                            print(f"❌ {error_msg}")
                            self.errors_summary.append({
                                "tipo": "ERROR_PROCESAMIENTO_CENTRO",
                                "centro": f"{center_code}_{center_name}",
                                "mensaje": error_msg,
                                "detalles": str(e)
                            })
                            # Asegurar que estamos en la página correcta para el siguiente centro
                            try:
                                await self.page.goto(center_list_url)
                                await self._wait_for_centers()
                            except:
                                pass

            except Exception as e:
                # Error no manejado
                print(f"❌ Error crítico procesando centro {i + 1}: {str(e)}")
                self.errors_summary.append({
                    "tipo": "ERROR_CRITICO_CENTRO",
                    "centro": f"{center_code}_{center_name}",
                    "mensaje": f"Error crítico en centro {i + 1}",
                    "detalles": str(e)
                })
                # Intentar recuperar navegando a la lista
                try:
                    await self.page.goto(center_list_url)
                    await self._wait_for_centers()
                except:
                    pass

    async def _process_documents_for_center(self, center_code: str, center_name: str):
        documents_table = self.page.locator("table.info-table")
        await expect(documents_table).to_be_visible(timeout=10000)

        directory_created = False
        center_folder_path = ""

        rows_selector = "table.info-table tbody tr"
        try:
            await self.page.wait_for_selector(rows_selector, timeout=5000)
            num_rows = await self.page.locator(rows_selector).count()
        except:
            print("No se encontraron documentos en la tabla para este centro.")
            return

        for j in range(num_rows):
            try:
                current_row = self.page.locator(rows_selector).nth(j)
                cells = await current_row.locator("td").all_inner_texts()
                row_data = {"document": cells[0], "cross_reference_doc": cells[1], "date": cells[2].strip()}

                if self._dates_match(row_data["date"], self.target_date):
                    folder_name = f"{center_code}_{center_name.replace(' ', '_')}"
                    await self._download_pdf(current_row, row_data, folder_name)
            except Exception as e:
                print(f"⚠️ Error procesando fila {j + 1}: {str(e)}")
                continue

    async def _download_pdf(self, row_locator, row_data: dict, folder_path: str):
        try:
            print(f"  -> ✅ Coincidencia encontrada (Doc: {row_data['document']}). Descargando...")

            # CAMBIO: Obtener el primer link/botón de la fila (el ojo)
            await row_locator.get_by_role("link").first.click()

            await expect(self.page.get_by_role("heading", name="Detalle del documento")).to_be_visible()

            await self.page.locator(".pdf-icon-container").click()

            iframe_locator = self.page.locator("iframe")
            await expect(iframe_locator).to_be_visible()
            blob_url = await iframe_locator.get_attribute("src")

            base64_pdf_data = await self.page.evaluate(self.JS_BLOB_TO_BASE64, blob_url)
            pdf_bytes = base64.b64decode(base64_pdf_data)

            file_name = f"documento_{row_data['document']}_{row_data['cross_reference_doc']}.pdf"

            # Save to S3 or local based on environment
            if self.app_env == "production":
                s3_url = await self.s3_uploader.upload_file_to_s3(pdf_bytes, file_name, os.path.basename(folder_path))
                self.downloaded_pdfs_summary.append({"centro": os.path.basename(folder_path), "archivo": file_name, "s3_url": s3_url})
            else:
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, "wb") as f:
                    f.write(pdf_bytes)
                print(f"  -> 📄 PDF guardado en: {file_path}")
                self.downloaded_pdfs_summary.append({"centro": os.path.basename(folder_path), "archivo": file_name})

            await self.page.get_by_role("button", name="Volver").click()
            await expect(self.page.get_by_role("heading", name="Detalle del documento")).to_be_visible()
            await self.page.go_back()
            await expect(self.page.locator("table.info-table")).to_be_visible()

        except Exception as e:
            print(f"❌ Error descargando PDF: {str(e)}")
            self.errors_summary.append({
                "tipo": "ERROR_DESCARGA_PDF",
                "centro": os.path.basename(folder_path),
                "documento": row_data['document'],
                "mensaje": str(e)
            })
            # Intentar volver a la tabla de documentos
            try:
                await self.page.go_back()
            except:
                pass

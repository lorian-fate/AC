


from playwright.sync_api import sync_playwright
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time




class Task1:

    LOGIN_URL = "https://wmediadores.mapfre.com/PortalMediadores_fe-web/#/login"



    def __init__(self):
        self.browser = None
        self.page = None
    

    def start_playwright(self, headless=True):
        """
        Inicia sync_playwright y abre navegador/context/page.
        Devuelve un dict con p, browser, context, page.
        """
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        return {"p": p, "browser": browser, "context": context, "page": page, "headless": headless}


    def stop_playwright(self, session):
        """
        Cierra browser y detiene p. session es el dict devuelto por start_playwright.
        """
        try:
            if session.get("browser"):
                session["browser"].close()
        except Exception:
            pass
        try:
            if session.get("p"):
                session["p"].stop()
        except Exception:
            pass
    
    
    def click_next_button(self, offer_frame, max_retries=3, wait_between=2500):
        """
        Pulsa de forma confiable el botón 'Siguiente >>' en el formulario principal (formDG).
        Reintenta si el clic no tiene efecto visible (sin cambio de contenido ni nuevos elementos).
        """

        print("\n➡️ Pulsando botón 'Siguiente >>'...")

        try:
            btn_next = offer_frame.locator("a#formDG\\:btnSiguiente")
            btn_next.wait_for(state="visible", timeout=8000)
        except Exception as e:
            print(f"❌ No se encontró el botón 'Siguiente >>': {e}")
            return {"success": False, "error": "Botón no visible"}

        for attempt in range(1, max_retries + 1):
            print(f"🔁 Intento {attempt}/{max_retries} de pulsar 'Siguiente'...")

            try:
                # Guardamos una referencia a algo estable antes del clic
                body_before = offer_frame.evaluate("document.body.innerHTML.length")

                # Intento de clic normal
                btn_next.click(force=True)
                offer_frame.wait_for_timeout(wait_between)

                # Verificamos si hubo cambio significativo
                body_after = offer_frame.evaluate("document.body.innerHTML.length")
                if abs(body_after - body_before) > 1000:
                    print("✅ Cambio detectado tras pulsar 'Siguiente'.")
                    return {"success": True}

                # Si no hubo cambio, intentamos un clic JS alternativo
                print("⚠️ Ningún cambio detectado. Probando clic JS alternativo...")
                offer_frame.evaluate(
                    """(btn) => btn.dispatchEvent(
                        new MouseEvent('click', { bubbles: true, cancelable: true })
                    )""",
                    btn_next.element_handle()
                )

                offer_frame.wait_for_timeout(wait_between)
                body_after_js = offer_frame.evaluate("document.body.innerHTML.length")
                if abs(body_after_js - body_before) > 1000:
                    print("✅ Cambio detectado tras clic JS.")
                    return {"success": True}

                # Detectar si se abrió algún modal confirmación / panel de limpieza
                modal_candidate = offer_frame.locator("div[id*='panelCambioClaveNavegacion'], div[id*='panelLimpiarPolizaPorDias']")
                if modal_candidate.count() > 0 and modal_candidate.first.is_visible():
                    print("🧩 Se abrió un modal de confirmación tras pulsar 'Siguiente'.")
                    return {"success": True, "modal_opened": True}

            except Exception as e:
                print(f"⚠️ Error en intento {attempt}: {e}")

        print("❌ No se logró avanzar tras pulsar 'Siguiente' varias veces.")
        return {"success": False, "error": "Sin efecto tras varios intentos"}


    def login_mapfre(self, page, username, password, wait_selector="a:has-text('Nueva producción')"):
        """
        Realiza el login usando la `page` proporcionada.
        Espera activamente a un selector que indique que la sesión está totalmente iniciada.
        Devuelve {'success': bool, 'screenshot': str, 'page': page}.
        """
        page.goto(self.LOGIN_URL, timeout=4000000)

        # Rellenar formulario de login
        page.fill("input[name='nuuma']", username)
        page.fill("input[name='contrasena']", password)
        page.click("button[class='btn btn-red ng-scope ng-binding']")

        # Esperar que la sesión esté establecida: preferimos esperar un selector del menú
        login_success = False
        screenshot = "login_result.png"
        try:
            # Primero esperar navegación/recarga
            page.wait_for_load_state("networkidle", timeout=30000)
            # Luego esperar un selector visible que solo aparece cuando está autenticado
            page.wait_for_selector(wait_selector, timeout=30000)
            login_success = True
        except Exception:
            # Fallback: intentar esperar un poco más por navegación completa
            try:
                page.wait_for_load_state("load", timeout=30000)
                page.wait_for_timeout(2000)
                # si aún no hay selector, considerarlo fallido
            except Exception:
                pass

        # Captura de pantalla del estado tras el intento
        try:
            page.screenshot(path=screenshot, full_page=True)
        except Exception:
            pass

        return {"success": login_success, "screenshot": screenshot, "page": page}


    def open_new_production_menu(self, page):
        """
        Abre el menú desplegable 'Nueva producción'.
        Retorna True si se abre correctamente.
        """
        try:
            menu = page.locator("a", has_text="Nueva producción")
            menu.wait_for(state="visible", timeout=5000)
            menu.click(force=True)
            print("✅ Menú 'Nueva producción' abierto correctamente.")
            return {"success": True}
        except Exception as e:
            print(f"❌ Error al abrir el menú 'Nueva producción': {e}")
            screenshot = "menu_new_production_error.png"
            try:
                page.screenshot(path=screenshot, full_page=True)
            except Exception:
                pass
            return {"success": False, "error": str(e), "screenshot": screenshot}


    def go_to_wealth(self, page, context=None):
        """
        Navega desde el menú 'Nueva producción' hacia 'Patrimoniales' (Wealth).
        Cierra el menú desplegable tras el clic para evitar que quede superpuesto.
        """
        try:
            # 1️⃣ Asegurar que el menú 'Nueva producción' está visible
            menu = page.locator("a", has_text="Nueva producción")
            menu.wait_for(state="visible", timeout=5000)
            menu.hover()
            page.wait_for_timeout(500)  # breve pausa para que el submenú aparezca

            # 2️⃣ Localizar el enlace 'Patrimoniales'
            sub_locator = page.locator("a[href*='aplicaciones-externas/patrimoniales']")
            sub_locator.wait_for(state="visible", timeout=5000)
            print("✅ Enlace 'Patrimoniales' localizado. Haciendo clic...")

            # 3️⃣ Clic y esperar la navegación
            with page.expect_navigation(wait_until="load", timeout=10000):
                sub_locator.click(force=True)

            # 4️⃣ Intentar cerrar el menú si sigue abierto
            page.evaluate("""
                const menu = document.querySelector('ul.dropdown-menu');
                if (menu) menu.style.display = 'none';
                const overlay = document.querySelector('.menu-overlay');
                if (overlay) overlay.style.display = 'none';
            """)
            page.wait_for_timeout(300)

            # 5️⃣ Confirmar que la nueva página está cargada
            page.wait_for_load_state("networkidle", timeout=5000)
            print("✅ Navegación a 'Patrimoniales' completada correctamente.")

            screenshot = "wealth_section.png"
            #time.sleep(20)
            try:
                page.screenshot(path=screenshot, full_page=True)
            except Exception:
                pass

            return {"success": True, "screenshot": screenshot, "page": page}

        except Exception as e:
            print(f"❌ Error al acceder a 'Patrimoniales': {e}")
            screenshot = "wealth_error.png"
            try:
                page.screenshot(path=screenshot, full_page=True)
            except Exception:
                pass
            return {"success": False, "screenshot": screenshot, "error": str(e)}


    def open_communities_tarification(self, page, context, max_retries=3):
        """
        Abre la ventana 'Tarificación y emisión' dentro de 'Comunidades'.
        Detecta tanto popups nuevos como pestañas reusadas (misma sesión NSE).
        """

        print("Buscando categoría 'Comunidades'...")
        community_block = page.locator("div.cards-np:has(h2:has-text('Comunidades'))")
        community_block.wait_for(state="visible", timeout=7000)

        target_div = community_block.locator("div.card-link:has(p:has-text('Tarificación y emisión'))")
        target_div.wait_for(state="visible", timeout=7000)

        popup = None
        last_error = None

        for attempt in range(1, max_retries + 1):
            print(f"\n🟢 Intento {attempt}/{max_retries}: abriendo popup...")

            existing_pages = list(context.pages)
            try:
                target_div.scroll_into_view_if_needed()
                target_div.hover()
                page.wait_for_timeout(500)
                target_div.click(force=True)
                page.wait_for_timeout(5000)  # permitir carga inicial
                time.sleep(3)

                # Buscar páginas candidatas
                new_or_updated = []
                for p in context.pages:
                    if p not in existing_pages:
                        new_or_updated.append(p)
                    else:
                        try:
                            url = p.url or ""
                            title = p.title() or ""
                            if "EVT21_NSE_FWEB" in url and "inicio.jsp" in url:
                                new_or_updated.append(p)
                        except Exception:
                            continue

                if not new_or_updated:
                    print("⚠️  No se detectaron nuevas páginas; reintentando...")
                    continue

                # Seleccionar la página adecuada
                for p in new_or_updated:
                    try:
                        if "NUEVO SISTEMA DE EMISIÓN" in p.title():
                            popup = p
                            break
                    except Exception:
                        continue

                if popup is None and new_or_updated:
                    popup = new_or_updated[-1]

                if popup is None:
                    print("⚠️  Ninguna página coincide con el popup esperado.")
                    continue

                popup.wait_for_load_state("domcontentloaded", timeout=10000)
                print(f"✅ Popup detectado: title='{popup.title()}' url='{popup.url}'")
                break

            except Exception as e:
                last_error = e
                print(f"❌ Error en intento {attempt}: {e}")
                page.wait_for_timeout(2000)

        if popup is None:
            screenshot = "tarificacion_failed.png"
            page.screenshot(path=screenshot, full_page=True)
            print("❌ No se logró abrir el popup tras varios intentos.")
            return {"success": False, "error": str(last_error), "screenshot": screenshot}

        # Captura de comprobación
        screenshot = "tarificacion_popup.png"
        try:
            popup.screenshot(path=screenshot, full_page=True)
        except Exception:
            pass

        return {"success": True, "popup": popup, "screenshot": screenshot}
    

    def open_offer_contracting(self, popup, context, max_wait=15000):
        """
        Navega dentro del popup 'NUEVO SISTEMA DE EMISIÓN' para abrir 'Oferta / Contratación'.
        Detecta si el contenido carga en un iframe o en una nueva pestaña.
        """

        print("\n🔍 Verificando que el popup esté listo...")
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=max_wait)
        except Exception as e:
            print(f"⚠️ El popup no terminó de cargar a tiempo: {e}")

        # Asegurar que el contenedor principal del popup existe
        print("📂 Buscando el contenedor principal del popup...")
        try:
            popup.locator("div.container").wait_for(state="visible", timeout=max_wait)
        except Exception:
            print("⚠️ No se encontró el contenedor principal, continuando de todos modos...")

        # Intentar localizar el enlace "Oferta / Contratación"
        print("🧭 Buscando enlace 'Oferta / Contratación' dentro del popup...")
        link = None
        try:
            link = popup.locator("a:has-text('Oferta / Contratación')")
            link.wait_for(state="visible", timeout=max_wait)
            print("✅ Enlace encontrado dentro del popup.")
        except Exception:
            print("⚠️ No se encontró el enlace visible directamente. Intentando buscar por href...")
            try:
                link = popup.locator("a[href*='cargaOperacion']")
                link.wait_for(state="visible", timeout=max_wait)
                print("✅ Enlace encontrado mediante href.")
            except Exception as e:
                print(f"❌ No se pudo localizar el enlace 'Oferta / Contratación': {e}")
                return {"success": False, "error": "No se encontró el enlace 'Oferta / Contratación'."}

        # Intentar hacer clic en el enlace
        print("🖱️ Haciendo clic en 'Oferta / Contratación'...")
        link.scroll_into_view_if_needed()
        link.click(force=True)
        popup.wait_for_timeout(2000)

        # Verificar si se cargó dentro de un iframe
        print("🧩 Verificando si se cargó contenido dentro del iframe #ARQOS_MC...")
        target_frame = None
        try:
            popup.locator("iframe#ARQOS_MC").wait_for(state="visible", timeout=10000)
            target_frame = popup.frame(name="ARQOS_MC")
            print("✅ Contenido detectado dentro del iframe ARQOS_MC.")
        except Exception:
            print("⚠️ No se encontró el iframe ARQOS_MC visible. Verificando si se abrió una nueva pestaña...")

        # Si no hay iframe, revisar si se abrió una nueva pestaña
        offer_page = None
        if target_frame is None:
            try:
                # Buscar página con URL de cargaOperacion
                for p in context.pages:
                    if "cargaOperacion" in p.url:
                        offer_page = p
                        break
                if offer_page:
                    offer_page.wait_for_load_state("domcontentloaded", timeout=10000)
                    print(f"✅ Nueva pestaña detectada: {offer_page.url}")
            except Exception as e:
                print(f"⚠️ No se detectó nueva pestaña: {e}")

        # Determinar el contexto activo
        if target_frame:
            print("📄 Navegación completada dentro del iframe.")
            return {"success": True, "context": "iframe", "frame": target_frame}
        elif offer_page:
            print("📄 Navegación completada en nueva pestaña.")
            return {"success": True, "context": "page", "page": offer_page}
        else:
            print("❌ No se logró detectar el contenido final tras el clic.")
            return {"success": False, "error": "No se encontró contenido tras el clic."}


    def click_page_three_in_offer(self, offer_frame, max_wait=8000):
        """
        Dentro del iframe 'ARQOS_MC', hace clic en el enlace '3'
        (paginación) y confirma que la acción se ejecuta correctamente.
        """

        print("\n🔢 Buscando el enlace de paginación '3' dentro del iframe...")

        try:
            # Intentar localizar el enlace exacto con href JS
            link3 = offer_frame.locator("a[href*='saveSelectedRows(3)']")
            link3.wait_for(state="visible", timeout=max_wait)
            print("✅ Enlace '3' encontrado.")
        except Exception as e:
            print(f"❌ No se encontró el enlace '3': {e}")
            return {"success": False, "error": "No se encontró el enlace '3' en la paginación."}

        try:
            # Simular clic directo
            print("🖱️ Haciendo clic en el enlace '3'...")
            link3.scroll_into_view_if_needed()
            link3.click(force=True)
            offer_frame.wait_for_timeout(2000)

            # Verificar que el clic tuvo efecto
            # (por ejemplo, que el enlace '3' cambie de estilo a 'selectedPage')
            try:
                selected = offer_frame.locator("a.selectedPage:has-text('3')")
                selected.wait_for(state="visible", timeout=5000)
                print("✅ La página '3' está ahora seleccionada.")
            except Exception:
                print("⚠️ No se detectó cambio visual, pero el clic fue ejecutado.")

            return {"success": True}

        except Exception as e:
            print(f"❌ Error al hacer clic en '3': {e}")
            return {"success": False, "error": str(e)}


    def select_product_and_click_next(self, offer_frame, max_wait=8000):
        """
        Dentro del iframe 'ARQOS_MC':
        1️⃣ Selecciona el radio correspondiente al producto deseado.
        2️⃣ Hace clic en el botón 'Siguiente' y espera que se ejecute la acción AJAX.
        """

        print("\n✅ Iniciando selección de producto y avance al siguiente paso...")

        # --- Paso 1: Seleccionar el radio/checkbox ---
        try:
            print("🔘 Buscando el radio button del producto...")
            radio = offer_frame.locator("input[type='radio'][id*='tProductosComerciales_radio_grupo_-1_fila_5']")
            radio.wait_for(state="visible", timeout=max_wait)
            print("✅ Radio button encontrado. Seleccionando producto...")

            radio.scroll_into_view_if_needed()
            radio.click(force=True)
            offer_frame.wait_for_timeout(1000)

            # Verificamos que el radio esté marcado
            if radio.is_checked():
                print("☑️ Producto seleccionado correctamente.")
            else:
                print("⚠️ El radio no aparece marcado, pero se hizo clic.")
        except Exception as e:
            print(f"❌ Error al seleccionar el producto: {e}")
            return {"success": False, "error": "No se pudo seleccionar el radio button."}

        # --- Paso 2: Click en el botón “Siguiente” ---
        try:
            print("\n➡️ Buscando botón 'Siguiente'...")
            siguiente = offer_frame.locator("a#formProductos\\:btnSiguiente")
            siguiente.wait_for(state="visible", timeout=max_wait)
            print("✅ Botón 'Siguiente' encontrado. Haciendo clic...")

            siguiente.scroll_into_view_if_needed()
            siguiente.click(force=True)

            # Esperar a que la acción AJAX complete (simulamos con un pequeño delay)
            offer_frame.wait_for_timeout(4000)

            # Verificar si cambia algo en la interfaz (opcional)
            print("🔄 Esperando posible cambio de panel tras clic en 'Siguiente'...")
            offer_frame.wait_for_load_state("domcontentloaded", timeout=8000)

            print("✅ Acción de 'Siguiente' ejecutada correctamente.")
            return {"success": True}

        except Exception as e:
            print(f"❌ Error al hacer clic en 'Siguiente': {e}")
            return {"success": False, "error": str(e)}
    

    def click_open_agent_modal(self, offer_frame, max_wait=8000):
        """
        Hace clic en la lupa para abrir el modal de búsqueda de agentes.
        Espera específicamente a que el contenedor de contenido ('#panelBusquedaAgentesContentDiv') sea visible.
        """
        print("\n🔍 Intentando abrir el modal de búsqueda de agentes...")

        try:
            lupa = offer_frame.locator("a#formDG\\:btnAbrirModalAgente img#formDG\\:imagenLupaAgentes")
            lupa.wait_for(state="visible", timeout=max_wait)
            print("✅ Lupa encontrada. Haciendo clic...")

            lupa.scroll_into_view_if_needed()
            lupa.click(force=True)
            time.sleep(3)
            print("🕒 Esperando a que el modal se abra...")

            # Esperamos al contenedor de contenido del modal
            modal = offer_frame.locator("div#panelBusquedaAgentesContentDiv")
            modal.wait_for(state="visible", timeout=max_wait)

            print("✅ Modal de búsqueda de agentes abierto correctamente.")
            return {"success": True, "modal": modal}

        except Exception as e:
            print(f"❌ Error al abrir el modal de búsqueda de agentes: {e}")
            return {"success": False, "error": str(e)}
        
    
    def confirm_agent_modal(self, offer_frame, max_wait=10000):
        """
        Dentro del modal de búsqueda de agentes:
        - Hace clic en 'Buscar'
        - Espera unos segundos
        - Hace clic en 'Aceptar'
        - Confirma que el modal se haya cerrado y el campo de agente se haya rellenado
        """

        print("\n🔍 Confirmando búsqueda de agentes dentro del modal...")

        try:
            # 1️⃣ Verificar que el modal está visible
            modal = offer_frame.locator("div#panelBusquedaAgentesContentDiv")
            modal.wait_for(state="visible", timeout=max_wait)
            print("✅ Modal detectado y visible.")

            # 2️⃣ Clic en 'Buscar'
            buscar_btn = offer_frame.locator("a#formAgentes\\:btnBuscar")
            buscar_btn.wait_for(state="visible", timeout=max_wait)
            print("🖱️ Haciendo clic en 'Buscar'...")
            buscar_btn.click(force=True)
            time.sleep(3)

            # 3️⃣ Esperar un momento a que AJAX procese resultados
            offer_frame.wait_for_timeout(3000)

            # 4️⃣ Clic en 'Aceptar'
            aceptar_btn = offer_frame.locator("a#formAgentes\\:btnAceptar")
            aceptar_btn.wait_for(state="visible", timeout=max_wait)
            print("🖱️ Haciendo clic en 'Aceptar'...")
            aceptar_btn.click(force=True)

            # 5️⃣ Esperar cierre del modal o actualización del campo agente
            print("🕒 Esperando cierre del modal o actualización del campo agente...")

            # Esperamos primero a que el modal se oculte (puede fallar si sigue visible)
            try:
                modal.wait_for(state="hidden", timeout=8000)
                print("✅ Modal cerrado correctamente.")
            except Exception:
                print("⚠️ El modal sigue visible, intentando verificar por campo de agente...")

            # Verificar que el campo de agente se haya rellenado
            agent_field = offer_frame.locator("#formDG\\:keyAgentecomboboxField")
            agent_field.wait_for(state="visible", timeout=max_wait)
            value = agent_field.input_value() if agent_field else ""
            if value.strip():
                print(f"✅ Agente asignado correctamente: {value}")
            else:
                print("⚠️ No se detectó valor en el campo del agente (puede ser un retardo AJAX).")

            return {"success": True}

        except Exception as e:
            print(f"❌ Error interactuando con el modal: {e}")
            return {"success": False, "error": str(e)}
        

    def open_location_modal(self, offer_frame, max_wait=10000):
        """
        Abre el modal de 'Localidad de firma' intentando distintos métodos de clic.
        Compatible con botones AJAX RichFaces que no responden al click directo.
        """
        print("\n📍 Abriendo modal de 'Localidad de firma'...")

        try:
            # 1️⃣ Buscar el botón principal (lupa)
            lupa_btn = offer_frame.locator("a#formDG\\:btnAbrirModalLocalidadFirma")
            lupa_btn.wait_for(state="visible", timeout=max_wait)
            print("🖱️ Intentando clic normal en la lupa...")
            lupa_btn.click(force=True)

            # 2️⃣ Esperar un breve tiempo para ver si se abre el modal
            offer_frame.wait_for_timeout(1500)
            modal = offer_frame.locator("div#panelLocalidadFirmaContentDiv")
            if modal.is_visible():
                print("✅ Modal de localidad de firma abierto correctamente (clic normal).")
                return {"success": True}

            # 3️⃣ Si no se abrió, intentar clic via JS dispatch_event
            print("⚠️ Modal no se abrió con clic normal. Intentando dispatch_event...")
            offer_frame.evaluate("""
                (btn) => {
                    btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                }
            """, lupa_btn.element_handle())
            offer_frame.wait_for_timeout(2000)
            if modal.is_visible():
                print("✅ Modal de localidad de firma abierto (dispatch_event).")
                return {"success": True}

            # 4️⃣ Intento alternativo con el botón oculto
            alt_btn = offer_frame.locator("a#formDG\\:btnCargaLocalidadFirmaSuscriptor")
            if alt_btn.count() > 0:
                print("⚙️ Intentando con botón alternativo (btnCargaLocalidadFirmaSuscriptor)...")
                try:
                    alt_btn.first.click(force=True)
                    offer_frame.wait_for_timeout(2000)
                    if modal.is_visible():
                        print("✅ Modal abierto correctamente con el botón alternativo.")
                        return {"success": True}
                except Exception:
                    pass

            # 5️⃣ Si no se abrió el modal
            print("❌ No se logró abrir el modal de localidad de firma.")
            return {"success": False, "error": "No se detectó apertura del modal"}

        except Exception as e:
            print(f"❌ Error al abrir el modal de localidad de firma: {e}")
            return {"success": False, "error": str(e)}


    def select_location_by_zip(self, offer_frame, postal_code: str, max_wait=10000):
        """
        Dentro del modal 'Localidad de Firma':
        - Introduce el código postal (simulando tecleo para activar botón).
        - Clic en Buscar.
        - Espera resultados.
        - Clic en Aceptar.
        - Espera al cierre del modal.
        """
        print(f"\n📬 Buscando localidad por código postal: {postal_code}...")

        try:
            # 1️⃣ Asegurar que el modal está visible
            modal = offer_frame.locator("div#panelLocalidadFirmaContentDiv")
            modal.wait_for(state="visible", timeout=max_wait)
            print("✅ Modal visible.")

            # 2️⃣ Localizar el input del código postal
            postal_input = offer_frame.locator("#localidadFirma\\:codPostal")
            postal_input.wait_for(state="visible", timeout=max_wait)
            postal_input.click()
            postal_input.fill("")  # limpiar antes por si acaso
            time.sleep(3)
            postal_input.type(postal_code, delay=100)  # simular tecleo humano
            print(f"📮 Código postal '{postal_code}' escrito (con eventos de teclado simulados).")

            # 🔁 Forzar manualmente el evento keyup en el input (por si la lógica JS no se activa sola)
            offer_frame.evaluate(
                """(selector) => {
                    const el = document.querySelector(selector);
                    if (el) {
                        const evt = new KeyboardEvent('keyup', {bubbles: true, cancelable: true});
                        el.dispatchEvent(evt);
                    }
                }""",
                "#localidadFirma\\:codPostal"
            )

            offer_frame.wait_for_timeout(500)  # pequeña espera

            # 3️⃣ Hacer clic en Buscar
            buscar_btn = offer_frame.locator("a#localidadFirma\\:btnBuscar")
            buscar_btn.wait_for(state="visible", timeout=max_wait)
            print("🖱️ Haciendo clic en 'Buscar'...")
            buscar_btn.click(force=True)

            # 4️⃣ Esperar resultados
            offer_frame.wait_for_timeout(3000)
            print("⌛ Esperando resultados...")

            # 5️⃣ Hacer clic en Aceptar
            aceptar_btn = offer_frame.locator("a#localidadFirma\\:btnAceptar")
            aceptar_btn.wait_for(state="visible", timeout=max_wait)
            print("🖱️ Haciendo clic en 'Aceptar'...")
            aceptar_btn.click(force=True)

            # 6️⃣ Esperar a que el modal se cierre
            print("🕒 Esperando a que el modal se cierre...")
            modal.wait_for(state="hidden", timeout=10000)
            print("✅ Modal cerrado correctamente. Localidad seleccionada.")

            return {"success": True}

        except Exception as e:
            print(f"❌ Error en la selección de localidad: {e}")
            return {"success": False, "error": str(e)}

































        """
        Accede al enlace 'Tarificación y emisión' dentro de la categoría 'Comunidades' en Wealth.
        Esta acción abre una ventana emergente (popup).
        """
        try:
            # Esperar que la página de Wealth cargue completamente
            page.wait_for_load_state("networkidle", timeout=20000)
            print("Página Wealth cargada. Buscando 'Comunidades'...")

            # Localizar la sección "Comunidades"
            comunidades_section = page.locator("h2:has-text('Comunidades')")
            comunidades_section.wait_for(state="visible", timeout=10000)

            # Buscar el enlace 'Tarificación y emisión' dentro de la sección
            target_locator = comunidades_section.locator(
                "xpath=following-sibling::div//p[normalize-space(text())='Tarificación y emisión']"
            )
            target_locator.wait_for(state="visible", timeout=10000)
            print("Enlace 'Tarificación y emisión' dentro de 'Comunidades' localizado.")

            # Preparar listener para nueva ventana emergente
            popup_future = context.wait_for_event("page", timeout=15000)

            # Hacer clic (sin bloque 'with')
            target_locator.click(force=True)
            print("Click ejecutado, esperando popup...")

            # Esperar que se abra la ventana emergente
            new_page = popup_future.value
            new_page.wait_for_load_state("load", timeout=20000)

            # Capturar evidencia
            screenshot = "tarificacion_emision_popup.png"
            try:
                new_page.screenshot(path=screenshot, full_page=True)
            except Exception:
                pass

            print("✅ Ventana emergente 'Tarificación y emisión (Comunidades)' abierta correctamente.")
            return {"success": True, "screenshot": screenshot, "page": new_page}

        except Exception as e:
            print(f"⚠️ Error al acceder a 'Tarificación y emisión (Comunidades)': {e}")
            screenshot = "tarificacion_emision_error.png"
            try:
                page.screenshot(path=screenshot, full_page=True)
            except Exception:
                pass
            return {"success": False, "error": str(e), "screenshot": screenshot}
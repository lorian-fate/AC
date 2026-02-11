# requirements: flask, playwright
# instalar navegadores: playwright install

from multiprocessing import context
from playwright.sync_api import sync_playwright
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError



# URL base (ejemplo de login Mapfre)
#LOGIN_URL = "https://micuenta.mapfre.es/oauth2/default/v1/authorize?client_id=0oac9sd7okFbaB60z417&code_challenge=UCriTfkP9vO1d0L0QAtC4KmJken7nCkrcp0sxt9Db0A&code_challenge_method=S256&nonce=MHFY2dM4OE89g5SDM0KvY2vEBrx4essf9NTNAeGiMBzRcAJCxrdtfRYlLI37sWdD&redirect_uri=https%3A%2F%2Fareadeclientes.mapfre.es%2Flogin%2Fparticulares%2Fcallback&response_type=code&state=ZVNuoFjAlE7BvBXg9WYyjRDd6ekXzbhQatGSUcu5DAcfcZqiPoBXpaQKvleQu35p&scope=email%20profile%20openid&id_operacion=5&app_version=14.3.5"

#LOGIN_URL = "https://mercadona.avature.net/es_ES/Careers/Login"
LOGIN_URL = "https://wmediadores.mapfre.com/PortalMediadores_fe-web/#/login"
#LOGOUT_URL = "https://areadeclientes.mapfre.es/logout"  # Ejemplo, ajustar si cambia

# --- Nuevas utilidades: gestionar Playwright fuera de las funciones de acción ---
def start_playwright(headless=False):
    """
    Inicia sync_playwright y abre navegador/context/page.
    Devuelve un dict con p, browser, context, page.
    """
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    return {"p": p, "browser": browser, "context": context, "page": page, "headless": headless}


def stop_playwright(session):
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

# --- Funciones core (ajustadas para recibir page/context externos) ---
def login_mapfreFunciona(page, username, password):
    """
    Versión rápida que usa una page ya creada por start_playwright.
    Realiza login, toma screenshot y cierra NO la sesión (no cierra browser).
    """
    page.goto(LOGIN_URL, timeout=4000000)

    # Rellenar formulario de login
    page.fill("input[name='nuuma']", username)
    page.fill("input[name='contrasena']", password)
    page.click("button[class='btn btn-red ng-scope ng-binding']")

    # Esperar redirección o algún elemento de la página privada
    try:
        page.wait_for_url("**/areadeclientes.mapfre.es/**", timeout=650000)
        login_success = True
    except:
        login_success = False

    # Tomar captura para verificar
    screenshot = "login_result.png"
    page.screenshot(path=screenshot, full_page=True)

    return {"success": login_success, "screenshot": screenshot}

def login_mapfre(page, username, password, wait_selector="a:has-text('Nueva producción')"):
    """
    Realiza el login usando la `page` proporcionada.
    Espera activamente a un selector que indique que la sesión está totalmente iniciada.
    Devuelve {'success': bool, 'screenshot': str, 'page': page}.
    """
    page.goto(LOGIN_URL, timeout=4000000)

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


def go_to_wealthFunciona(page, context=None):
    """
    Navega al enlace 'Wealth' del menú desplegable.
    - Usa Playwright locators y esperas explícitas.
    - Asume que la navegación ocurre en la misma pestaña.
    """
    try:
        # Abrir el menú "Nueva producción"
        menu = page.locator("a", has_text="Nueva producción")
        menu.wait_for(state="visible", timeout=5000)
        menu.click(force=True)
        print("Menú 'Nueva producción' abierto. Esperando enlace 'Wealth'...")

        # Esperar a que aparezca el subenlace "Patrimoniales"
        sub_locator = page.locator("a[href*='aplicaciones-externas/patrimoniales']")
        sub_locator.wait_for(state="visible", timeout=5000)

        print("Enlace 'Wealth' localizado. Haciendo clic...")
        # Click y esperar navegación en la misma pestaña
        with page.expect_navigation(wait_until="load", timeout=10000):
            sub_locator.click(force=True)

        # Esperar a que la página cargue completamente
        page.wait_for_load_state("networkidle", timeout=5000)
        screenshot = "wealth_section.png"
        try:
            page.screenshot(path=screenshot, full_page=True)
        except Exception:
            pass
        print("Navegación a 'Wealth' completada correctamente.")
        return {"success": True, "screenshot": screenshot, "page": page}

    except Exception as e:
        print(f"Error al acceder a Wealth: {e}")
        screenshot = "wealth_error.png"
        try:
            page.screenshot(path=screenshot, full_page=True)
        except Exception:
            pass
        return {"success": False, "screenshot": screenshot, "error": str(e)}


def open_new_production_menu(page):
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


def go_to_wealth(page, context=None):
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


def open_communities_tarificationKK(page, context, max_retries=3):
    """
    Abre de forma confiable la ventana 'Tarificación y emisión' dentro de 'Comunidades'.
    Reintenta clics si el popup no se abre a la primera.
    """

    print("Buscando categoría 'Comunidades'...")
    community_block = page.locator("div.cards-np:has(h2:has-text('Comunidades'))")
    community_block.wait_for(state="visible", timeout=7000)

    target_div = community_block.locator("div.card-link:has(p:has-text('Tarificación y emisión'))")
    target_div.wait_for(state="visible", timeout=7000)

    popup = None
    last_error = None

    for attempt in range(1, max_retries + 1):
        print(f"Intento {attempt} de {max_retries}: intentando abrir popup...")

        try:
            # Nos aseguramos de que Angular haya aplicado los bindings
            page.wait_for_timeout(1000)
            target_div.scroll_into_view_if_needed()
            target_div.hover()
            time.sleep(0.3)  # breve espera antes del clic

            with context.expect_page(timeout=8000) as popup_info:
                target_div.click(force=True)
            popup = popup_info.value
            popup.wait_for_load_state("domcontentloaded", timeout=10000)
            print("✅ Popup detectado correctamente.")
            break

        except Exception as e:
            print(f"⚠️  No se abrió el popup en el intento {attempt}: {e}")
            last_error = e

            # Intento alternativo: clic directo vía JS
            try:
                page.evaluate(
                    """el => el.click()""",
                    target_div.element_handle()
                )
                with context.expect_page(timeout=8000) as popup_info:
                    pass  # Esperar si se abre tras el clic JS
                popup = popup_info.value
                popup.wait_for_load_state("domcontentloaded", timeout=10000)
                print("✅ Popup detectado tras click JS.")
                break
            except Exception:
                print("❌ Click JS tampoco abrió popup. Reintentando...")
                page.wait_for_timeout(2000)

    if popup is None:
        screenshot = "tarificacion_failed.png"
        page.screenshot(path=screenshot, full_page=True)
        print("❌ No se logró abrir el popup tras varios intentos.")
        return {"success": False, "error": str(last_error), "screenshot": screenshot}

    # Captura del popup final
    screenshot = "tarificacion_popup.png"
    try:
        popup.screenshot(path=screenshot, full_page=True)
    except Exception:
        pass

    return {"success": True, "popup": popup, "screenshot": screenshot}


def open_communities_tarification(page, context, max_retries=3):
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
            time.sleep(5)

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


def open_offer_contracting(popup, context, max_wait=15000):
    """
    Navega dentro del popup 'NUEVO SISTEMA DE EMISIÓN' para abrir 'Oferta / Contratación'.
    Detecta si el contenido carga en un iframe o en una nueva pestaña.
    """

    print("\n🔍 Verificando que el popup esté listo...")
    time.sleep(5)  # breve espera inicial
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


def click_page_three_in_offer(offer_frame, max_wait=8000):
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


def select_product_and_click_next(offer_frame, max_wait=8000):
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


def click_open_agent_modal(offer_frame, max_wait=8000):
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


def confirm_agent_modal(offer_frame, max_wait=10000):
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




def open_location_modalOLD(offer_frame, max_wait=15000):
    """
    Abre el modal de 'Localidad de Firma' haciendo clic en la lupa correspondiente.
    Espera a que el modal esté completamente visible.
    """
    print("\n🏙️ Abriendo modal de 'Localidad de Firma'...")

    try:
        # 1️⃣ Click en la lupa
        lupa = offer_frame.locator("a#formDG\\:btnAbrirModalLocalidadFirma img#formDG\\:imagenLupaClientes")
        #lupa = offer_frame.locator("a#formDG\\:btnAbrirModalAgente img#formDG\\:imagenLupaAgentes")
        lupa.wait_for(state="visible", timeout=max_wait)
        
        lupa.scroll_into_view_if_needed()
        lupa.click(force=True)
        time.sleep(3)
        print("🖱️ Lupa de 'Localidad de Firma' clickeada, esperando apertura del modal...")

        # 2️⃣ Esperar que el modal aparezca
        modal = offer_frame.locator("div#panelLocalidadFirmaContentDiv")
        modal.wait_for(state="visible", timeout=max_wait)
        
        print("✅ Modal de 'Localidad de Firma' abierto correctamente.")
        return {"success": True}

    except Exception as e:
        print(f"❌ Error al abrir el modal de Localidad de Firma: {e}")
        return {"success": False, "error": str(e)}



def open_location_modal(offer_frame, max_wait=10000):
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





def select_location_by_zip(offer_frame, postal_code: str, max_wait=10000):
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




def click_next_button(offer_frame, max_retries=3, wait_between=2500):
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


def click_next_button_obj_aseg(offer_frame, wait_after=3000):
    """
    Pulsa el botón 'Siguiente >>' del formulario formObjAseg.
    En JSF, si el frame se destruye tras el clic, se considera ÉXITO.
    """

    print("\n➡️ Pulsando botón 'Siguiente >>' (formObjAseg)...")

    try:
        btn_next = offer_frame.locator("a#formObjAseg\\:btnSiguiente")
        btn_next.wait_for(state="visible", timeout=10000)
    except Exception as e:
        print(f"❌ No se encontró el botón 'Siguiente >>' (formObjAseg): {e}")
        return {"success": False, "error": "Botón no visible"}

    try:
        # Aseguramos foco
        btn_next.scroll_into_view_if_needed()
        btn_next.hover()
        offer_frame.wait_for_timeout(300)

        print("🔘 Clic en 'Siguiente >>'...")
        btn_next.click(force=True)

        # Si JSF navega, este contexto se destruirá → ÉXITO
        offer_frame.wait_for_timeout(wait_after)

        print("✅ Clic ejecutado, navegación JSF iniciada.")
        return {"success": True}

    except Exception as e:
        msg = str(e)

        # ESTE es el caso correcto
        if "Execution context was destroyed" in msg:
            print("✅ El frame se recargó tras pulsar 'Siguiente' (comportamiento esperado).")
            return {"success": True, "navigated": True}

        print(f"❌ Error inesperado al pulsar 'Siguiente': {e}")
        return {"success": False, "error": msg}




def open_cadastral_reference(offer_frame):
    print("📍 Abriendo modal de 'Referencia Catastral'...")

    BTN_SELECTOR = "#formObjAseg\\:btnAbrirModalRefCatastrales"

    MODAL_SELECTORS = [
        "div#panelInformacionCatastralContentDiv",
        "div#panelInformacionCatastralContainer",
        "div#panelInformacionCatastral",
        "div[id*='panelInformacionCatastral'][class*='content']",
        "div[id*='panelInformacionCatastral']"
    ]

    # 1) Click en botón
    try:
        print("🖱️ Haciendo clic en el botón 'Añadir Ref. Catastrales'...")
        btn = offer_frame.locator(BTN_SELECTOR)
        btn.wait_for(state="visible", timeout=8000)
        btn.click()
    except Exception as e:
        print(f"❌ No se pudo clicar el botón de referencias catastrales: {e}")
        return False

    # 2) Esperar modal
    print("⏳ Esperando a que se abra el modal 'Información Catastral'...")

    for selector in MODAL_SELECTORS:
        try:
            modal = offer_frame.locator(selector)
            modal.wait_for(state="visible", timeout=10000)
            print(f"✅ Modal de referencias catastrales detectado: {selector}")
            return True
        except:
            continue

    print("❌ No se logró detectar el modal de información catastral con ningún selector.")
    return False



def fill_cadastral_data(offer_frame, cp: str, via: str, numero: str, max_wait=10000):
    """
    Flujo completo para buscar y seleccionar referencia catastral dentro del modal:
      - cp: código postal (5 dígitos)
      - via: nombre de la vía (ej. 'RIO ERESMA')
      - numero: número del portal (ej. '1')
    Trabaja dentro del `offer_frame` (iframe ARQOS_MC).
    Devuelve dict con éxito y el municipio detectado.
    """

    def esc(selector: str) -> str:
        """Escapar ':' en selectores CSS"""
        return selector.replace(":", "\\:")

    try:
        print("📮 1) Introduciendo Código Postal:", cp)
        cp_sel = f"#{esc('formInformacionCatastral:codPostalCatastro')}"
        cp_input = offer_frame.locator(cp_sel)
        cp_input.wait_for(state="visible", timeout=max_wait)
        cp_input.fill(cp)
        # onchange hace un submit AJAX que pone foco en nombreVia; esperar un poco
        offer_frame.wait_for_timeout(1200)

        # Esperar que el select de municipio tenga opción seleccionada diferente / cargada
        municipio_sel = f"#{esc('formInformacionCatastral:localidadCatastro')}"
        print("⏳ Esperando que se cargue el municipio en", municipio_sel)
        # esperamos hasta que haya >0 opciones seleccionadas o hasta timeout
        offer_frame.wait_for_timeout(500)  # pequeña pausa inicial
        municipio = None
        try:
            # intentar varias veces porque el AJAX tarda
            for _ in range(int(max_wait / 500)):
                opts = offer_frame.locator(f"{municipio_sel} option[selected]")
                if opts.count() > 0:
                    municipio = opts.first.inner_text().strip()
                    break
                # fallback: si select value != "" y text present
                sel_elem = offer_frame.locator(municipio_sel)
                if sel_elem.count() > 0:
                    val = sel_elem.input_value().strip()
                    if val:
                        # obtener la opción seleccionada por atributo selected o por value
                        try:
                            sel_text = offer_frame.locator(f"{municipio_sel} option[value='{val}']").inner_text().strip()
                            municipio = sel_text
                            break
                        except Exception:
                            pass
                offer_frame.wait_for_timeout(500)
        except Exception:
            pass

        if not municipio:
            print("⚠️ No se detectó municipio seleccionado tras introducir CP; continuamos pero municipio queda vacío.")
            municipio = ""

        print(f"✅ Municipio detectado: '{municipio}'")

        # 2) Escribir nombre de Vía y seleccionar sugerencia
        print("✍️ 2) Introduciendo Nombre de Vía:", via)
        via_field_sel = f"#{esc('formInformacionCatastral:nombreViaCatastrocomboboxField')}"
        via_input = offer_frame.locator(via_field_sel)
        via_input.wait_for(state="visible", timeout=max_wait)
        # Limpiar y escribir poco a poco (disparar onkeyup y AJAX)
        via_input.fill("") 
        offer_frame.wait_for_timeout(200)
        via_input.type(via, delay=50)  # tipeo para disparar onkeyup

        # Esperar a que la lista de sugerencias se rellene y sea visible
        list_parent_sel = f"#{esc('formInformacionCatastral:nombreViaCatastrolistParent')}"
        list_sel = f"#{esc('formInformacionCatastral:nombreViaCatastrolist')}"
        # Dar tiempo para que RichFaces muestre la lista
        offer_frame.wait_for_timeout(800)
        # Esperar hasta que haya items
        items = None
        for _ in range(int(max_wait/500)):
            # contar hijos dentro del contenedor de la lista
            try:
                items_count = offer_frame.locator(f"{list_sel} >> xpath=.//*").count()
            except Exception:
                items_count = 0
            if items_count > 0:
                break
            offer_frame.wait_for_timeout(300)
        # intentar seleccionar item que contenga la vía (case-insensitive)
        print("🔎 Buscando sugerencia que coincida con la vía...")
        selected_suggestion = None
        try:
            suggestions = offer_frame.locator(f"{list_sel}").locator("xpath=.//*")
            count = suggestions.count()
            via_lower = via.lower()
            for i in range(count):
                try:
                    txt = suggestions.nth(i).inner_text().strip().lower()
                except Exception:
                    txt = ""
                if via_lower in txt:
                    suggestions.nth(i).click()
                    selected_suggestion = suggestions.nth(i)
                    break
            # si no encontró coincidencia, intenta el primer elemento disponible
            if selected_suggestion is None and count > 0:
                print("⚠️ No coincidencia exacta en sugerencias; seleccionando la primera sugerencia disponible.")
                suggestions.nth(0).click()
                selected_suggestion = suggestions.nth(0)
        except Exception as e:
            print("⚠️ No se pudieron leer/seleccionar las sugerencias:", e)

        offer_frame.wait_for_timeout(700)
        if selected_suggestion:
            print("✅ Sugerencia seleccionada.")
        else:
            print("⚠️ No se seleccionó ninguna sugerencia (no había items). Continuamos.")

        # 3) Introducir número de portal
        print("🔢 3) Introduciendo número de portal:", numero)
        numero_sel = f"#{esc('formInformacionCatastral:numeroViaCatastro')}"
        numero_input = offer_frame.locator(numero_sel)
        numero_input.wait_for(state="visible", timeout=max_wait)
        numero_input.fill(numero)
        offer_frame.wait_for_timeout(300)

        # 4) Pulsar Buscar
        print("🔎 4) Pulsando botón Buscar catastral...")
        buscar_sel = f"#{esc('formInformacionCatastral:btnBuscarCatastro')}"
        buscar_btn = offer_frame.locator(buscar_sel)
        buscar_btn.wait_for(state="visible", timeout=max_wait)
        buscar_btn.click(force=True)

        # 5) Esperar resultados (tabla de situaciones)
        print("⏳ Esperando resultados de búsqueda catastral...")
        # Los resultados aparecen en tbody.lmbTbody (según HTML)
        results_rows = offer_frame.locator("tbody.lmbTbody tr")
        # esperar a que existan filas con checkbox (filas de datos)
        found = False
        for _ in range(int(max_wait/500)):
            try:
                # contar filas que contienen input checkbox
                cnt = offer_frame.locator("tbody.lmbTbody tr input[type='checkbox']").count()
            except Exception:
                cnt = 0
            if cnt > 0:
                found = True
                break
            offer_frame.wait_for_timeout(500)
        if not found:
            print("❌ No se encontraron resultados tras la búsqueda.")
            return {"success": False, "error": "No se encontraron resultados tras la búsqueda catastral."}

        print("✅ Resultados encontrados. Procesando selección de la vía correcta...")

        # 6) Seleccionar las filas cuya descripción (segunda celda) contenga la vía (palabras)
        # Normalizar búsqueda: comprobar que todas las palabras de via aparecen en el texto del resultado
        via_words = [w.strip().lower() for w in via.split() if w.strip()]
        rows = offer_frame.locator("tbody.lmbTbody tr")
        rows_count = rows.count()
        matched_any = False
        for i in range(rows_count):
            try:
                row = rows.nth(i)
                # buscar la celda de texto (segundo td con la descripción)
                desc = ""
                try:
                    desc = row.locator("td").nth(1).inner_text().strip().lower()
                except Exception:
                    # fallback: todo el texto del row
                    desc = row.inner_text().strip().lower()
                # comprobar coincidencia por palabras
                is_match = all(w in desc for w in via_words) if via_words else False
                checkbox = row.locator("input[type='checkbox'], input[type='radio']")
                # Si es fila de datos (tiene checkbox)
                if checkbox.count() > 0:
                    if is_match:
                        matched_any = True
                        # marcar si no está marcado
                        try:
                            if not checkbox.first.is_checked():
                                checkbox.first.click(force=True)
                                offer_frame.wait_for_timeout(200)
                        except Exception:
                            # intentar click de la celda si checkbox falla
                            try:
                                row.locator("td").nth(0).click()
                            except Exception:
                                pass
                        print(f"  ✅ Marcada fila {i} con descripción: {desc}")
                    else:
                        # desmarcar si estuviera marcado
                        try:
                            if checkbox.first.is_checked():
                                checkbox.first.click(force=True)
                                offer_frame.wait_for_timeout(150)
                                print(f"  ℹ️ Deseleccionada fila {i} (no coincide): {desc}")
                        except Exception:
                            pass
            except Exception:
                continue

        if not matched_any:
            print("⚠️ No se encontró ninguna fila que coincidiera exactamente con la vía; seleccionando la primera fila por defecto.")
            try:
                first_checkbox = offer_frame.locator("tbody.lmbTbody tr input[type='checkbox']").first
                first_checkbox.click(force=True)
            except Exception:
                pass

        # 7) Pulsar "Aceptar Selección"
        aceptar_sel = f"#{esc('formInformacionCatastral:btnAceptarCatastro')}"
        print("🖱️ Pulsando 'Aceptar Selección'...")
        aceptar_btn = offer_frame.locator(aceptar_sel)
        aceptar_btn.wait_for(state="visible", timeout=max_wait)
        aceptar_btn.click(force=True)

        # 8) Esperar modal de localidades (panelLocalidadCatastro) y seleccionar municipio
        # identificar modal contenido: panelLocalidadCatastroContentDiv (seguimos patrón)
        panel_localidades_sel = f"div#panelLocalidadCatastroContentDiv"
        print("⏳ Esperando modal de localidades tras aceptar selección...")
        # Esperar a que el radio list aparezca (tabla tLocalidades)
        found_localidades = False
        for _ in range(int(max_wait/500)):
            try:
                # local radio rows
                rcount = offer_frame.locator("tr[id^='tLocalidades_pos']").count()
            except Exception:
                rcount = 0
            if rcount > 0:
                found_localidades = True
                break
            offer_frame.wait_for_timeout(500)

        if not found_localidades:
            print("⚠️ No se detectó el modal de localidades o no hay filas tLocalidades. Intentando esperar panel específico...")
            try:
                offer_frame.locator(panel_localidades_sel).wait_for(state="visible", timeout=5000)
                found_localidades = True
            except Exception:
                pass

        if not found_localidades:
            print("❌ No se abrió modal de localidades; no se puede continuar.")
            return {"success": False, "error": "No aparecieron localidades tras aceptar selección."}

        # seleccionar el radio que coincida con municipio almacenado
        print("🔎 Seleccionando localidad que coincida con el municipio:", municipio)
        radio_rows = offer_frame.locator("tr[id^='tLocalidades_pos']")
        rr_count = radio_rows.count()
        selected_locality = None
        municipio_lower = municipio.strip().lower()
        for i in range(rr_count):
            try:
                row = radio_rows.nth(i)
                cell_text = row.locator("td").nth(1).inner_text().strip().lower()
                if municipio_lower and municipio_lower in cell_text:
                    # click radio input
                    radio = row.locator("input[type='radio']")
                    if radio.count() > 0:
                        radio.first.click(force=True)
                        selected_locality = cell_text
                        print(f"  ✅ Seleccionada localidad: {cell_text}")
                        break
            except Exception:
                continue

        if not selected_locality:
            print("⚠️ No se encontró localidad que coincida exactamente con municipio. Seleccionando la primera radio disponible.")
            try:
                radio_rows.locator("input[type='radio']").first.click(force=True)
                selected_locality = radio_rows.locator("td").nth(1).first.inner_text().strip()
            except Exception:
                pass

        offer_frame.wait_for_timeout(700)

        # 9) Pulsar botón Aceptar del modal de localidades
        localidad_aceptar_sel = f"#{esc('localidadCatastro:btnAceptar')}"
        print("🖱️ Pulsando 'Aceptar' en modal de localidades...")
        aceptar_localidad_btn = offer_frame.locator(localidad_aceptar_sel)
        aceptar_localidad_btn.wait_for(state="visible", timeout=max_wait)
        aceptar_localidad_btn.click(force=True)

        # 10) Esperar cierre del modal principal de información catastral
        panel_informacion_sel = f"#{esc('panelInformacionCatastralContentDiv')}"
        print("⏳ Esperando cierre del panel de información catastral...")
        try:
            offer_frame.locator(panel_informacion_sel).wait_for(state="hidden", timeout=10000)
            print("✅ Modal catastral cerrado correctamente.")
        except Exception:
            print("⚠️ El panel de información catastral no se ocultó en el timeout; continuamos de todos modos.")

        return {"success": True, "municipio": municipio}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}



def open_gestion_clientes(offer_frame, timeout=10000):
    """
    Abre la ventana/modal 'Gestión Clientes' desde el formulario formFiguras.
    Detecta correctamente el modal RichFaces 'panelBusquedaClientes'.
    """

    print("\n➡️ Accediendo a 'Gestión Clientes'...")

    try:
        btn_gc = offer_frame.locator(
            "a#formFiguras\\:btnGestionClientesTomadorDP"
        )
        btn_gc.wait_for(state="visible", timeout=timeout)
    except Exception as e:
        print(f"❌ No se encontró el botón 'Gestión Clientes': {e}")
        return {"success": False, "error": "Botón no visible"}

    try:
        # Preparación del clic (muy importante en JSF)
        btn_gc.scroll_into_view_if_needed()
        btn_gc.hover()
        offer_frame.wait_for_timeout(300)

        print("🔘 Clic en 'Gestión Clientes'...")
        btn_gc.click(force=True)

        # Caso normal: se abre el modal RichFaces
        modal = offer_frame.locator("div#panelBusquedaClientes")

        try:
            modal.wait_for(state="visible", timeout=timeout)
            print("✅ Modal 'Gestión Clientes' abierto correctamente.")
            return {
                "success": True,
                "modal": "panelBusquedaClientes"
            }

        except Exception:
            # Caso JSF: el contexto se destruye antes de que podamos esperar
            print("ℹ️ No se pudo esperar directamente el modal, verificando contexto...")

            # Pequeña espera de estabilidad
            offer_frame.wait_for_timeout(2000)

            if offer_frame.locator("div#panelBusquedaClientes").count() > 0:
                print("✅ Modal 'Gestión Clientes' detectado tras recarga JSF.")
                return {
                    "success": True,
                    "modal": "panelBusquedaClientes",
                    "context_reloaded": True
                }

            raise Exception("El modal no apareció")

    except Exception as e:
        msg = str(e)

        # Tratamos navegación JSF como éxito si el modal aparece
        if "Execution context was destroyed" in msg:
            print("✅ Contexto recargado por JSF, verificando modal...")

            offer_frame.wait_for_timeout(2000)
            if offer_frame.locator("div#panelBusquedaClientes").count() > 0:
                print("✅ Modal 'Gestión Clientes' abierto correctamente.")
                return {
                    "success": True,
                    "modal": "panelBusquedaClientes",
                    "navigated": True
                }

        print(f"❌ Error al abrir 'Gestión Clientes': {e}")
        return {"success": False, "error": msg}



def search_juridical_client(
    offer_frame,
    razon_social: str,
    documento: str,
    timeout=10000
):
    """
    Busca un cliente jurídico en el modal Gestión Clientes.
    Devuelve True si hay resultados reales, False si no.
    """

    print("\n🔍 Buscando cliente jurídico...")

    # Seleccionar Jurídica
    radio = offer_frame.locator(
        "input#formClientes\\:tipoPersona\\:1"
    )
    radio.wait_for(state="attached", timeout=timeout)
    radio.check(force=True)

    # Rellenar Razón Social
    offer_frame.locator(
        "input#formClientes\\:razonSocial"
    ).fill(razon_social)

    # Rellenar Documento
    offer_frame.locator(
        "input#formClientes\\:numDoc"
    ).fill(documento)

    # Buscar
    offer_frame.locator(
        "a#formClientes\\:btnBuscar"
    ).click(force=True)

    # Esperar a que termine el AJAX
    offer_frame.wait_for_timeout(3000)

    # 🔍 Verificar contenido real en las filas
    rows = offer_frame.locator("tr[id^='tClientes_pos']")

    for i in range(rows.count()):
        row = rows.nth(i)

        # Obtener texto visible de la fila
        text = row.inner_text().strip()

        if text:
            print("✅ Cliente encontrado.")
            return True

    print("⚠️ Cliente no encontrado.")
    return False




def create_juridical_client(
    offer_frame,
    *,
    cp: str,
    localidad: str,
    tipo_via: str,
    nombre_via: str,
    numero: str = "",
    portal: str = "",
    escalera: str = "",
    piso: str = "",
    puerta: str = "",
    movil: str
):
    """
    Alta completa de cliente jurídico desde Gestión Clientes.
    """

    print("\n🆕 Alta de cliente jurídico...")

    # Botón Alta
    offer_frame.locator(
        "a#formClientes\\:btnAlta"
    ).click(force=True)

    # Esperar segundo modal
    #modal = offer_frame.locator("div#modalDetalleClientesTab")
    #modal.wait_for(state="visible", timeout=15000)

    offer_frame.locator("#formDetalleClientes\\:btnGuardar").wait_for(
        state="attached",
        timeout=15000
    )

    # Aceptar inicial
    offer_frame.locator(
        "a#formDetalleClientes\\:btnGuardar"
    ).click(force=True)

    offer_frame.wait_for_timeout(2000)

    # === DIRECCIONES ===
    offer_frame.locator(
        "td#formDetalleClientes\\:PestDirecciones_lbl"
    ).click()

    # Tipo dirección: Habitual
    offer_frame.select_option(
        "select#formDetalleClientes\\:tipoDireccion",
        value="1"
    )

    # Código Postal
    offer_frame.fill(
        "input#formDetalleClientes\\:codPostal",
        cp
    )
    offer_frame.wait_for_timeout(2000)

    # Localidad
    offer_frame.select_option(
        "select#formDetalleClientes\\:localidad",
        label=localidad
    )

    # Tipo vía
    offer_frame.select_option(
        "select#formDetalleClientes\\:tipoVia",
        label=tipo_via
    )

    # Nombre vía
    offer_frame.fill(
        "input#formDetalleClientes\\:nombreVia1",
        nombre_via
    )

    # Opcionales
    if numero:
        offer_frame.fill("input#formDetalleClientes\\:numero", numero)
    if portal:
        offer_frame.fill("input#formDetalleClientes\\:portal", portal)
    if escalera:
        offer_frame.fill("input#formDetalleClientes\\:escalera", escalera)
    if piso:
        offer_frame.fill("input#formDetalleClientes\\:piso", piso)
    if puerta:
        offer_frame.fill("input#formDetalleClientes\\:puerta", puerta)

    # Aceptar dirección
    offer_frame.locator(
        "span#formDetalleClientes\\:boton_aceptar_N"
    ).click()

    offer_frame.wait_for_timeout(2000)

    # === MEDIOS DE CONTACTO ===
    offer_frame.locator(
        "td#formDetalleClientes\\:PestMediosContacto_lbl"
    ).click()

    offer_frame.fill(
        "input#formDetalleClientes\\:movil1",
        movil
    )
    offer_frame.wait_for_timeout(2000)
    # 🔑 FORZAR BLUR REAL (como hace el usuario)
    offer_frame.locator("body").click(position={"x": 50, "y": 50})

    offer_frame.locator(
        "a#formDetalleClientes\\:btnAceptarMC"
    ).click(force=True)

    #offer_frame.locator("a#formDetalleClientes\\:btnAceptarMC").click()

    offer_frame.wait_for_timeout(2000)




    




    # Guardar cliente
    offer_frame.locator(
        "a#formDetalleClientes\\:btnAceptarDetalleCliente"
    ).click(force=True)

    offer_frame.wait_for_timeout(3000)

    # Seleccionar cliente (modal principal)
    offer_frame.locator(
        "a#formClientes\\:btnAceptar"
    ).click(force=True)

    print("✅ Cliente jurídico creado y seleccionado correctamente.")




















def search_or_create_cliente_juridico_____(
    offer_frame,
    razon_social,
    documento
):
    """
    Busca un cliente jurídico.
    Si no existe, inicia el flujo de Alta.
    """

    print("\n➡️ Gestión Clientes: búsqueda jurídica")

    # Seleccionar Jurídica
    radio_juridica = offer_frame.locator(
        "input#formClientes\\:tipoPersona\\:1"
    )
    radio_juridica.wait_for(state="visible", timeout=10000)
    radio_juridica.check(force=True)
    offer_frame.wait_for_timeout(1500)

    # Rellenar razón social
    offer_frame.locator(
        "input#formClientes\\:razonSocial"
    ).fill(razon_social)

    # Rellenar documento
    offer_frame.locator(
        "input#formClientes\\:numDoc"
    ).fill(documento)

    # Buscar
    btn_buscar = offer_frame.locator(
        "a#formClientes\\:btnBuscar"
    )
    btn_buscar.click(force=True)

    offer_frame.wait_for_timeout(2500)

    # Comprobar resultados
    filas = offer_frame.locator("tbody.lmbTbody tr")
    if filas.count() > 0:
        print("✅ Cliente encontrado, seleccionando...")
        filas.first.click(force=True)
        return {"success": True, "found": True}

    print("⚠️ Cliente no encontrado, iniciando alta...")
    offer_frame.locator(
        "a#formClientes\\:btnAlta"
    ).click(force=True)

    return {"success": True, "found": False, "alta": True}












def open_customer_management(offer_frame):
    """
    Abre el modal de Gestión de Clientes desde el offer_frame.
    """
    print("\n👥 Abriendo modal de 'Gestión de Clientes'...")

    BTN_SELECTOR = "#formFiguras\\:btnGestionClientesTomadorDP"

    MODAL_SELECTORS = [
        "div#panelInformacionCatastralContentDiv",
        "div#panelInformacionCatastralContainer",
        "div#panelInformacionCatastral",
        "div[id*='panelInformacionCatastral'][class*='content']",
        "div[id*='panelInformacionCatastral']"
    ]

    # 1) Click en botón
    try:
        print("🖱️ Haciendo clic en el botón 'Gestion clientes'...")
        btn = offer_frame.locator(BTN_SELECTOR)
        btn.wait_for(state="visible", timeout=8000)
        btn.click()
    except Exception as e:
        print(f"❌ No se pudo clicar el botón de referencias catastrales: {e}")
        return False

    # 2) Esperar modal
    """print("⏳ Esperando a que se abra el modal 'Información Catastral'...")

    for selector in MODAL_SELECTORS:
        try:
            modal = offer_frame.locator(selector)
            modal.wait_for(state="visible", timeout=10000)
            print(f"✅ Modal de referencias catastrales detectado: {selector}")
            return True
        except:
            continue

    print("❌ No se logró detectar el modal de información catastral con ningún selector.")"""
    return False


def manage_customer(
    offer_frame,
    tipo_cliente,  # 'Física' o 'Jurídica'
    num_doc,
    razon_social,
    cod_postal,
    provincia,
    localidad,
    tipo_via,
    nombre_via,
    numero_portal,
    movil
):
    """
    Gestiona un cliente dentro del modal de Gestión de Clientes.
    """

    # 1. Hacer click en "Gestión Clientes"
    offer_frame.find_element_by_id("formFiguras:btnGestionClientesTomadorDP").click()
    offer_frame.wait_for_element("formClientes:tipoPersona:1")  # Espera a que aparezca el modal

    # 2. Seleccionar tipo de cliente
    if tipo_cliente.lower() == "jurídica":
        offer_frame.find_element_by_id("formClientes:tipoPersona:1").click()
    else:
        offer_frame.find_element_by_id("formClientes:tipoPersona:0").click()
    
    # 3. Introducir número de documento y razón social
    offer_frame.find_element_by_id("formClientes:numDoc").send_keys(num_doc)
    offer_frame.find_element_by_id("formClientes:razonSocial").send_keys(razon_social)
    
    # 4. Pulsar "Buscar"
    offer_frame.find_element_by_id("formClientes:btnBuscar").click()
    offer_frame.wait_for_element("tClientes_1")  # Espera a que se cargue la tabla de clientes

    # 5. Seleccionar cliente o dar de alta
    tabla_clientes = offer_frame.find_elements_by_css_selector("#tClientes_1 tbody tr")
    if len(tabla_clientes) == 0 or all(cell.text.strip() == "" for cell in tabla_clientes[0].find_elements_by_tag_name("td")):
        # Si no hay resultados, pulsar "Alta"
        offer_frame.find_element_by_id("formClientes:btnAlta").click()
    else:
        # Si hay resultados, pulsar "Seleccionar"
        offer_frame.find_element_by_id("formClientes:btnAceptar").click()

    offer_frame.wait_for_element("formDetalleClientes:btnGuardar")  # Espera a que se abra el modal de detalle

    # 6. Pulsar botón "Aceptar" del nuevo modal
    offer_frame.find_element_by_id("formDetalleClientes:btnGuardar").click()
    offer_frame.wait_for_element("formDetalleClientes:PestDirecciones_lbl")  # Espera que aparezcan las pestañas internas

    # 7. Acceder a Direcciones
    offer_frame.find_element_by_id("formDetalleClientes:PestDirecciones_lbl").click()
    offer_frame.select_dropdown("formDetalleClientes:tipoDireccion", "HABITUAL", by_value=True)
    offer_frame.find_element_by_id("formDetalleClientes:codPostal").send_keys(cod_postal)
    
    offer_frame.wait_for_element("formDetalleClientes:provincia")
    offer_frame.select_dropdown("formDetalleClientes:provincia", provincia)
    offer_frame.select_dropdown("formDetalleClientes:localidad", localidad)
    offer_frame.select_dropdown("formDetalleClientes:tipoVia", tipo_via)
    
    # Nombre de la vía con selección de sugerencia
    nombre_input = offer_frame.find_element_by_id("formDetalleClientes:nombreVia1")
    nombre_input.send_keys(nombre_via)
    offer_frame.select_suggestion("formDetalleClientes:nombreVia1", nombre_via)
    
    offer_frame.find_element_by_id("formDetalleClientes:numero").send_keys(numero_portal)
    offer_frame.find_element_by_id("formDetalleClientes:btnGuardar").click()  # Aceptar direcciones

    # 8. Medios de contacto
    offer_frame.find_element_by_id("formDetalleClientes:PestMediosContacto_lbl").click()
    offer_frame.find_element_by_id("formDetalleClientes:movil").send_keys(movil)
    offer_frame.find_element_by_id("formDetalleClientes:btnGuardar").click()  # Aceptar medios de contacto

    # 9. Guardar todo y seleccionar cliente
    offer_frame.find_element_by_id("formDetalleClientes:btnGuardar").click()
    offer_frame.find_element_by_id("formClientes:btnAceptar").click()  # Seleccionar cliente final
   


def select_location_by_zipOLD(offer_frame, postal_code: str, max_wait=10000):
    """
    Dentro del modal 'Localidad de Firma':
    - Introduce el código postal.
    - Clic en Buscar.
    - Espera unos segundos.
    - Clic en Aceptar.
    - Confirma que el modal se haya cerrado correctamente.
    """
    print(f"\n📬 Buscando localidad por código postal: {postal_code}...")

    try:
        # 1️⃣ Esperar que el modal esté visible
        modal = offer_frame.locator("div#panelLocalidadFirmaContentDiv")
        modal.wait_for(state="visible", timeout=max_wait)
        print("✅ Modal visible.")

        # 2️⃣ Introducir código postal
        postal_input = offer_frame.locator("#localidadFirma\\:codPostal")
        postal_input.wait_for(state="visible", timeout=max_wait)
        postal_input.fill(postal_code)
        time.sleep(3)
        print(f"📮 Código postal '{postal_code}' ingresado correctamente.")

        # 3️⃣ Hacer clic en Buscar
        buscar_btn = offer_frame.locator("a#localidadFirma\\:btnBuscar")
        buscar_btn.wait_for(state="visible", timeout=max_wait)
        print("🖱️ Haciendo clic en 'Buscar'...")
        buscar_btn.click(force=True)

        # 4️⃣ Esperar unos segundos a que cargue resultados
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






def debug_list_links(popup):
    """
    Imprime todos los enlaces (<a>) detectados en el popup,
    mostrando su texto y href para diagnóstico.
    """
    try:
        links = popup.locator("a")
        count = links.count()
        print(f"🔍 Se detectaron {count} enlaces en el popup:")
        for i in range(count):
            href = links.nth(i).get_attribute("href")
            text = links.nth(i).inner_text().strip()
            print(f"  [{i}] texto='{text}'  href='{href}'")
    except Exception as e:
        print(f"❌ Error listando enlaces: {e}")


def debug_list_all_pages(context):
    print("\n📑 Páginas activas en el contexto:")
    for i, p in enumerate(context.pages):
        try:
            print(f"[{i}] title='{p.title()}' url='{p.url}'")
        except Exception:
            print(f"[{i}] (sin título aún)")






# --- Ejemplo de uso: gestionar Playwright fuera y ejecutar varias funciones ---
if __name__ == "__main__":
    #credentials = {"username": "GMRAFA3", "password": "tw7P(kg(@0,"}
    # H82883265 C. P. Encina 6
    credentials = {"username": "TAMARG3", "password": "+`4bBQ_6b"}

    currentPage = None

    # Iniciar playwright y abrir página
    session = start_playwright(headless=False)
    try:
        # Hacer login usando la page abierta
        login_result = login_mapfre(session["page"], credentials["username"], credentials["password"])
        if not login_result["success"]:
            print("❌ Error en el login. Captura:", login_result.get("screenshot"))
        else:
            print("✅ Login exitoso")

            result_menu = open_new_production_menu(session["page"])
            if result_menu["success"]:
                go_to_wealth(session["page"], session["context"])
                time.sleep(2.5)

                # Ejecutar acciones posteriores sobre la misma sesión
                #go_to_wealth(session["page"], session["context"])
                #time.sleep(15)

                result_popup = open_communities_tarification(session["page"], session["context"])
                #time.sleep(10)
                debug_list_all_pages(session["context"])
                if result_popup["success"]:

                    popup = result_popup["popup"]
                    debug_list_links(popup)

                    
                    print("✅ Ventana de Tarificación y emisión abierta correctamente.")
                    time.sleep(2.5)
                    #open_offer_contracting(popup, session["context"])

                    offer = open_offer_contracting(popup, session["context"])
                    if offer["success"] and offer["context"] == "iframe":
                        frame = offer["frame"]
                        time.sleep(5.5)
                        click_page_three_in_offer(frame)
                        select_product_and_click_next(frame)
                        # Ya estás dentro del iframe 'offer_frame' después de hacer clic en 'Siguiente'
                        result = click_open_agent_modal(frame)
                        if result["success"]:
                            confirm_agent_modal(frame)
                        result1 = open_location_modal(frame)
                        if result1["success"]:
                            select_location_by_zip(frame, "28913")
                            click_next_button(frame)
                        time.sleep(5.5)
                        result2 = open_cadastral_reference(frame)
                        if result2:
                            print("✅ Modal de referencias catastrales abierto correctamente.")
                            fill_cadastral_data(frame, cp="28913", via="RIO ERESMA", numero="1")
                            click_next_button_obj_aseg(frame)

                            result_gestion_clientes = open_gestion_clientes(frame)
                            if result_gestion_clientes["success"]:
                                found = search_juridical_client(frame, razon_social="C. P. Encina 6", documento="H82883265")
                                

                                if not found:
                                    create_juridical_client(
                                        frame,
                                        cp="28913",
                                        localidad="LEGANES",
                                        tipo_via="CL - CALLE",
                                        nombre_via="RIO ERESMA",
                                        numero="1",
                                        movil="600123456"
                                    )

                                print("✅ Modal de gestión de clientes abierto correctamente.")
                                # Aquí podrías llamar a funciones para interactuar con el modal de gestión de clientes
                            else:
                                print("❌ No se pudo abrir el modal de gestión de clientes:", result_gestion_clientes.get("error"))
                            
                        #else:
                        #    print("❌ No se pudo abrir el modal de referencias catastrales.")

                else:
                    print("No se abrió la ventana de Tarificación y emisión.")

                # Mantener la ventana abierta para inspección si no estamos en headless
                if not session.get("headless"):
                    print("La sesión queda abierta. Pulsa Enter para cerrar el navegador y terminar...")
                    input()
            else:
                print("⚠️ No se pudo abrir el menú 'Nueva producción':", result_menu["error"])

    finally:
        # Cerrar navegador y detener playwright al finalizar todas las acciones
        stop_playwright(session)
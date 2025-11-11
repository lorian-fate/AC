




# requirements: flask, playwright
# instalar navegadores: playwright install

from playwright.sync_api import sync_playwright
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

# URL base (ejemplo de login Mapfre)
#LOGIN_URL = "https://micuenta.mapfre.es/oauth2/default/v1/authorize?client_id=0oac9sd7okFbaB60z417&code_challenge=UCriTfkP9vO1d0L0QAtC4KmJken7nCkrcp0sxt9Db0A&code_challenge_method=S256&nonce=MHFY2dM4OE89g5SDM0KvY2vEBrx4essf9NTNAeGiMBzRcAJCxrdtfRYlLI37sWdD&redirect_uri=https%3A%2F%2Fareadeclientes.mapfre.es%2Flogin%2Fparticulares%2Fcallback&response_type=code&state=ZVNuoFjAlE7BvBXg9WYyjRDd6ekXzbhQatGSUcu5DAcfcZqiPoBXpaQKvleQu35p&scope=email%20profile%20openid&id_operacion=5&app_version=14.3.5"

#LOGIN_URL = "https://mercadona.avature.net/es_ES/Careers/Login"
LOGIN_URL = "https://wmediadores.mapfre.com/PortalMediadores_fe-web/#/login"
#LOGOUT_URL = "https://areadeclientes.mapfre.es/logout"  # Ejemplo, ajustar si cambia



# --- Funciones core ---
def login_mapfreFunciona(username, password):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # pon True en producción
        context = browser.new_context()

        page = context.new_page()
        page.goto(LOGIN_URL, timeout=4000000)

        # Rellenar formulario de login
        page.fill("input[name='nuuma']", username)
        page.fill("input[name='contrasena']", password)
        #page.click("button[type='submit']")
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

        browser.close()
        return {"success": login_success, "screenshot": screenshot}



# --- Función de login ---
def login_mapfre(username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # pon True en producción
        context = browser.new_context()

        page = context.new_page()
        page.goto(LOGIN_URL, timeout=4000000)

        # Rellenar formulario de login
        page.fill("input[name='nuuma']", username)
        page.fill("input[name='contrasena']", password)
        page.click("button[class='btn btn-red ng-scope ng-binding']")

        # Esperar redirección a área privada
        try:
            page.wait_for_url("**/areadeclientes.mapfre.es/**", timeout=650000)
            login_success = True
        except:
            login_success = False

        # Captura de pantalla del login
        screenshot = "login_result.png"
        page.screenshot(path=screenshot, full_page=True)

        if not login_success:
            browser.close()
            return {"success": False, "screenshot": screenshot}

        # Si el login fue exitoso, continuar con la sesión abierta
        return {"success": True, "page": page, "browser": browser, "context": context}



# --- Nueva función: acceso a Wealth ---
def go_to_wealth(page):
    """
    Esta función asume que ya se inició sesión correctamente
    y que `page` está en el contexto autenticado.
    Navega al enlace “Wealth” del menú desplegable.
    """
    try:
        # Asegurarse de que el menú esté desplegado
        page.click("a:has-text('Nueva producción')", timeout=15000)

        # Esperar que aparezca el submenú
        page.wait_for_selector("a[href*='aplicaciones-externas/patrimoniales']", timeout=15000)

        # Click en "Wealth"
        page.click("a[href*='aplicaciones-externas/patrimoniales']")

        # Esperar a que cargue la página correspondiente
        page.wait_for_url("**/aplicaciones-externas/patrimoniales**", timeout=40000)

        # Captura de pantalla del resultado
        screenshot = "wealth_section.png"
        page.screenshot(path=screenshot, full_page=True)

        return {"success": True, "screenshot": screenshot}

    except Exception as e:
        print(f"Error al acceder a Wealth: {e}")
        screenshot = "wealth_error.png"
        page.screenshot(path=screenshot, full_page=True)
        return {"success": False, "screenshot": screenshot, "error": str(e)}




def go_to_tarificacion_emision__No_probado(page):
    """
    Accede al enlace 'Tarificación y emisión' dentro de la sección 'Wealth'.
    Debe llamarse después de go_to_wealth().
    """
    try:
        # Esperar a que cargue la página de Wealth completamente
        page.wait_for_load_state("networkidle", timeout=25000)

        # Esperar que aparezca el texto 'Tarificación y emisión'
        page.wait_for_selector("p:has-text('Tarificación y emisión')", timeout=20000)

        # Click sobre el enlace que contiene ese texto
        page.click("p:has-text('Tarificación y emisión')")

        # Esperar que redirija o cargue nueva interfaz (ajustar según caso)
        page.wait_for_load_state("load", timeout=40000)

        # Capturar evidencia
        screenshot = "tarificacion_emision.png"
        page.screenshot(path=screenshot, full_page=True)

        return {"success": True, "screenshot": screenshot}

    except Exception as e:
        print(f"⚠️ Error al acceder a Tarificación y emisión: {e}")
        screenshot = "tarificacion_emision_error.png"
        page.screenshot(path=screenshot, full_page=True)
        return {"success": False, "error": str(e), "screenshot": screenshot}

def go_to_tarificacion_emision__Ajustado(page, context):
    """
    Desde la página de Wealth, accede a 'Tarificación y emisión'.
    Abre una nueva ventana/pestaña (emergente) y la devuelve.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
        page.wait_for_selector("p:has-text('Tarificación y emisión')", timeout=20000)

        # Esperar a que se abra nueva pestaña al hacer clic
        with context.expect_page() as new_page_info:
            page.click("p:has-text('Tarificación y emisión')")

        new_page = new_page_info.value
        new_page.wait_for_load_state("load", timeout=45000)

        screenshot = "tarificacion_emision.png"
        new_page.screenshot(path=screenshot, full_page=True)

        return {"success": True, "screenshot": screenshot, "page": new_page}

    except Exception as e:
        print(f"⚠️ Error al acceder a Tarificación y emisión: {e}")
        screenshot = "tarificacion_emision_error.png"
        page.screenshot(path=screenshot, full_page=True)
        return {"success": False, "error": str(e), "screenshot": screenshot}




def go_to_oferta_contratacion(page):
    """
    Accede al enlace 'Oferta / Contratación' dentro de la ventana emergente
    que se abre tras entrar en 'Tarificación y emisión'.
    """

    try:
        # Esperar a que el DOM cargue completamente
        page.wait_for_load_state("networkidle", timeout=30000)

        # Esperar a que aparezca el enlace "Oferta / Contratación"
        page.wait_for_selector("a:has-text('Oferta / Contratación')", timeout=25000)

        # Hacer clic y esperar nueva navegación
        with page.expect_navigation(wait_until="load", timeout=45000):
            page.click("a:has-text('Oferta / Contratación')")

        # Captura de pantalla para validación
        screenshot = "oferta_contratacion.png"
        page.screenshot(path=screenshot, full_page=True)

        print("✅ Acceso correcto a 'Oferta / Contratación'")
        return {"success": True, "screenshot": screenshot}

    except Exception as e:
        print(f"⚠️ Error al acceder a Oferta / Contratación: {e}")
        screenshot = "oferta_contratacion_error.png"
        page.screenshot(path=screenshot, full_page=True)
        return {"success": False, "error": str(e), "screenshot": screenshot}




def go_to_page_three(page):
    """
    Dentro de la ventana de 'Oferta / Contratación', hace clic en la página número '3'.
    Espera a que el contenido se actualice tras la acción.
    """

    try:
        # Esperar a que el DOM esté estable
        page.wait_for_load_state("networkidle", timeout=20000)

        # Esperar a que aparezca el enlace con id o texto '3'
        selector_opcion_3 = "a#tProductosComercialeslinkN3, a:has-text('3')"
        page.wait_for_selector(selector_opcion_3, timeout=15000)

        # Hacer clic
        page.click(selector_opcion_3)

        # Esperar a que se actualicen los datos (AJAX o recarga)
        # Si el click no recarga la página completa, añadimos un breve delay
        page.wait_for_timeout(2000)

        # Confirmar que algo ha cambiado (opcional: revisar DOM)
        screenshot = "pagina_3.png"
        page.screenshot(path=screenshot, full_page=True)

        print("✅ Acceso correcto a la página 3.")
        return {"success": True, "screenshot": screenshot}

    except Exception as e:
        print(f"⚠️ Error al acceder a la página 3: {e}")
        screenshot = "pagina_3_error.png"
        page.screenshot(path=screenshot, full_page=True)
        return {"success": False, "error": str(e), "screenshot": screenshot}




def select_centro_and_next(page):
    """
    En la página actual:
    1. Marca el radio button dentro de la columna con class='CENTRO'.
    2. Hace clic en el botón 'Siguiente >>' para avanzar.
    """

    try:
        # Esperar que cargue el contenido de la tabla
        page.wait_for_load_state("networkidle", timeout=20000)

        # Esperar el radio button dentro de una celda con class='CENTRO'
        page.wait_for_selector("td.CENTRO input[type='radio']", timeout=20000)

        # Hacer clic en el radio button (selecciona el registro)
        page.click("td.CENTRO input[type='radio']")

        # Confirmar selección (puede hacerse una pausa breve si hay validaciones JS)
        page.wait_for_timeout(1000)

        # Esperar y hacer clic en el botón 'Siguiente >>'
        page.wait_for_selector("a#formProductos\\:btnSiguiente", timeout=20000)
        with page.expect_navigation(wait_until="load", timeout=45000):
            page.click("a#formProductos\\:btnSiguiente")

        # Capturar evidencia
        screenshot = "seleccion_centro_y_siguiente.png"
        page.screenshot(path=screenshot, full_page=True)

        print("✅ Seleccionado 'Centro' y avanzado correctamente.")
        return {"success": True, "screenshot": screenshot}

    except Exception as e:
        print(f"⚠️ Error al seleccionar 'Centro' y avanzar: {e}")
        screenshot = "seleccion_centro_y_siguiente_error.png"
        page.screenshot(path=screenshot, full_page=True)
        return {"success": False, "error": str(e), "screenshot": screenshot}





def go_to_wealthOLD(driver, timeout=15):
    """
    Navega al módulo 'Wealth' dentro de la aplicación Mapfre.
    Requiere que la sesión esté iniciada.
    """
    try:
        wait = WebDriverWait(driver, timeout)

        # Esperar a que el menú principal esté presente
        menu_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[contains(text(), 'Nueva producción')]")
        ))

        # A veces los submenús están ocultos por CSS (display:none)
        # Se puede usar JavaScript para forzar la apertura
        driver.execute_script("arguments[0].click();", menu_button)
        time.sleep(1)

        # Esperar a que aparezca el enlace Wealth
        wealth_link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@href, '#/aplicaciones-externas/patrimoniales')]")
        ))

        # Hacer clic en el enlace Wealth
        driver.execute_script("arguments[0].click();", wealth_link)

        # Esperar a que la página de Wealth cargue
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Patrimoniales') or contains(@id, 'wealth')]")
        ))

        print("✅ Navegación exitosa al módulo 'Wealth'.")
        return True

    except TimeoutException:
        print("⚠️ No se pudo acceder al enlace 'Wealth' dentro del tiempo límite.")
        return False
    except Exception as e:
        print(f"❌ Error navegando al módulo 'Wealth': {e}")
        return False



def task_tarificarProyectoDeSegurosDeComunidadDePropietariosMapfre():
    return 0



#login_mapfre("GMRAFA3", "tw7P(kg(@0,")





if __name__ == "__main__":
    credentials = {"username": "GMRAFA3", "password": "tw7P(kg(@0,"}

    # Login
    session = login_mapfre(credentials["username"], credentials["password"])
    if session["success"]:
        print("✅ Login exitoso")

        # Ir a Wealth
        wealth_result = go_to_wealth(session["page"])
        if wealth_result["success"]:
            print("✅ Acceso a Wealth")

            # Ir a Tarificación y emisión
            #tarificacion_result = go_to_tarificacion_emision(session["page"])
            #print("Acceso a Tarificación y emisión:", tarificacion_result)
        else:
            print("❌ No se pudo acceder a Wealth")

        # Logout
        #logout_mapfre(session["page"], session["browser"])
        print("👋 Sesión cerrada.")
    else:
        print("❌ Error en el login.")




"""
#Mejorado para la función go_to_oferta_contratacion ajustado
if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 1. Login
        login_mapfre("usuario_demo", "clave_demo")

        # 2. Ir a Wealth
        go_to_wealth(page)

        # 3. Ir a Tarificación y emisión (devuelve nueva página)
        tarificacion_result = go_to_tarificacion_emision(page, context)
        if tarificacion_result["success"]:
            new_page = tarificacion_result["page"]

            # 4. En nueva página, acceder a Oferta / Contratación
            oferta_result = go_to_oferta_contratacion(new_page)
            print(oferta_result)

"""
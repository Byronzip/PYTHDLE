import builtins
import keyword
import random
import re
import sys
import json
import asyncio
from datetime import date, timedelta
from pyscript import document, window
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch
from explicaciones import EXPLICACIONES
from idiomas import TEXTOS, NOMBRES

# ===== 1. CONFIGURACIÓN =====
INTENTOS = 6
LARGO_MIN, LARGO_MAX = 3, 8
INICIO = date(2026, 1, 1)       # día 1 del juego
INCLUIR_MODULOS = False         # True = suma los módulos de la biblioteca estándar
EXCLUIR = {"copyright", "credits", "license", "exit", "quit"}

# Contador compartido de ganadores (servicio gratuito Abacus).
# Guarda un número por día; todos los jugadores ven el mismo.
CONTADOR_URL = "https://abacus.jasoncameron.dev"
CONTADOR_ESPACIO = "pythdle-juego"


# ===== 2. IDIOMA =====
def idioma_inicial():
    guardado = window.localStorage.getItem("pythdle-idioma")
    if guardado in TEXTOS:
        return guardado
    # Si no eligió uno, usamos el del navegador (español o, si no, inglés)
    return "es" if str(window.navigator.language).startswith("es") else "en"


idioma = idioma_inicial()


def t(clave, **datos):
    # t("faltan") -> "Faltan letras" o "Not enough letters", según el idioma
    return TEXTOS[idioma][clave].format(**datos)


# ===== 3. LAS PALABRAS LAS SACA PYTHON DE SÍ MISMO =====
# keyword  -> palabras clave (if, for, while, lambda...)
# builtins -> funciones integradas (print, len, range...)
# dir(str), dir(list), dir(dict) -> sus métodos (split, append, keys...)
# sys.stdlib_module_names -> nombres de módulos (math, json, random...)

def armar_diccionario():
    palabras = {}   # "print" -> ("print", "funcion")  (la categoría se traduce con t)

    def agregar(nombre, categoria):
        if (LARGO_MIN <= len(nombre) <= LARGO_MAX
                and nombre.isascii() and nombre.isalpha()
                and nombre not in EXCLUIR):
            palabras.setdefault(nombre.lower(), (nombre, categoria))

    for nombre in dir(builtins):
        if nombre[0].islower() and callable(getattr(builtins, nombre)):
            agregar(nombre, "funcion")

    for nombre in keyword.kwlist + keyword.softkwlist:
        agregar(nombre, "clave")

    for tipo, categoria in [(str, "texto"), (list, "lista"), (dict, "diccionario")]:
        for nombre in dir(tipo):
            if not nombre.startswith("_"):
                agregar(nombre, categoria)

    if INCLUIR_MODULOS:
        for nombre in sorted(sys.stdlib_module_names):
            if not nombre.startswith("_"):
                agregar(nombre, "modulo")

    return palabras


DICCIONARIO = armar_diccionario()


# ===== 4. UN COMANDO DIFERENTE CADA DÍA =====
def hoy():
    # Pedimos la fecha al navegador para que cambie a medianoche
    # en la hora local del jugador (y no en la hora UTC).
    ahora = window.Date.new()
    return date(ahora.getFullYear(), ahora.getMonth() + 1, ahora.getDate())


def comando_del_dia(dia):
    lista = sorted(DICCIONARIO)               # mismo orden base para todos
    dias = (dia - INICIO).days
    ciclo, posicion = divmod(dias, len(lista))

    # La semilla hace que el desorden sea SIEMPRE el mismo para un ciclo:
    # todos los jugadores ven el mismo comando el mismo día, ninguno se
    # repite hasta que salgan todos, y el ciclo siguiente cambia el orden.
    random.Random(ciclo).shuffle(lista)
    return lista[posicion], dias + 1


DIA = hoy()
secreta, NUMERO = comando_del_dia(DIA)
largo = len(secreta)
CLAVE = f"pywordle-{DIA.isoformat()}"     # progreso guardado de hoy
CONTADOR_LLAVE = f"ganadores-{DIA.isoformat()}"


# ===== 5. ESTADO DEL JUEGO =====
def cargar_progreso():
    texto = window.localStorage.getItem(CLAVE)
    return json.loads(texto) if texto else []


intentos = cargar_progreso()
actual = ""
terminado = False
animar_fila = None    # fila recién enviada con Enter: sus aciertos giran una vez
mensaje = (None, {})  # último mensaje, para poder traducirlo al cambiar de idioma
ganadores = None      # último valor del contador (None = aún no llega)
panel_abierto = None  # "estadisticas", "ayuda" o None


# ===== 6. LÓGICA: comparar un intento con la secreta =====
def evaluar(intento, secreta):
    resultado = ["ausente"] * len(secreta)
    sobrantes = {}

    for i in range(len(secreta)):
        if intento[i] == secreta[i]:
            resultado[i] = "correcta"
        else:
            sobrantes[secreta[i]] = sobrantes.get(secreta[i], 0) + 1

    for i in range(len(secreta)):
        if resultado[i] != "correcta" and sobrantes.get(intento[i], 0) > 0:
            resultado[i] = "presente"
            sobrantes[intento[i]] -= 1

    return resultado


# ===== 7. DIBUJAR EL TABLERO =====
def dibujar():
    tablero = document.getElementById("tablero")
    tablero.innerHTML = ""
    global animar_fila

    for fila in range(INTENTOS):
        div_fila = document.createElement("div")
        div_fila.className = "fila"

        palabra = ""
        colores = None
        if fila < len(intentos):
            palabra = intentos[fila]
            colores = evaluar(palabra, secreta)
        elif fila == len(intentos) and not terminado:
            palabra = actual

        for col in range(largo):
            casilla = document.createElement("div")
            casilla.className = "casilla"
            casilla.textContent = palabra[col] if col < len(palabra) else ""
            if colores:
                casilla.classList.add(colores[col])
            if fila == animar_fila:
                if palabra == secreta:
                    # ¡Ganó! Toda la fila salta y gira más grande
                    casilla.classList.add("girar-grande")
                    casilla.style.animationDelay = f"{col * 0.12}s"
                elif colores[col] != "ausente":
                    # Solo giran las letras correctas y las fuera de posición
                    casilla.classList.add("girar")
                    casilla.style.animationDelay = f"{col * 0.1}s"   # una tras otra
            div_fila.appendChild(casilla)

        tablero.appendChild(div_fila)

    # La animación es solo una vez: al escribir la siguiente letra
    # se redibuja el tablero y la fila ya no debe volver a girar.
    animar_fila = None

    pintar_teclado()          # cada vez que se redibuja, se actualizan los colores


# ===== 8. TECLADO EN PANTALLA =====
FILAS_TECLADO = ["qwertyuiop", "asdfghjkl", ["enter", *"zxcvbnm", "backspace"]]
ETIQUETAS = {"enter": "Enter", "backspace": "⌫"}


def crear_teclado():
    teclado = document.getElementById("teclado")
    for fila in FILAS_TECLADO:
        div_fila = document.createElement("div")
        div_fila.className = "fila-teclas"
        for letra in fila:
            boton = document.createElement("button")
            boton.className = "tecla"
            boton.dataset.letra = letra             # recuerda qué tecla es
            boton.textContent = ETIQUETAS.get(letra, letra)
            if letra in ETIQUETAS:
                boton.classList.add("ancha")
            div_fila.appendChild(boton)
        teclado.appendChild(div_fila)


def pintar_teclado():
    # Para cada letra guardamos el MEJOR color que ha tenido:
    # verde le gana a amarillo, y amarillo le gana a gris.
    prioridad = {"ausente": 1, "presente": 2, "correcta": 3}
    estado = {}
    for intento in intentos:
        for letra, color in zip(intento, evaluar(intento, secreta)):
            if prioridad[color] > prioridad.get(estado.get(letra), 0):
                estado[letra] = color

    for boton in document.querySelectorAll(".tecla"):
        boton.classList.remove("correcta", "presente", "ausente")
        color = estado.get(boton.dataset.letra)
        if color:
            boton.classList.add(color)


def al_hacer_clic(evento):
    boton = evento.target.closest(".tecla")
    if boton:
        boton.blur()            # para que Enter del teclado físico no la "vuelva a pulsar"
        procesar(boton.dataset.letra)


# ===== 9. TECLADO FÍSICO =====
def al_presionar(evento):
    if evento.key == "Escape":
        if panel_abierto:
            cerrar_panel()
        else:
            cerrar_modal()
        return
    enfocado = document.activeElement
    if panel_abierto or (enfocado and enfocado.tagName == "SELECT"):
        return          # mientras lees un panel o eliges idioma, no se escribe
    procesar(evento.key.lower())


# Las dos formas de escribir (teclado físico y en pantalla) terminan aquí
def procesar(tecla):
    global actual, animar_fila
    if terminado:
        return

    if tecla == "enter":
        if len(actual) < largo:
            mostrar("faltan")
            return
        if actual not in DICCIONARIO:
            mostrar("no_existe", palabra=actual)
            return
        intentos.append(actual)
        animar_fila = len(intentos) - 1
        actual = ""
        window.localStorage.setItem(CLAVE, json.dumps(intentos))
        revisar_fin(animar=True)

    elif tecla == "backspace":
        actual = actual[:-1]

    elif len(tecla) == 1 and tecla.isascii() and tecla.isalpha() and len(actual) < largo:
        actual += tecla

    dibujar()


def gano_hoy():
    return bool(intentos) and intentos[-1] == secreta


def mensaje_final():
    nombre, categoria = DICCIONARIO[secreta]
    datos = {"nombre": nombre, "categoria": t("cat_" + categoria)}
    if gano_hoy():
        mostrar("ganaste", n=len(intentos), max=INTENTOS, **datos)
    else:
        mostrar("perdiste", **datos)


def revisar_fin(animar=False):
    # animar=True cuando el juego termina ahora mismo (y no al recargar la página)
    global terminado
    gano = gano_hoy()
    terminado = gano or len(intentos) >= INTENTOS
    if not terminado:
        mostrar(None)
        return

    mensaje_final()
    armar_explicacion()
    asyncio.ensure_future(iniciar_contador(gano))
    # Si la fila está girando, esperamos a que termine antes de abrir la ventana
    if animar:
        espera = (largo * 120 + 1100) if gano else (largo * 100 + 700)
    else:
        espera = 0
    window.setTimeout(create_proxy(abrir_modal), espera)
    window.setInterval(create_proxy(cuenta_regresiva), 1000)
    cuenta_regresiva()


# ===== 10. VENTANA CON EL RESULTADO =====
def abrir_modal(*_):
    if panel_abierto:
        return          # no tapamos un panel que el jugador abrió
    document.getElementById("modal").hidden = False
    document.getElementById("ver-resultado").hidden = True


def cerrar_modal(*_):
    document.getElementById("modal").hidden = True
    if terminado:
        document.getElementById("ver-resultado").hidden = False


def al_hacer_clic_modal(evento):
    # Se cierra con la X o haciendo clic en el fondo oscuro
    if evento.target.id == "modal" or evento.target.closest(".cerrar"):
        cerrar_modal()


def armar_explicacion():
    nombre, categoria = DICCIONARIO[secreta]
    gano = gano_hoy()
    cuadro = document.getElementById("explicacion")
    cuadro.innerHTML = ""
    cuadro.className = "gano" if gano else "perdio"

    def agregar(etiqueta, texto, clase=""):
        elemento = document.createElement(etiqueta)
        elemento.textContent = texto      # textContent: nada se interpreta como HTML
        elemento.className = clase
        cuadro.appendChild(elemento)
        return elemento

    boton = agregar("button", "×", "cerrar")
    boton.setAttribute("aria-label", t("cerrar"))

    if gano:
        agregar("h2", t("correcto", nombre=nombre))
    else:
        agregar("h2", t("fallaste", nombre=nombre))
        agregar("p", t("animo"), "aviso")
    agregar("p", t("cat_" + categoria), "categoria")

    explicaciones = EXPLICACIONES[idioma]
    if secreta in explicaciones:
        uso, ejemplo = explicaciones[secreta]
        agregar("h3", t("para_que"))
        agregar("p", uso)
        agregar("h3", t("ejemplo"))
        agregar("pre", ejemplo)
    else:
        agregar("p", t("sin_explicacion", nombre=nombre), "aviso")

    # Contador de ganadores: los rodillos los llena girar_contador()
    contador = agregar("div", "", "contador")
    vivo = document.createElement("span")
    vivo.className = "en-vivo"
    vivo.textContent = t("en_vivo")
    contador.appendChild(vivo)
    rodillos = document.createElement("div")
    rodillos.id = "rodillos"
    contador.appendChild(rodillos)
    texto = document.createElement("p")
    texto.id = "texto-contador"
    texto.textContent = t("sin_conexion" if ganadores == "error" else "conectando")
    contador.appendChild(texto)

    if isinstance(ganadores, int):        # al cambiar de idioma, se conserva el número
        girar_contador(ganadores)


# ===== 11. CONTADOR EN TIEMPO REAL (efecto tragamonedas) =====
async def iniciar_contador(gano):
    global ganadores
    base = f"{CONTADOR_URL}/{{}}/{CONTADOR_ESPACIO}/{CONTADOR_LLAVE}"
    marca = CLAVE + "-contado"           # para sumar a cada jugador una sola vez
    sumar = gano and not window.localStorage.getItem(marca)
    try:
        respuesta = await pyfetch(base.format("hit" if sumar else "get"))
        # "get" responde 404 si nadie ha ganado todavía hoy
        valor = (await respuesta.json())["value"] if respuesta.ok else 0
        if sumar and respuesta.ok:
            window.localStorage.setItem(marca, "1")
    except Exception:
        ganadores = "error"
        document.getElementById("texto-contador").textContent = t("sin_conexion")
        return

    girar_contador(valor)

    # EventSource mantiene la conexión abierta: el servidor avisa
    # cada vez que alguien más adivina, y los rodillos vuelven a girar.
    def al_recibir(evento):
        girar_contador(json.loads(evento.data)["value"])

    fuente = window.EventSource.new(base.format("stream"))
    fuente.onmessage = create_proxy(al_recibir)


def girar_contador(valor):
    global ganadores
    ganadores = valor
    caja = document.getElementById("rodillos")
    digitos = str(valor)
    caja.setAttribute("aria-label", digitos)

    # Un rodillo por dígito; cada rodillo es una tira con 0-9 repetido 3 veces
    while caja.children.length < len(digitos):
        rodillo = document.createElement("div")
        rodillo.className = "rodillo"
        rodillo.dataset.actual = "0"
        tira = document.createElement("div")
        tira.className = "tira"
        for n in range(30):
            numero = document.createElement("span")
            numero.textContent = str(n % 10)
            tira.appendChild(numero)
        rodillo.appendChild(tira)
        caja.prepend(rodillo)

    for i, rodillo in enumerate(caja.querySelectorAll(".rodillo")):
        tira = rodillo.firstElementChild
        # 1) sin animación, volvemos al número actual en la primera vuelta
        tira.style.transition = "none"
        tira.style.transform = f"translateY(-{rodillo.dataset.actual}em)"
        tira.offsetHeight                 # obliga al navegador a aplicar el salto
        # 2) giramos dos vueltas completas hasta el nuevo número;
        #    los rodillos de la derecha frenan más tarde, como un tragamonedas
        tira.style.transition = f"transform {1.2 + i * 0.4}s cubic-bezier(.15, .7, .2, 1)"
        tira.style.transform = f"translateY(-{20 + int(digitos[i])}em)"
        rodillo.dataset.actual = digitos[i]

    texto = t("ganadores_1") if valor == 1 else t("ganadores_n")
    document.getElementById("texto-contador").textContent = texto


# ===== 12. ESTADÍSTICAS =====
# No guardamos nada extra: cada día jugado ya está en localStorage como
# "pywordle-AAAA-MM-DD" -> lista de intentos, y el comando de ese día
# se puede volver a calcular con comando_del_dia().

def partidas_guardadas():
    partidas = []       # (fecha, número de intentos, ¿ganó?)
    for i in range(window.localStorage.length):
        llave = window.localStorage.key(i)
        encontrado = re.fullmatch(r"pywordle-(\d{4}-\d{2}-\d{2})", llave or "")
        if not encontrado:
            continue
        dia = date.fromisoformat(encontrado.group(1))
        lista = json.loads(window.localStorage.getItem(llave))
        palabra = comando_del_dia(dia)[0]
        if palabra in lista:
            partidas.append((dia, lista.index(palabra) + 1, True))
        elif len(lista) >= INTENTOS:
            partidas.append((dia, len(lista), False))
        # si no ganó ni usó los 6 intentos, la partida sigue en curso: no cuenta
    return sorted(partidas)


def calcular_estadisticas():
    partidas = partidas_guardadas()
    distribucion = [0] * INTENTOS
    racha = mejor_racha = 0
    dia_anterior = None

    for dia, usados, gano in partidas:
        if gano:
            distribucion[usados - 1] += 1
            # La racha sigue solo si ganó también el día anterior
            seguida = dia_anterior is not None and dia - dia_anterior == timedelta(days=1)
            racha = racha + 1 if seguida else 1
            mejor_racha = max(mejor_racha, racha)
        else:
            racha = 0
        dia_anterior = dia

    # Si la última partida fue antes de ayer, la racha ya se cortó
    if partidas and DIA - partidas[-1][0] > timedelta(days=1):
        racha = 0

    jugados = len(partidas)
    ganados = sum(distribucion)
    mejor = next((n + 1 for n, cantidad in enumerate(distribucion) if cantidad), None)
    return {
        "jugados": jugados,
        "ganados": ganados,
        "porcentaje": round(ganados * 100 / jugados) if jugados else 0,
        "mejor": mejor,
        "racha": racha,
        "mejor_racha": mejor_racha,
        "distribucion": distribucion,
    }


def armar_estadisticas(cuerpo):
    datos = calcular_estadisticas()

    tarjetas = document.createElement("div")
    tarjetas.className = "tarjetas"
    for icono, valor, clave in [
        ("🕹️", datos["jugados"], "jugados"),
        ("🏆", datos["ganados"], "ganados"),
        ("📈", datos["porcentaje"], "victorias"),
        ("💎", f"#{datos['mejor']}" if datos["mejor"] else "–", "mejor_intento"),
        ("🔥", datos["racha"], "racha_actual"),
        ("⚡", datos["mejor_racha"], "mejor_racha"),
    ]:
        tarjeta = document.createElement("div")
        tarjeta.className = "tarjeta"
        numero = document.createElement("strong")
        numero.textContent = str(valor)
        etiqueta = document.createElement("span")
        etiqueta.textContent = f"{icono} {t(clave)}"
        tarjeta.append(numero, etiqueta)
        tarjetas.appendChild(tarjeta)
    cuerpo.appendChild(tarjetas)

    compartir = document.createElement("button")
    compartir.className = "compartir"
    compartir.textContent = t("compartir")
    compartir.onclick = create_proxy(lambda _: compartir_estadisticas(compartir, datos))
    cuerpo.appendChild(compartir)

    titulo = document.createElement("h3")
    titulo.textContent = t("distribucion")
    cuerpo.appendChild(titulo)

    # Una barra por intento; el ancho es el % de victorias logradas en ese intento
    for n, cantidad in enumerate(datos["distribucion"], start=1):
        porcentaje = round(cantidad * 100 / datos["ganados"]) if datos["ganados"] else 0
        fila = document.createElement("div")
        fila.className = "barra-fila"
        if gano_hoy() and n == len(intentos):
            fila.classList.add("hoy")       # resalta el intento con que ganaste hoy

        numero = document.createElement("span")
        numero.textContent = f"#{n}"
        pista = document.createElement("div")
        pista.className = "pista"
        relleno = document.createElement("div")
        relleno.className = "relleno" + (" vacio" if not cantidad else "")
        relleno.style.width = f"{porcentaje}%"
        relleno.textContent = f"{porcentaje}%"
        pista.appendChild(relleno)
        total = document.createElement("strong")
        total.textContent = str(cantidad)

        fila.append(numero, pista, total)
        cuerpo.appendChild(fila)


def compartir_estadisticas(boton, datos):
    # Texto con cuadritos de colores (sin revelar las letras) para pegar en un chat
    if terminado:
        cuadros = {"correcta": "🟩", "presente": "🟨", "ausente": "⬜"}
        resultado = f"{len(intentos) if gano_hoy() else 'X'}/{INTENTOS}\n" + "\n".join(
            "".join(cuadros[c] for c in evaluar(intento, secreta)) for intento in intentos
        )
    else:
        resultado = ""
    texto = t("compartir_texto", numero=NUMERO, resultado=resultado, **datos)
    window.navigator.clipboard.writeText(texto)
    boton.textContent = t("copiado")
    window.setTimeout(create_proxy(lambda: setattr(boton, "textContent", t("compartir"))), 2000)


# ===== 13. CÓMO JUGAR =====
# Los colores del ejemplo los calcula evaluar(), igual que en el juego real
EJEMPLO_SECRETA = "count"
EJEMPLO_INTENTOS = ["input", "round", "count"]


def fila_ejemplo(palabra):
    fila = document.createElement("div")
    fila.className = "fila ejemplo"
    for letra, color in zip(palabra, evaluar(palabra, EJEMPLO_SECRETA)):
        casilla = document.createElement("div")
        casilla.className = f"casilla {color}"
        casilla.textContent = letra
        fila.appendChild(casilla)
    return fila


def armar_ayuda(cuerpo):
    def parrafo(texto, clase=""):
        p = document.createElement("p")
        p.textContent = texto
        p.className = clase
        cuerpo.appendChild(p)

    primero, segundo, ultimo = EJEMPLO_INTENTOS
    parrafo(t("ayuda_intro"))
    parrafo(t("ayuda_validas"))
    cuerpo.appendChild(fila_ejemplo(primero))

    # Leyenda: qué significa cada color, con las letras del primer ejemplo
    leyenda = document.createElement("div")
    leyenda.className = "leyenda"
    colores = evaluar(primero, EJEMPLO_SECRETA)
    for color in ["ausente", "presente", "correcta"]:
        linea = document.createElement("p")
        letras = [letra for letra, c in zip(primero, colores) if c == color]
        for letra in letras:
            chip = document.createElement("span")
            chip.className = f"chip {color}"
            chip.textContent = letra
            linea.appendChild(chip)
        linea.append(" " + t("ayuda_" + color))
        leyenda.appendChild(linea)
    cuerpo.appendChild(leyenda)

    parrafo(t("ayuda_otro"))
    cuerpo.appendChild(fila_ejemplo(segundo))
    parrafo(t("ayuda_cerca"))
    cuerpo.appendChild(fila_ejemplo(ultimo))
    parrafo(t("ayuda_adivinada"), "destacado")
    parrafo(t("ayuda_final"))


# ===== 14. PANELES (estadísticas y cómo jugar) =====
def abrir_panel(tipo):
    global panel_abierto
    panel_abierto = tipo
    document.getElementById("modal").hidden = True   # el panel va por encima
    document.getElementById("panel-titulo").textContent = t(
        "estadisticas" if tipo == "estadisticas" else "como_jugar"
    )
    cuerpo = document.getElementById("panel-cuerpo")
    cuerpo.innerHTML = ""
    cuerpo.className = tipo
    if tipo == "estadisticas":
        armar_estadisticas(cuerpo)
    else:
        armar_ayuda(cuerpo)
    document.getElementById("panel").hidden = False
    for boton in document.querySelectorAll(".icono"):
        boton.classList.toggle("activo", boton.id == f"btn-{tipo}")


def cerrar_panel(*_):
    global panel_abierto
    panel_abierto = None
    document.getElementById("panel").hidden = True
    for boton in document.querySelectorAll(".icono"):
        boton.classList.remove("activo")
    if terminado:
        document.getElementById("ver-resultado").hidden = False


def al_hacer_clic_panel(evento):
    if evento.target.id == "panel" or evento.target.closest(".cerrar-panel"):
        cerrar_panel()


def alternar_panel(tipo):
    # Volver a tocar el mismo ícono cierra el panel
    if panel_abierto == tipo:
        cerrar_panel()
    else:
        abrir_panel(tipo)


# ===== 15. TEXTOS EN PANTALLA Y CAMBIO DE IDIOMA =====
def mostrar(clave, **datos):
    global mensaje
    mensaje = (clave, datos)
    document.getElementById("mensaje").textContent = t(clave, **datos) if clave else ""


def cuenta_regresiva():
    ahora = window.Date.new()
    manana = window.Date.new(ahora.getFullYear(), ahora.getMonth(), ahora.getDate() + 1)
    segundos = int((manana.getTime() - ahora.getTime()) / 1000)
    if segundos <= 0:
        window.location.reload()      # ya es otro día: carga el nuevo comando
        return
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    document.getElementById("cuenta").textContent = t("proximo", h=h, m=m, s=s)


def aplicar_textos():
    document.documentElement.lang = idioma
    document.getElementById("info").textContent = t(
        "info", numero=NUMERO, largo=largo, total=len(DICCIONARIO)
    )
    document.getElementById("ver-resultado").textContent = t("ver_resultado")
    document.getElementById("btn-estadisticas").setAttribute("aria-label", t("estadisticas"))
    document.getElementById("btn-ayuda").setAttribute("aria-label", t("como_jugar"))
    document.querySelector(".cerrar-panel").setAttribute("aria-label", t("cerrar"))
    document.getElementById("idioma").setAttribute("aria-label", t("idioma"))

    clave, datos = mensaje
    if terminado:
        mensaje_final()               # la categoría también cambia de idioma
        armar_explicacion()
        cuenta_regresiva()
    elif clave:
        mostrar(clave, **datos)
    if panel_abierto:
        abrir_panel(panel_abierto)


def cambiar_idioma(evento):
    global idioma
    idioma = evento.target.value
    window.localStorage.setItem("pythdle-idioma", idioma)
    evento.target.blur()
    aplicar_textos()


def crear_selector_idioma():
    selector = document.getElementById("idioma")
    for codigo, nombre in NOMBRES.items():
        opcion = document.createElement("option")
        opcion.value = codigo
        opcion.textContent = nombre
        selector.appendChild(opcion)
    selector.value = idioma
    selector.addEventListener("change", create_proxy(cambiar_idioma))


# ===== 16. INICIO =====
crear_teclado()
crear_selector_idioma()
aplicar_textos()
document.addEventListener("keydown", create_proxy(al_presionar))
document.getElementById("teclado").addEventListener("click", create_proxy(al_hacer_clic))
document.getElementById("modal").addEventListener("click", create_proxy(al_hacer_clic_modal))
document.getElementById("panel").addEventListener("click", create_proxy(al_hacer_clic_panel))
document.getElementById("ver-resultado").addEventListener("click", create_proxy(abrir_modal))
document.getElementById("btn-estadisticas").addEventListener(
    "click", create_proxy(lambda e: (e.currentTarget.blur(), alternar_panel("estadisticas")))
)
document.getElementById("btn-ayuda").addEventListener(
    "click", create_proxy(lambda e: (e.currentTarget.blur(), alternar_panel("ayuda")))
)
revisar_fin()      # por si ya jugaste hoy y recargaste la página
dibujar()

# La primera vez que alguien entra, le mostramos cómo se juega
if not window.localStorage.getItem("pythdle-ayuda-vista") and not intentos:
    window.localStorage.setItem("pythdle-ayuda-vista", "1")
    abrir_panel("ayuda")

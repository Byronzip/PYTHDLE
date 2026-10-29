# ===== TEXTOS DEL JUEGO EN CADA IDIOMA =====
# Para agregar un idioma nuevo: copia el bloque "es", cambia la clave
# (por ejemplo "pt") y traduce los textos. Las {llaves} se rellenan solas.

NOMBRES = {"es": "Español", "en": "English"}

TEXTOS = {
    "es": {
        "info": "Pythdle #{numero} · {largo} letras · {total} comandos posibles",
        "faltan": "Faltan letras",
        "no_existe": "'{palabra}' no es un comando de Python",
        "ganaste": "¡Ganaste en {n}/{max}! Era {nombre} ({categoria})",
        "perdiste": "Perdiste. Era {nombre} ({categoria})",
        "proximo": "Próximo comando en {h:02d}:{m:02d}:{s:02d}",
        "ver_resultado": "Ver resultado",
        "cerrar": "Cerrar",

        # Categorías
        "cat_funcion": "Función integrada",
        "cat_clave": "Palabra clave",
        "cat_texto": "Método de texto",
        "cat_lista": "Método de lista",
        "cat_diccionario": "Método de diccionario",
        "cat_modulo": "Módulo",

        # Ventana del resultado
        "correcto": "¡Correcto! El comando era {nombre}",
        "fallaste": "¡Fallaste! El comando era {nombre}",
        "animo": "No te preocupes: mañana hay un comando nuevo. Así aprendes uno más de Python.",
        "para_que": "¿Para qué se usa?",
        "ejemplo": "Ejemplo",
        "sin_explicacion": "Aún no tenemos una explicación para este comando. "
                           "Prueba help({nombre}) en Python para saber más.",
        "en_vivo": "EN VIVO",
        "conectando": "Conectando...",
        "sin_conexion": "No se pudo conectar con el contador",
        "ganadores_1": "persona adivinó el comando de hoy",
        "ganadores_n": "personas adivinaron el comando de hoy",

        # Estadísticas
        "estadisticas": "Estadísticas",
        "jugados": "Juegos jugados",
        "ganados": "Juegos ganados",
        "victorias": "Victorias (%)",
        "mejor_intento": "Mejor intento",
        "racha_actual": "Racha actual",
        "mejor_racha": "Mejor racha",
        "compartir": "Comparte tus estadísticas",
        "copiado": "¡Copiado! Pégalo donde quieras",
        "distribucion": "Distribución de intentos",
        "compartir_texto": "Pythdle #{numero} {resultado}\n"
                           "Jugados: {jugados} · Victorias: {porcentaje}% · Racha: {racha}",

        # Cómo jugar
        "como_jugar": "Cómo jugar",
        "ayuda_intro": "Adivina el comando de Python del día en 6 intentos. "
                       "El color de las letras cambia para mostrar lo cerca que estás.",
        "ayuda_validas": "Cada intento debe ser un comando real de Python (una función, "
                         "una palabra clave o un método) con el largo indicado. Por ejemplo:",
        "ayuda_ausente": "no está en el comando.",
        "ayuda_presente": "está en el comando, pero en otro lugar.",
        "ayuda_correcta": "está en el comando y en el lugar correcto.",
        "ayuda_otro": "Usa lo que aprendiste en el siguiente intento:",
        "ayuda_cerca": "¡Muy cerca!",
        "ayuda_adivinada": "¡Comando adivinado! 🏆",
        "ayuda_final": "Cada día hay un comando nuevo. Al terminar verás para qué sirve "
                       "y un pequeño ejemplo.",
        "idioma": "Idioma",
    },

    "en": {
        "info": "Pythdle #{numero} · {largo} letters · {total} possible commands",
        "faltan": "Not enough letters",
        "no_existe": "'{palabra}' is not a Python command",
        "ganaste": "You won in {n}/{max}! It was {nombre} ({categoria})",
        "perdiste": "You lost. It was {nombre} ({categoria})",
        "proximo": "Next command in {h:02d}:{m:02d}:{s:02d}",
        "ver_resultado": "See result",
        "cerrar": "Close",

        "cat_funcion": "Built-in function",
        "cat_clave": "Keyword",
        "cat_texto": "String method",
        "cat_lista": "List method",
        "cat_diccionario": "Dictionary method",
        "cat_modulo": "Module",

        "correcto": "Correct! The command was {nombre}",
        "fallaste": "Missed it! The command was {nombre}",
        "animo": "Don't worry: there's a new command tomorrow. Now you know one more bit of Python.",
        "para_que": "What is it for?",
        "ejemplo": "Example",
        "sin_explicacion": "We don't have an explanation for this command yet. "
                           "Try help({nombre}) in Python to learn more.",
        "en_vivo": "LIVE",
        "conectando": "Connecting...",
        "sin_conexion": "Couldn't connect to the counter",
        "ganadores_1": "person guessed today's command",
        "ganadores_n": "people guessed today's command",

        "estadisticas": "Statistics",
        "jugados": "Games played",
        "ganados": "Games won",
        "victorias": "Win rate (%)",
        "mejor_intento": "Best try",
        "racha_actual": "Current streak",
        "mejor_racha": "Best streak",
        "compartir": "Share your stats",
        "copiado": "Copied! Paste it anywhere",
        "distribucion": "Guess distribution",
        "compartir_texto": "Pythdle #{numero} {resultado}\n"
                           "Played: {jugados} · Wins: {porcentaje}% · Streak: {racha}",

        "como_jugar": "How to play",
        "ayuda_intro": "Guess the Python command of the day in 6 tries. "
                       "The letters change color to show how close you are.",
        "ayuda_validas": "Each guess must be a real Python command (a function, "
                         "a keyword or a method) of the right length. For example:",
        "ayuda_ausente": "is not in the command.",
        "ayuda_presente": "is in the command, but in another spot.",
        "ayuda_correcta": "is in the command and in the right spot.",
        "ayuda_otro": "Use what you learned on the next try:",
        "ayuda_cerca": "So close!",
        "ayuda_adivinada": "Command guessed! 🏆",
        "ayuda_final": "There's a new command every day. When you finish you'll see "
                       "what it's for and a small example.",
        "idioma": "Language",
    },
}

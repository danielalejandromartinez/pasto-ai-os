import os
import json
from datetime import datetime, timedelta
import pytz 
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analizar_intencion(texto_usuario: str, usuario_contexto: dict, historial_chat: list = []):
    """
    Cerebro de Alejandro v17.0 - Edición "Analytical, Predictive & Universal Intelligence".
    Paso del Loop: [2. INTERPRETAR 🧠]
    Misión: Clasificación industrial de intenciones incluyendo Emojis, Tiempos, Comandos CEO y Analítica Profunda.
    """
    
    # 🎨 [LOG DE INICIO] - Estética NASA para el Video Beam de la Junta
    nombre_usuario = usuario_contexto.get('nombre', 'Desconocido')
    rol_usuario = usuario_contexto.get('rol', 'JUGADOR')
    
    print(f"\n\033[1;95m" + "="*85)
    print(f"🔍 [OÍDO/INTENT] -> ESCANEANDO FRECUENCIA: {nombre_usuario} ({rol_usuario})")
    print(f"📩 SEÑAL RECIBIDA: '{texto_usuario}'")
    print(f"="*85 + "\033[0m")
    
    # 1. CONTEXTO TEMPORAL DE ALTA PRECISIÓN (Bogotá, Colombia)
    bogota_tz = pytz.timezone('America/Bogota')
    ahora = datetime.now(bogota_tz)
    fecha_humana = ahora.strftime("%A, %d de %B de %Y, Hora Actual: %H:%M")
    
    # 2. CONSTITUCIÓN DE LA MEMORIA ACTIVA (Sincronización de Contexto para Autonomía)
    historial_txt = "SISTEMA SIN MEMORIA PREVIA (Inicio de Ciclo)"
    if historial_chat:
        historial_txt = "REGISTROS DE MEMORIA RECIENTE (HISTORIAL DE CONVERSACIÓN):\n"
        for m in historial_chat[-6:]:
            rol = "Alejandro (SISTEMA)" if m['role'] == 'assistant' else f"{nombre_usuario} (SOCIO)"
            historial_txt += f"- {rol}: {m['content']}\n"
    
    # 🧠 PROMPT MAESTRO V17.0 (Ingeniería de Instrucciones de Máxima Robustez y Poder Analítico)
    prompt = f"""
    Eres el componente de INTERPRETACIÓN de Pasto.AI OS. Tu misión es transformar CUALQUIER señal humana 
    en datos técnicos deterministas para un sistema operativo agéntico autónomo de clase mundial.
    RELOJ DE SISTEMA: {fecha_humana} (Colombia).

    ### CONTEXTO DE MEMORIA:
    {historial_txt}

    ### TU MISIÓN TÉCNICA:
    Analiza la "SEÑAL RECIBIDA" ignorando el ruido y extrayendo la voluntad real del usuario con precisión forense.

    ### REGLAS DE INTELIGENCIA ANALÍTICA Y PREDICTIVA:
    1. ANALÍTICA DE RANKING: Si el socio pregunta por su puesto, diferencia de puntos con otros, cuántos partidos le faltan para subir de posición, o qué probabilidades tiene de ganar la estrella de la temporada -> tipo: 'consultar_analitica'.
       - Ejemplo: "¿Cuantos puntos me faltan para alcanzar a Daniel?", "¿Que probabilidad tengo de ser el #1?", "¿Kien me persigue?".
       - Extrae el 'objetivo_analitico' (ej: gap con puesto 1) y el 'rival_referencia' si lo menciona.

    ### REGLAS DE INTELIGENCIA SIMBÓLICA Y SOCIAL:
    2. CORTESÍA Y GRATITUD: Si el usuario dice "gracias", "mil gracias", "perfecto", "excelente", "entendido", ❤️, 🙏 -> tipo: 'agradecimiento'.
    3. EMOJIS DE ACEPTACIÓN: 👍, ✅, 🔥, 🆗, 👌, 🔝 -> tipo: 'aceptar_reto' (si hay un reto pendiente en el historial).
    
    ### REGLAS DE RESILIENCIA LINGÜÍSTICA (INNEGOCIABLES):
    4. FLEXIBILIDAD DE VERBOS: "jugar con", "darle una paliza a", "desafiar", "echar un partido" -> 'crear_reto'.
    5. INTELIGENCIA TEMPORAL: "pasado mañana", "este sábado". Genera 'fecha_iso' (YYYY-MM-DDTHH:MM:SS) si tienes día y hora.
    6. CATEGORÍAS LITERALES: Prohibido usar sinónimos. Usa exactamente los nombres configurados (Pro, Intermedio, Novato).

    ### COMANDOS DE RANGO Y GESTIÓN:
    - 'unirse_categoria': Acción personal de perfil ("ponme en...", "quiero estar en...").
    - 'configurar_categorias': Orden administrativa de estructura global (Solo ADMIN/CEO).
    - 'autorizar_socio': Orden administrativa de acceso para terceros (Solo ADMIN/CEO).

    ### LISTA DE INTENCIONES OFICIALES:
    - 'crear_reto', 'aceptar_reto', 'rechazar_reto', 'reproponer_reto', 'configurar_categorias', 'unirse_categoria', 'autorizar_socio', 'agradecimiento', 'consultar_analitica', 'enviar_comprobante', 'chat_general'.

    MENSAJE ACTUAL: "{texto_usuario}"

    ### FORMATO DE SALIDA (JSON ÚNICAMENTE):
    {{
        "tipo": "NOMBRE_INTENCION",
        "datos": {{
            "rival": "nombre extraído o heredado",
            "dia": "día detectado o heredado",
            "hora": "hora detectada",
            "categoria": "categoría literal detectada",
            "objetivo_analitico": "ej: diferencia de puntos o probabilidad de ganar",
            "rival_referencia": "nombre del rival con el que se compara o null",
            "telefono_a_autorizar": "número o null",
            "nombre_a_autorizar": "nombre o null",
            "fecha_iso": "ISO calculada o null",
            "analisis_visual_simbolico": "Emoji o palabra clave detectada",
            "analisis_dialecto": "Tono (Formal/Emoji/Analítico/Coloquial/Gratitud)",
            "razonamiento_tecnico": "Lógica forense del resultado basado en el contexto"
        }},
        "confianza": "alta/media/baja"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": texto_usuario}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )
        
        resultado = json.loads(response.choices[0].message.content)
        
        # 🎨 [LOG DE RESULTADO] - Trazabilidad NASA de Grado Industrial
        tipo = resultado.get("tipo", "chat_general")
        datos = resultado.get("datos", {})
        dialecto = datos.get("analisis_dialecto", "Estándar")
        simbolo = datos.get("analisis_visual_simbolico", "Ninguno")
        log_ia = datos.get("razonamiento_tecnico", "N/A")

        print(f"\033[1;33m🗣️  DIALECTO DETECTADO -> {dialecto}\033[0m")
        if simbolo != "Ninguno":
            print(f"\033[1;93m✨ SEÑAL IDENTIFICADA -> {simbolo}\033[0m")
        print(f"\033[1;36m🧠 [ANÁLISIS LÓGICO] -> {log_ia}\033[0m")
        
        if tipo == "autorizar_socio":
            print(f"\033[1;91m⚡ [COMANDO CEO] -> AUTORIZAR: {datos.get('nombre_a_autorizar')} ({datos.get('telefono_a_autorizar')})")
        elif tipo == "consultar_analitica":
            print(f"\033[1;34m📊 [MODO ESTRATEGA] -> CONSULTA: {datos.get('objetivo_analitico')}\033[0m")
        elif tipo == "agradecimiento":
            print(f"\033[1;93m🙏 [CORTESÍA] -> El socio ha expresado gratitud o confirmación final.\033[0m")
        
        # Logs de slots detallados
        print(f"   👤 Rival: {datos.get('rival')} | 📦 Cat: {datos.get('categoria')}")
        print(f"   📅 Día:   {datos.get('dia')} | ⏰ Hora: {datos.get('hora')}")
        if datos.get('fecha_iso') and str(datos.get('fecha_iso')).lower() != 'null': 
            print(f"   🌐 \033[1;92mISO CALCULADA: {datos.get('fecha_iso')}\033[0m")
            
        print(f"\033[1;92m✅ [INTENCIÓN FINAL] -> {tipo.upper()}\033[0m")
        print("\033[1;95m" + "="*85 + "\033[0m\n")
        
        return resultado

    except Exception as e:
        print(f"\033[1;31m❌ [ERROR CRÍTICO EN OÍDO] -> {e}\033[0m")
        return {"tipo": "chat_general", "datos": {}, "confianza": "error"}
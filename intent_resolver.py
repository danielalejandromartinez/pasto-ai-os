import os
import json
from datetime import datetime
import pytz 
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analizar_intencion(texto_usuario: str, usuario_contexto: dict, historial_chat: list = []):
    """
    Cerebro de Alejandro v22.0 - Edición "Persistent Context & Detective Logic".
    Paso del Loop: [2. INTERPRETAR 🧠]
    Misión: Garantizar que Alejandro NUNCA olvide el contexto de un reto (Slot Filling).
    """
    
    # 🎨 [PASO 1 DEL LOOP: OBSERVAR 👁️] - Estética NASA para el Centro de Mando
    nombre_usuario = usuario_contexto.get('nombre', 'Desconocido')
    rol_usuario = usuario_contexto.get('rol', 'JUGADOR')
    
    print(f"\n\033[1;95m" + "="*85)
    print(f"🔍 [LOOP: PASO 2 - INTERPRETAR 🧠] -> ESCANEANDO FRECUENCIA: {nombre_usuario}")
    print(f"📩 SEÑAL RECIBIDA: '{texto_usuario}'")
    print(f"="*85 + "\033[0m")
    
    # 1. CONTEXTO TEMPORAL DE ALTA PRECISIÓN (Bogotá, Colombia)
    bogota_tz = pytz.timezone('America/Bogota')
    ahora = datetime.now(bogota_tz)
    fecha_humana = ahora.strftime("%A, %d de %B de %Y, Hora Actual: %H:%M")
    
    # 2. CONSTITUCIÓN DE LA MEMORIA ACTIVA (PASO 7: APRENDER 📚)
    historial_txt = "SISTEMA SIN MEMORIA PREVIA (Inicio de Ciclo)"
    if historial_chat:
        historial_txt = "REGISTROS DE MEMORIA RECIENTE (HISTORIAL):\n"
        for m in historial_chat[-8:]: # Ampliamos a 8 mensajes para no perder ni una pista
            rol = "Alejandro (SISTEMA)" if m['role'] == 'assistant' else f"{nombre_usuario} (SOCIO)"
            historial_txt += f"- {rol}: {m['content']}\n"
    
    # 🧠 PROMPT MAESTRO V22.0 (La Constitución de la Memoria Infinita)
    prompt = f"""
    Eres el Módulo de INTERPRETACIÓN de Pasto.AI OS. Tu misión es transformar señales humanas en datos deterministas.
    RELOJ DE SISTEMA: {fecha_humana} (Colombia).

    ### CONTEXTO DE MEMORIA:
    {historial_txt}

    ### TU MISIÓN TÉCNICA (LA REGLA DEL DETECTIVE):
    1. SLOT FILLING & HERENCIA: Si el mensaje actual es corto (ej: "mañana", "a las 5", "ok", "👍") y no menciona al rival, DEBES BUSCAR en el 'HISTORIAL' quién era el rival del que estaban hablando.
    2. PERSISTENCIA DE MISIÓN: Si hay un proceso de reto abierto, NO saltes a 'chat_general' a menos que el usuario cambie de tema radicalmente. Tu objetivo es completar el reto.
    3. JERGA Y EMOJIS: "De una", "👍", "hágale" = ACEPTAR_RETO.
    4. COMANDO SAAS: Detecta 'crear_nuevo_club' si el CEO lo pide.

    ### REGLA DE ORO DE SALIDA:
    Si en el historial Hugo dijo "Retar a Daniel" y ahora dice "mañana", el JSON debe devolver 'tipo': 'crear_reto' y 'rival': 'Daniel'. NUNCA devuelvas None si el dato existe en el pasado reciente.

    MENSAJE ACTUAL: "{texto_usuario}"

    ### FORMATO DE SALIDA (JSON ÚNICAMENTE):
    {{
        "tipo": "NOMBRE_INTENCION",
        "datos": {{
            "rival": "nombre HEREDADO del historial o nuevo",
            "dia": "día HEREDADO o nuevo",
            "hora": "hora detectada",
            "categoria": "categoría literal",
            "nombre_club": "Nombre para SaaS si aplica",
            "telefono_admin": "Teléfono para SaaS si aplica",
            "fecha_iso": "ISO calculada si tienes día y hora"
        }},
        "analisis_visual": {{
            "dialecto": "Origen detectado (Pasto/Madrid/Emoji/SaaS)",
            "señal_identificada": "Palabra o símbolo clave"
        }},
        "razonamiento_paso_3": "[PASO 3: RAZONAR 🧐] Explica aquí cómo uniste el historial con el mensaje actual para no perder el rival.",
        "verificacion_paso_6": "[PASO 6: VERIFICAR ✅] ¿Los datos están completos para la misión? SI/NO"
    }}
    """

    try:
        # [PASO 5 DEL LOOP: EJECUTAR ⚡] - Consultamos a la Inteligencia Superior
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": texto_usuario}
            ],
            response_format={ "type": "json_object" },
            temperature=0 # Temperatura 0 para que sea un matemático y no un poeta
        )
        
        resultado = json.loads(response.choices[0].message.content)
        
        # 🎨 [PASO 3 Y 6 EN LOGS] - Transparencia total para el CEO y el CTO
        datos = resultado.get("datos", {})
        analisis = resultado.get("analisis_visual", {})
        log_ia = resultado.get("razonamiento_paso_3", "N/A")
        log_verif = resultado.get("verificacion_paso_6", "N/A")

        print(f"\033[1;33m🗣️  DIALECTO DETECTADO -> {analisis.get('dialecto')}\033[0m")
        print(f"\033[1;36m🧠 [LOOP: PASO 3 - RAZONAR 🧐] -> {log_ia}\033[0m")
        print(f"\033[1;32m✅ [LOOP: PASO 6 - VERIFICAR ✅] -> {log_verif}\033[0m")
        
        # Logs de slots con herencia
        print(f"   👤 Rival: {datos.get('rival')} | 📦 Cat: {datos.get('categoria')}")
        print(f"   📅 Día:   {datos.get('dia')} | ⏰ Hora: {datos.get('hora')}")
        if datos.get('fecha_iso') and str(datos.get('fecha_iso')).lower() != 'null': 
            print(f"   🌐 ISO CALCULADA: {datos.get('fecha_iso')}")
            
        print(f"\033[1;92m🚀 [INTENCIÓN FINAL] -> {resultado.get('tipo').upper()}\033[0m")
        print("\033[1;95m" + "="*85 + "\033[0m\n")
        
        return resultado

    except Exception as e:
        print(f"\033[1;31m❌ [ERROR CRÍTICO EN PASO 2] -> {e}\033[0m")
        return {"tipo": "chat_general", "datos": {}, "confianza": "error"}
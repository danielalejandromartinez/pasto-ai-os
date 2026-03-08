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
    Cerebro de Alejandro v20.0 - Edición "Global Slang & Emoji Intelligence".
    Paso del Loop: [2. INTERPRETAR 🧠]
    Misión: Comprensión universal de jerga (Pasto, Madrid, Argentina) y simbología (Emojis).
    """
    
    # 🎨 [PASO 1 DEL LOOP: OBSERVAR 👁️]
    nombre_usuario = usuario_contexto.get('nombre', 'Desconocido')
    rol_usuario = usuario_contexto.get('rol', 'JUGADOR')
    
    print(f"\n\033[1;95m" + "="*85)
    print(f"🔍 [OÍDO/INTENT] -> ESCANEANDO FRECUENCIA UNIVERSAL: {nombre_usuario}")
    print(f"📩 SEÑAL RECIBIDA: '{texto_usuario}'")
    print(f"="*85 + "\033[0m")
    
    # Contexto temporal de alta precisión
    bogota_tz = pytz.timezone('America/Bogota')
    ahora = datetime.now(bogota_tz)
    fecha_humana = ahora.strftime("%A, %d de %B de %Y, Hora Actual: %H:%M")
    
    # [PASO 7 DEL LOOP: APRENDER 📚] - Carga de Memoria Activa
    historial_txt = "SISTEMA SIN MEMORIA PREVIA"
    if historial_chat:
        historial_txt = "HISTORIAL DE CONVERSACIÓN (Contexto de Jerga y Emojis):\n"
        for m in historial_chat[-8:]:
            rol = "Alejandro (SISTEMA)" if m['role'] == 'assistant' else f"{nombre_usuario} (SOCIO)"
            historial_txt += f"- {rol}: {m['content']}\n"
    
    # 🧠 PROMPT MAESTRO V20.0 (El Políglota Universal)
    prompt = f"""
    Eres el Módulo de INTERPRETACIÓN de Pasto.AI OS. Tu misión es descifrar la voluntad real del usuario 
    sin importar su dialecto, jerga o uso de emojis.
    RELOJ: {fecha_humana} (Colombia).

    ### CONTEXTO DE MEMORIA:
    {historial_txt}

    ### TU MISIÓN TÉCNICA (UNIVERSAL UNDERSTANDING):
    1. JERGA GLOBAL: Entiende "De una", "Parce" (Colombia), "Mola", "Vale", "Hostia" (España), "Che", "Dale", "Copado" (Argentina), "Bacan", "Chévere" y cualquier variante regional.
    2. INTELIGENCIA DE EMOJIS: 
       - 👍, ✅, 🤝, 🔥, 👌, 🔝, 🆗, 🦾 = ACEPTAR_RETO (si hay un reto pendiente).
       - ❌, 👎, 🚫, 🙅‍♂️ = RECHAZAR_RETO.
       - 🎾, ⚔️, 🏟️ = CREAR_RETO.
    3. SLOT FILLING: Si el mensaje es solo un emoji o una palabra de jerga, BUSCA EN LA MEMORIA qué se estaba hablando y completa los datos (rival, día, hora). NUNCA borres datos heredados.

    ### FORMATO DE SALIDA (JSON ÚNICAMENTE):
    {{
        "tipo": "NOMBRE_INTENCION",
        "datos": {{
            "rival": "nombre heredado o nuevo",
            "dia": "día heredado o nuevo",
            "hora": "hora detectada",
            "fecha_iso": "ISO calculada o null"
        }},
        "analisis_visual": {{
            "dialecto": "Origen detectado (Pasto/Madrid/Argentina/Emoji/etc)",
            "señal_identificada": "Emoji o Jerga detectada"
        }},
        "razonamiento_paso_3": "[RAZONAR 🧐] Explica por qué este emoji o jerga significa esta intención basándote en el historial.",
        "verificacion_paso_6": "[VERIFICAR ✅] ¿Los datos heredados coinciden con la jerga actual? (SI/NO)"
    }}
    """

    try:
        # [PASO 5 DEL LOOP: EJECUTAR ⚡]
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
        
        # 🎨 [LOGS DE TRANSPARENCIA NASA]
        datos = resultado.get("datos", {})
        analisis = resultado.get("analisis_visual", {})
        log_ia = resultado.get("razonamiento_paso_3", "N/A")
        log_verif = resultado.get("verificacion_paso_6", "N/A")

        print(f"\033[1;33m🗣️  DIALECTO/JERGA -> {analisis.get('dialecto')}\033[0m")
        if analisis.get('señal_identificada'):
            print(f"\033[1;93m✨ SEÑAL DETECTADA -> {analisis.get('señal_identificada')}\033[0m")
        
        # [PASO 3 DEL LOOP: RAZONAR 🧐]
        print(f"\033[1;36m🧠 [LOOP: PASO 3 - RAZONAR 🧐] -> {log_ia}\033[0m")
        
        # [PASO 6 DEL LOOP: VERIFICAR ✅]
        print(f"\033[1;32m✅ [LOOP: PASO 6 - VERIFICAR ✅] -> {log_verif}\033[0m")
        
        # Logs de slots detallados
        print(f"   👤 Rival: {datos.get('rival')} | 📅 Día: {datos.get('dia')} | ⏰ Hora: {datos.get('hora')}")
            
        print(f"\033[1;92m🚀 [INTENCIÓN FINAL] -> {resultado.get('tipo').upper()}\033[0m")
        print("\033[1;95m" + "="*85 + "\033[0m\n")
        
        return resultado

    except Exception as e:
        print(f"\033[1;31m❌ [ERROR CRÍTICO EN OÍDO] -> {e}\033[0m")
        return {"tipo": "chat_general", "datos": {}, "confianza": "error"}
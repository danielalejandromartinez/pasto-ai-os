import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def enviar_whatsapp(telefono_destino, mensaje):
    """
    EL RELEVISTA DE MENSAJES:
    Envía mensajes reales a Meta y reporta el estado exacto de la entrega.
    """
    # 🎨 LOG DE INTENCIÓN - Azul
    print(f"\n\033[1;94m📤 [WHATSAPP SERVICE] -> Intentando enviar a {telefono_destino}...\033[0m")
    
    # Modo Laboratorio (Si faltan llaves)
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("\033[1;33m⚠️ [SISTEMA] Modo Simulación activo (Falta Token o ID en .env).\033[0m")
        print(f"\033[90mContenido: \"{mensaje}\"\033[0m\n")
        return {"exito": True, "simulado": True}

    # Configuración de la "Antena" de Meta
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # El paquete de datos oficial
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefono_destino,
        "type": "text",
        "text": {"body": mensaje}
    }

    try:
        # 🚀 LANZAMIENTO
        response = requests.post(url, headers=headers, json=data)
        res_json = response.json()

        # 🔍 VERIFICACIÓN DE RADAR (Lo que Meta responde)
        if response.status_code == 200:
            print(f"\033[1;92m🟢 [ÉXITO DE ENTREGA] -> Mensaje aceptado por Meta.")
            print(f"🆔 ID Mensaje: {res_json.get('messages', [{}])[0].get('id')}\033[0m\n")
            return {"exito": True, "data": res_json}
        else:
            # 🔴 LOG DE ERROR DETALLADO - Aquí sabremos por qué no llega
            print(f"\033[1;91m🔴 [ERROR DE META] -> Código: {response.status_code}")
            print(f"❌ Detalle: {json.dumps(res_json, indent=2)}\033[0m\n")
            
            # Tip para el desarrollador
            if response.status_code == 401:
                print("\033[1;33m💡 SUGERENCIA: Tu WHATSAPP_TOKEN parece haber expirado. Renuévalo en el panel de Meta.\033[0m")
            
            return {"exito": False, "error": res_json}

    except Exception as e:
        print(f"\033[1;31m❌ [ERROR CRÍTICO] Fallo en la antena de red: {e}\033[0m")
        return {"exito": False}
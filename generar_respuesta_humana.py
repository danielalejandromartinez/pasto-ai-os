import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def redactar(resultado_accion: dict, usuario_contexto: dict):
    """
    LA VOZ DE ALEJANDRO V14.0 - EDICIÓN "SELLO DE SEGURIDAD MULTI-TENANT".
    Misión: Interfaz autónoma VIP. La IA genera el lenguaje, el sistema inyecta los datos críticos.
    """
    nombre_usuario = usuario_contexto.get("nombre", "Campeón")
    club_id = usuario_contexto.get("club_id", 1) # Obtenemos el ID real del club del usuario
    status = resultado_accion.get("status")
    
    # --- EXTRACCIÓN DE DATOS TÉCNICOS Y VISUALES ---
    datos_v = resultado_accion.get("datos_visuales", {})
    veredicto = resultado_accion.get("veredicto", {})
    perfil = resultado_accion.get("perfil_socio", {})
    orden_tecnica = resultado_accion.get("orden_ia") or resultado_accion.get("mensaje") or "Atiende al socio."
    
    # 🛡️ MARCADOR DE SEGURIDAD (Placeholder)
    # Alejandro NO escribirá links reales, usará esta etiqueta.
    MARCADOR_LINK = "{{LINK_RANKING}}"

    # 🎨 [LOG DE OBSERVABILIDAD]
    print(f"\033[37m[VOZ/ALEJANDRO] -> Redactando con Sello de Seguridad para Club ID: {club_id}\033[0m")

    # --- CONSTRUCCIÓN DEL DOSSIER REAL DEL SOCIO ---
    resumen_perfil_txt = "No disponible actualmente."
    if perfil:
        resumen_perfil_txt = f"""
        DATOS REALES DEL SOCIO {nombre_usuario}:
        - Categoría/Liga Actual: {perfil.get('categorias_activas')}
        - XP Acumulado: {perfil.get('xp_legado')}
        - Saldo en Wallet: ${perfil.get('creditos_wallet')}
        - Récord: {perfil.get('victorias')} victorias / {perfil.get('derrotas')} derrotas
        """

    # --- EL MANUAL DE PROTOCOLO AGÉNTICO (System Prompt Maestro) ---
    contexto_agente = f"""
    Eres Alejandro, el Gerente de Innovación del Club. ERES un anfitrión ejecutivo de gran lujo.
    
    ### EXPEDIENTE DEL SOCIO:
    {resumen_perfil_txt}

    REGLAS DE ORO DE COMUNICACIÓN (CRÍTICO):
    1. PROHIBIDO ESCRIBIR URLS: Tienes terminantemente prohibido inventar o escribir una dirección web (http/www). 
    2. SELLO DE SEGURIDAD: Siempre que necesites referenciar el sitio web o el ranking del club, escribe EXACTAMENTE este código: {MARCADOR_LINK}. El sistema lo reemplazará por el link correcto después.
    3. PRIORIDAD DE MISIÓN: Si la 'ORDEN TÉCNICA' solicita un dato, pídelo de forma clara. No te distraigas con el expediente.
    4. CERO COMPORTAMIENTO DE ASISTENTE: Habla como un Gerente de Élite. No digas "Claro", "Aquí tienes".
    5. BRANDING: Firma siempre con: "Innovación deportiva por Pasto.AI".
    """

    # --- MAPEADO DE MISIONES SEGÚN EL ESTADO DEL LOOP ---
    
    # A. BIENVENIDA
    if status == "welcome_new_socio":
        mision_ia = f"Bienvenida oficial. Pide selfie para activar su tarjeta VIP en el Muro de la Fama visitando {MARCADOR_LINK}."

    # B. FOTO APROBADA + PEDIR CATEGORÍA INICIAL
    elif status == "ask_initial_category":
        mision_ia = f"Felicita por la selfie. Informa que su tarjeta ya brilla en {MARCADOR_LINK}. Pide elegir categoría: {orden_tecnica}."

    # C. LIGA/CATEGORÍA ASIGNADA
    elif status == "category_assigned":
        mision_ia = f"Confirma categoría oficial. Perfil activo en {MARCADOR_LINK}. Invítalo al combate."

    # D. AUDITORÍA DE PAGO
    elif status == "payment_audited":
        if veredicto.get("es_valido"):
            mision_ia = f"Confirma recibo (Monto {datos_v.get('monto')}, Ref {datos_v.get('referencia')}). Éxito en {MARCADOR_LINK}."
        else:
            mision_ia = f"Error en pago: {veredicto.get('explicacion_detallada')}. Pide soporte para {MARCADOR_LINK}."

    # E. SLOT FILLING: CATEGORÍA
    elif status == "ask_category":
        mision_ia = f"Misión: El socio quiere retar. Cita categorías disponibles: {orden_tecnica}. Pide que elija una para agendar en {MARCADOR_LINK}."

    # F. SLOT FILLING: FECHAS Y HORAS
    elif status == "ask_date":
        mision_ia = f"Falta el día del reto. Pídelo para agendar en {MARCADOR_LINK}."

    elif status == "ask_time":
        mision_ia = f"Falta la HORA. Pídela con estilo ejecutivo para cerrar en {MARCADOR_LINK}."

    # G. COMANDOS ADMINISTRATIVOS
    elif status in ["config_success", "auth_success"]:
        mision_ia = f"Traduce éxito administrativo: {orden_tecnica}. Menciona el Muro de la Fama en {MARCADOR_LINK}."

    # H. FLUJO DE RETOS
    elif status in ["challenge_scheduled", "challenge_confirmed", "challenge_proposed"]:
        mision_ia = f"Traduce orden de duelo: {orden_tecnica}. Lenguaje épico. Cita {MARCADOR_LINK}."

    # I. CONSULTA O CHAT GENERAL
    else:
        mision_ia = f"""
        ORDEN TÉCNICA: {orden_tecnica}. 
        Responde usando expediente: {resumen_perfil_txt}. Termina con el link {MARCADOR_LINK} al Muro de la Fama.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": contexto_agente},
                {"role": "user", "content": mision_ia}
            ],
            temperature=0.3
        )
        
        texto_ia = response.choices[0].message.content
        
        # 🛡️ INYECCIÓN DINÁMICA DEL SISTEMA (Aquí es donde el código manda)
        # Construimos el link real basado en el Club del usuario
        link_real_club = f"https://pasto-ai-os.onrender.com/club/{club_id}"
        
        # Reemplazamos el marcador por la URL verdadera
        respuesta_final = texto_ia.replace(MARCADOR_LINK, link_real_club)
        
        print(f"\033[32m[VOZ/ALEJANDRO] -> Link inyectado con éxito para Club {club_id}\033[0m")
        return respuesta_final

    except Exception as e:
        print(f"❌ Error crítico en Voz: {e}")
        link_fallback = f"https://pasto-ai-os.onrender.com/club/{club_id}"
        return f"Estimado {nombre_usuario}, su solicitud ha sido procesada. Verifique en el Muro de la Fama: {link_fallback}. \n\nInnovación deportiva por Pasto.AI"
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def redactar(resultado_accion: dict, usuario_contexto: dict):
    """
    LA VOZ DE ALEJANDRO V13.0 - EDICIÓN "ENFOQUE EN MISIÓN".
    Misión: Interfaz autónoma VIP con jerarquía de prioridades y conciencia de datos.
    """
    nombre_usuario = usuario_contexto.get("nombre", "Campeón")
    status = resultado_accion.get("status")
    
    # --- EXTRACCIÓN DE DATOS TÉCNICOS Y VISUALES ---
    datos_v = resultado_accion.get("datos_visuales", {})
    veredicto = resultado_accion.get("veredicto", {})
    perfil = resultado_accion.get("perfil_socio", {}) # El expediente que viene del Orquestador
    orden_tecnica = resultado_accion.get("orden_ia") or resultado_accion.get("mensaje") or "Atiende al socio."
    
    # 🚀 LINK OFICIAL PARA LA DEMO
    link_ranking = "https://consoles-untitled-mail-shake.trycloudflare.com/club/1"

    # 🎨 [LOG DE OBSERVABILIDAD]
    print(f"\033[37m[VOZ/ALEJANDRO] -> Ejecutando Comunicación de Alta Gama para: {status}\033[0m")

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
    Eres Alejandro, el Gerente de Innovación del Club Colombia. ERES un anfitrión ejecutivo de gran lujo.
    
    ### EXPEDIENTE DEL SOCIO:
    {resumen_perfil_txt}

    REGLAS DE ORO DE COMUNICACIÓN (CRÍTICO):
    1. PRIORIDAD DE MISIÓN: Si la 'ORDEN TÉCNICA' solicita un dato (categoría, día, hora), tu prioridad número uno es pedir ese dato de forma clara. NO permitas que los datos del expediente (puntos/saldo) distraigan al socio de completar la acción.
    2. CONCIENCIA DE DATOS: Usa el expediente para personalizar, pero no para charlar sin sentido. Ejemplo: Si el socio pregunta cuánto tiene, responde con el saldo exacto del expediente.
    3. PROHIBIDO INVENTAR: No uses sinónimos para categorías. Si la orden dice "Pro, Intermedio, Novato", usa esos nombres EXACTAMENTE.
    4. CERO COMPORTAMIENTO DE ASISTENTE: Prohibido decir "Claro", "Aquí tienes", "Esta es la versión". Habla como un Gerente Real.
    5. IDENTIDAD: Solo preséntate como Alejandro en 'welcome_new_socio'.
    6. BRANDING: Firma siempre con: "Innovación deportiva por Pasto.AI".
    7. SEGUNDA PERSONA: Dirígete al socio con absoluta distinción y respeto (Tú/Usted).
    """

    # --- MAPEADO DE MISIONES SEGÚN EL ESTADO DEL LOOP ---
    
    # A. BIENVENIDA (Presentación oficial)
    if status == "welcome_new_socio":
        mision_ia = f"Bienvenida oficial. Preséntate. Explica que inicia con 0.0 XP como Fundador y pide selfie para activar su tarjeta VIP en {link_ranking}."

    # B. FOTO APROBADA + PEDIR CATEGORÍA INICIAL
    elif status == "ask_initial_category":
        mision_ia = f"Felicita por la selfie. Informa que su tarjeta ya brilla en {link_ranking}. Ahora pide elegir su categoría entre las opciones literales: {orden_tecnica}."

    # C. LIGA/CATEGORÍA ASIGNADA
    elif status == "category_assigned":
        mision_ia = f"Confirma que ya pertenece a la categoría oficial. Perfil 100% activo en {link_ranking}. Invítalo al combate."

    # D. AUDITORÍA DE PAGO (EFECTO WOW)
    elif status == "payment_audited":
        if veredicto.get("es_valido"):
            mision_ia = f"Confirma que VISTE el recibo mencionando: Monto {datos_v.get('monto')}, Fecha {datos_v.get('fecha')} y Referencia {datos_v.get('referencia')}. Informa éxito en {link_ranking}."
        else:
            mision_ia = f"Informa error en el pago: {veredicto.get('explicacion_detallada')}. Pide el soporte correcto para {link_ranking}."

    # E. SLOT FILLING: PEDIR CATEGORÍA PARA UN RETO (AQUÍ CORREGIMOS EL FALLO)
    elif status == "ask_category":
        mision_ia = f"""
        ORDEN TÉCNICA: El socio quiere retar pero NO especificó la categoría. 
        Misión: Debes citar las categorías disponibles en el club según esta lista: {orden_tecnica}. 
        Pídele a {nombre_usuario} que elija en cuál desea agendar el duelo. 
        IMPORTANTE: No te distraigas felicitándolo por sus puntos, ve directo a la pregunta de la categoría.
        """

    # F. SLOT FILLING: FECHAS Y HORAS
    elif status == "ask_date":
        mision_ia = f"ORDEN: Falta el día del reto. Pide el día exacto para agendar en {link_ranking}. Puedes mencionar que Maria Paula (o el rival) ya está esperando."

    elif status == "ask_time":
        mision_ia = f"ORDEN: Falta la HORA del reto. Pídela con estilo ejecutivo para cerrar el agendamiento en {link_ranking}."

    # G. COMANDOS ADMINISTRATIVOS (CONFIGURACIÓN Y AUTORIZACIÓN)
    elif status in ["config_success", "auth_success"]:
        mision_ia = f"Traduce este éxito administrativo: {orden_tecnica}. Mantén el tono institucional y menciona {link_ranking}."

    # H. FLUJO DE RETOS (HANDSHAKES)
    elif status in ["challenge_scheduled", "challenge_confirmed", "challenge_proposed"]:
        mision_ia = f"Traduce esta orden de duelo: {orden_tecnica}. Usa lenguaje épico. Cita el Muro de la Riqueza en {link_ranking}."

    # I. CONSULTA O CHAT GENERAL (USO DE CONCIENCIA)
    else:
        mision_ia = f"""
        ORDEN TÉCNICA: {orden_tecnica}. 
        El socio puede estar preguntando sobre su estatus personal. Responde de forma humana usando los datos de su expediente: {resumen_perfil_txt}. 
        Ignora errores de ortografía del usuario. Termina con el link {link_ranking}.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": contexto_agente},
                {"role": "user", "content": mision_ia}
            ],
            temperature=0.3 # Mayor consistencia, menor creatividad.
        )
        
        respuesta_final = response.choices[0].message.content
        print(f"\033[37m[VOZ/ALEJANDRO] -> Comunicación VIP con jerarquía de misión generada.\033[0m")
        return respuesta_final

    except Exception as e:
        print(f"❌ Error crítico en Voz: {e}")
        return f"Estimado {nombre_usuario}, su solicitud ha sido procesada con éxito. Le invito a visualizar los detalles en el Muro de la Riqueza: {link_ranking}. \n\nInnovación deportiva por Pasto.AI"
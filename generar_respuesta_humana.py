import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def redactar(resultado_accion: dict, usuario_contexto: dict):
    """
    LA VOZ DE ALEJANDRO V19.0 - EDICIÓN "EFICIENCIA DE ÉLITE".
    Misión: Prestigio sin fricción. Paso 8: Ajustar Comportamiento para el cierre de misiones.
    """
    nombre_usuario = usuario_contexto.get("nombre", "Campeón")
    club_id = usuario_contexto.get("club_id", 1)
    status = resultado_accion.get("status")
    
    if "nuevo_club_id" in resultado_accion:
        club_id = resultado_accion["nuevo_club_id"]
    
    # --- EXTRACCIÓN DE DATOS TÉCNICOS ---
    perfil = resultado_accion.get("perfil_socio", {})
    orden_tecnica = resultado_accion.get("orden_ia") or resultado_accion.get("mensaje") or "Atiende al socio con distinción."
    
    # 🛡️ SELLO DE SEGURIDAD (Marcador de link)
    MARCADOR_LINK = "{{LINK_RANKING}}"

    # 🎨 [LOG DE OBSERVABILIDAD]
    print(f"\033[37m[VOZ/ALEJANDRO] -> Ejecutando Paso 8 (Ajustar) para: {nombre_usuario} | Contexto: {status}\033[0m")

    # --- CONSTRUCCIÓN DE LA CONCIENCIA SITUACIONAL ---
    resumen_perfil_txt = "Identidad en proceso de sincronización."
    if perfil:
        resumen_perfil_txt = f"""
        EXPEDIENTE REAL DE {nombre_usuario}:
        - Liga: {perfil.get('categorias_activas')}
        - Legado Acumulado: {perfil.get('xp_legado')} XP
        - Récord: {perfil.get('victorias')} victorias / {perfil.get('derrotas')} derrotas
        """

    contexto_agente = f"""
    Eres Alejandro, el Gerente de Innovación del Club. ERES un anfitrión de ultra-lujo y Embajador de Pasto.AI.
    Tu voz es la de un mentor estratégico: distinguido, pero EFICIENTE y RESOLUTIVO.

    ### CONCIENCIA DEL SOCIO:
    {resumen_perfil_txt}

    ### REGLAS DE ORO DE COMUNICACIÓN (INNEGOCIABLES):
    1. IDENTIDAD: Llama al socio siempre por su nombre: {nombre_usuario}.
    2. SEGURIDAD: PROHIBIDO inventar URLs. Usa ÚNICAMENTE el marcador {MARCADOR_LINK}.
    3. FOCO EN LA MISIÓN: Si la 'ORDEN TÉCNICA' te pide un dato (día, hora, rival), tu mensaje debe ser corto y directo a la pregunta. No des discursos largos que distraigan al usuario de responder lo que falta.
    4. TONO: Ejecutivo de alta gama. Menos es más. 
    5. BRANDING: Firma siempre: "Innovación deportiva por Pasto.AI".
    """

    # --- MAPEADO DE MISIONES ESTRATÉGICAS (PASO 8) ---
    if status == "welcome_new_socio":
        mision_ia = f"Bienvenida VIP a {nombre_usuario}. Pide la selfie de forma elegante para activar su tarjeta en {MARCADOR_LINK}."

    elif status == "ask_date":
        # 🆕 AJUSTE: Más directo, menos discurso.
        mision_ia = f"El socio quiere un reto. Pregúntale de forma directa y distinguida qué día desea agendar el duelo. No lo mandes a ver el link para esto, pregúntaselo tú."

    elif status == "ask_time":
        mision_ia = f"Ya tenemos el día. Ahora pídele la hora exacta con brevedad ejecutiva para cerrar el agendamiento."

    elif status == "reporte_analitico":
        mision_ia = f"Actúa como estratega. Usa los datos {orden_tecnica} para motivar a {nombre_usuario} en {MARCADOR_LINK}."

    elif status == "config_success":
        mision_ia = f"ÉXITO DE EXPANSIÓN. Confirma que el nuevo territorio del Imperio está listo: {orden_tecnica}. Cita {MARCADOR_LINK}."

    elif status == "challenge_scheduled":
        mision_ia = f"DUELO LANZADO. Confirma que el reto ha sido enviado al rival. Lenguaje épico corto. Cita {MARCADOR_LINK}."

    else:
        mision_ia = f"ORDEN DEL SISTEMA: {orden_tecnica}. Responde con distinción a {nombre_usuario} y menciona el link {MARCADOR_LINK}."

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
        
        base_url = "https://pasto-ai-os.onrender.com"
        if not os.getenv("DATABASE_URL") or "postgres" not in os.getenv("DATABASE_URL"):
            base_url = "http://localhost:8000"

        link_real = f"{base_url}/club/{club_id}"
        respuesta_final = texto_ia.replace(MARCADOR_LINK, link_real)
        
        print(f"\033[32m[VOZ/ALEJANDRO] -> Respuesta optimizada para {nombre_usuario} generada.\033[0m")
        return respuesta_final

    except Exception as e:
        print(f"❌ Error crítico en Voz: {e}")
        link_fallback = f"http://localhost:8000/club/{club_id}"
        return f"Estimado {nombre_usuario}, su solicitud ha sido procesada. Verifique en el Muro de la Fama: {link_fallback}. \n\nInnovación deportiva por Pasto.AI"
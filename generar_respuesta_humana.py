import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def redactar(resultado_accion: dict, usuario_contexto: dict):
    """
    LA VOZ DE ALEJANDRO V16.0 - EDICIÓN "ESTRATEGA DE ÉLITE".
    Misión: Transformar datos en prestigio. Paso 8 del Loop: Ajustar Comportamiento para máxima retención.
    """
    nombre_usuario = usuario_contexto.get("nombre", "Campeón")
    club_id = usuario_contexto.get("club_id", 1)
    status = resultado_accion.get("status")
    
    # --- EXTRACCIÓN DE DATOS TÉCNICOS ---
    datos_v = resultado_accion.get("datos_visuales", {})
    veredicto = resultado_accion.get("veredicto", {})
    perfil = resultado_accion.get("perfil_socio", {})
    orden_tecnica = resultado_accion.get("orden_ia") or resultado_accion.get("mensaje") or "Atiende al socio con distinción."
    
    # 🛡️ SELLO DE SEGURIDAD (Placeholder inyectado por el sistema)
    MARCADOR_LINK = "{{LINK_RANKING}}"

    # 🎨 [LOG DE OBSERVABILIDAD]
    print(f"\033[37m[VOZ/ALEJANDRO] -> Ejecutando Paso 8 (Ajustar) para: {nombre_usuario}\033[0m")

    # --- CONSTRUCCIÓN DE LA CONCIENCIA SITUACIONAL ---
    resumen_perfil_txt = "Identidad en proceso de sincronización."
    if perfil:
        resumen_perfil_txt = f"""
        EXPEDIENTE REAL DE {nombre_usuario}:
        - Liga: {perfil.get('categorias_activas')}
        - Legado Acumulado: {perfil.get('xp_legado')} XP
        - Créditos: ${perfil.get('creditos_wallet')}
        - Historial: {perfil.get('victorias')} victorias / {perfil.get('derrotas')} derrotas
        """

    # --- 📜 CONSTITUCIÓN DE PRESTIGIO 2030 ---
    reglamento_resumido = """
    REGLAS DE ORO DEL CLUB:
    - Valentía: Jugar siempre suma (10 pts por ganar, 3 pts por participar).
    - Calidad: Solo los 24 mejores resultados definen tu posición en la Temporada.
    - Reconocimiento: El líder mensual gana la Medalla y el Aura Neón. Las Estrellas de Temporada son para siempre.
    """

    contexto_agente = f"""
    Eres Alejandro, el Gerente de Innovación del Club. ERES un anfitrión de ultra-lujo.
    Tu voz es la de un mentor estratégico que valora el tiempo y el prestigio de los socios.

    ### CONCIENCIA DEL SOCIO:
    {resumen_perfil_txt}

    ### REGLAMENTO DE LA ARENA:
    {reglamento_resumido}

    REGLAS DE ORO DE COMUNICACIÓN (INNEGOCIABLES):
    1. IDENTIDAD: Llama al socio siempre por su nombre: {nombre_usuario}.
    2. SEGURIDAD: PROHIBIDO inventar URLs. Usa ÚNICAMENTE el marcador {MARCADOR_LINK}.
    3. TONO ESTRATÉGICO: No informes, MOTIVA. Usa el expediente para mostrarle el camino a la cima (Estrellas/Medallas).
    4. CERO COMPORTAMIENTO ROBÓTICO: Eres el anfitrión del Imperio. No pidas perdón por ser una IA, actúa como un humano de alto nivel.
    5. BRANDING: Firma siempre: "Innovación deportiva por Pasto.AI".
    """

    # --- MAPEADO DE MISIONES ESTRATÉGICAS ---
    if status == "welcome_new_socio":
        mision_ia = f"Bienvenida de Élite a {nombre_usuario}. Explica que su Beca de Innovación está activa con 0 XP. Pide la selfie para que su tarjeta neón brille en {MARCADOR_LINK}."

    elif status == "reporte_analitico":
        mision_ia = f"Actúa como un estratega de alto rendimiento. Usa los datos {orden_tecnica} para decirle a {nombre_usuario} exactamente cuántas victorias le faltan para subir de puesto o ganar la Medalla en {MARCADOR_LINK}."

    elif status == "challenge_scheduled":
        mision_ia = f"Duelo agendado. Eleva la importancia del desafío contra el rival. Menciona que el resultado impactará su Legado en {MARCADOR_LINK}."

    elif status == "agradecimiento_final":
        mision_ia = f"El socio te dio las gracias. Responde como el anfitrión de un club exclusivo. Despídete invitándolo a la Arena. Cita {MARCADOR_LINK}."

    else:
        mision_ia = f"ORDEN DEL SISTEMA: {orden_tecnica}. Responde con distinción. Si el socio tiene un reto pendiente o puntos por ganar, recuérdaselo usando el Reglamento 2030 y el link {MARCADOR_LINK}."

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": contexto_agente},
                {"role": "user", "content": mision_ia}
            ],
            temperature=0.4 # Un toque de calidez humana sin perder precisión
        )
        
        texto_ia = response.choices[0].message.content
        
        # 🛡️ INYECCIÓN DINÁMICA (Bilingüe: Local vs Producción)
        base_url = "https://pasto-ai-os.onrender.com"
        if not os.getenv("DATABASE_URL") or "postgres" not in os.getenv("DATABASE_URL"):
            base_url = "http://localhost:8000"

        link_real = f"{base_url}/club/{club_id}"
        respuesta_final = texto_ia.replace(MARCADOR_LINK, link_real)
        
        print(f"\033[32m[VOZ/ALEJANDRO] -> Comunicación de Élite para {nombre_usuario} enviada.\033[0m")
        return respuesta_final

    except Exception as e:
        print(f"❌ Error crítico en Voz: {e}")
        link_fallback = f"http://localhost:8000/club/{club_id}"
        return f"Estimado {nombre_usuario}, su solicitud ha sido procesada con éxito. Siga su camino a la gloria aquí: {link_fallback}. \n\nInnovación deportiva por Pasto.AI"
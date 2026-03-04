def tomar_decision(intencion: dict, usuario_contexto: dict):
    """
    Motor de Decisión con SEGURIDAD DE LISTA BLANCA.
    Fusiona la lógica de seguridad con la lógica de negocio existente.
    """
    tipo_intencion = intencion.get("tipo")
    datos_ia = intencion.get("datos", {})
    
    rol_usuario = usuario_contexto.get("rol")
    telefono = usuario_contexto.get("telefono")
    club_id = usuario_contexto.get("club_id")
    nombre_usuario = usuario_contexto.get("nombre")

    # ============================================================
    # 🛡️ ZONA DE SEGURIDAD (EL PORTERO)
    # ============================================================

    # 1. BLOQUEO A DESCONOCIDOS
    if rol_usuario == "NO_AUTORIZADO":
        return {
            "accion": "responder_texto",
            "respuesta": "🔒 Hola. Este es un servicio exclusivo para socios del Club. Tu número no aparece en nuestra lista autorizada. Por favor actualiza tus datos en la recepción."
        }

    # 2. BIENVENIDA AUTOMÁTICA (SOCIO NUEVO DEL EXCEL)
    # Si está en la lista blanca pero es su primera vez, le creamos el perfil automáticamente.
    if rol_usuario == "SOCIO_NUEVO":
        return {
            "accion": "crear_perfil_db",
            "datos": {
                "nombre": nombre_usuario, # Este nombre viene del Excel (WhiteList)
                "categoria": "General",
                "padrino_telefono": telefono,
                "club_id": club_id
            }
        }

    # ============================================================
    # 🧠 ZONA DE LÓGICA DE NEGOCIO (TU CÓDIGO PROBADO)
    # ============================================================

    # --- REGLA 1: CREACIÓN DE JUGADORES (Manual por Admin) ---
    if tipo_intencion == "crear_jugador":
        # Como el sistema ya crea socios automáticamente, esto queda solo para Admins
        if rol_usuario not in ["ADMIN", "SUPER_ADMIN"]:
             return {"accion": "responder_texto", "respuesta": "Tu perfil ya está activo y verificado."}
             
        nombre = datos_ia.get("nombre_detectado")
        categoria = datos_ia.get("categoria_detectada", "General")
        
        if not nombre:
            return {"accion": "responder_texto", "respuesta": "Necesito el nombre para crearlo."}
            
        return {
            "accion": "crear_perfil_db",
            "datos": {
                "nombre": nombre,
                "categoria": categoria,
                "padrino_telefono": telefono,
                "club_id": club_id
            }
        }

    # --- REGLA 2: RETOS (1 vs 1) - LÓGICA BLINDADA ---
    if tipo_intencion == "crear_reto":
        rival = datos_ia.get("rival_detectado")
        fecha = datos_ia.get("fecha_iso") # Capturamos la fecha
        
        # A. LÓGICA DE IDENTIDAD (ADMIN vs JUGADOR)
        if rol_usuario in ["ADMIN", "SUPER_ADMIN"] and datos_ia.get("nombre_detectado"):
             retador = datos_ia.get("nombre_detectado")
        else:
             retador = usuario_contexto.get("nombre")

        # B. VALIDACIONES BÁSICAS
        if not rival: 
            return {"accion": "responder_texto", "respuesta": "¿Contra quién es el reto?"}
            
        if retador == "Desconocido" or "Admin" in retador:
             return {"accion": "responder_texto", "respuesta": "Error de identidad. No puedo procesar el reto."}

        # C. REGLA DE ORO: FECHA OBLIGATORIA
        if not fecha:
            return {
                "accion": "responder_texto",
                "respuesta": "📅 Para agendar el reto, necesito saber el día y la hora exacta. (Ej: 'Mañana a las 5pm')"
            }

        # D. SI TENEMOS TODO, AGENDAMOS
        return {
            "accion": "agendar_reto_db",
            "datos": {
                "retador": retador, 
                "rival": rival, 
                "club_id": club_id,
                "fecha_iso": fecha
            }
        }

    # --- REGLA 3: GESTIÓN DE TORNEOS (Solo Admins) ---
    if tipo_intencion == "crear_torneo":
        if rol_usuario not in ["ADMIN", "SUPER_ADMIN"]:
            return {"accion": "responder_texto", "respuesta": "🚫 Solo el Administrador puede crear torneos."}
            
        nombre_torneo = datos_ia.get("nombre_detectado", "Torneo Express")
        return {
            "accion": "crear_torneo_db",
            "datos": {"nombre": nombre_torneo, "club_id": club_id}
        }

    # --- REGLA 4: INSCRIBIR EN TORNEO ---
    if tipo_intencion == "inscribir_en_torneo":
        nombre = datos_ia.get("nombre_detectado")
        if not nombre: 
            nombre = usuario_contexto.get("nombre")
            if nombre == "Desconocido": return {"accion": "responder_texto", "respuesta": "¿A quién inscribo?"}
        
        return {
            "accion": "inscribir_torneo_db",
            "datos": {
                "nombre_jugador": nombre, 
                "club_id": club_id, 
                "padrino_telefono": telefono
            }
        }

    # --- REGLA 5: GENERAR CUADROS (Solo Admin) ---
    if tipo_intencion == "generar_cuadros":
        if rol_usuario not in ["ADMIN", "SUPER_ADMIN"]:
            return {"accion": "responder_texto", "respuesta": "🚫 Solo el Admin puede iniciar el torneo."}
        
        return {
            "accion": "generar_cuadros_db",
            "datos": {"club_id": club_id}
        }

    # --- REGLA 6: REGISTRAR RESULTADOS ---
    if tipo_intencion == "registrar_resultado":
        reportante = usuario_contexto.get("nombre")
        
        if reportante == "Desconocido":
            return {"accion": "responder_texto", "respuesta": "No sé quién eres. Regístrate primero."}

        return {
            "accion": "registrar_resultado_db",
            "datos": {
                "marcador": datos_ia.get("marcador_detectado"),
                "club_id": club_id,
                "reportante": reportante
            }
        }

    # --- REGLA 7: CREAR CLUB (SaaS) ---
    if tipo_intencion == "crear_nuevo_club":
        if rol_usuario != "SUPER_ADMIN": return {"accion": "responder_texto", "respuesta": "Acceso denegado."}
        return {
            "accion": "crear_club_saas",
            "datos": {"nombre": datos_ia.get("nombre_club"), "admin_phone": datos_ia.get("telefono_admin")}
        }

    # --- REGLA 8: CHAT GENERAL ---
    if tipo_intencion == "chat_general":
        return {"accion": "generar_respuesta_ia", "datos": {}}

    # --- REGLA 9: CONSULTAR RANKING ---
    if tipo_intencion == "consultar_ranking":
        return {
            "accion": "consultar_ranking_db",
            "datos": {"club_id": club_id}
        }

    return {"accion": "esperar", "datos": {}}
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import or_, func
from agents.membership_agent import MembershipAgent
from agents.booking_agent import BookingAgent
from agents.finance_agent import FinanceAgent
from agents.ranking_agent import RankingAgent # ✅ NUEVO COMPONENTE DEL ENJAMBRE
from models import Player, WhatsAppUser, Match, TaskQueue, PointTransaction, Category, WhiteList
from datetime import datetime, timedelta
import json
import os

class Orchestrator:
    def __init__(self, db: Session, usuario_contexto: dict):
        self.db = db
        self.contexto = usuario_contexto
        self.membership = MembershipAgent(db)
        self.booking = BookingAgent(db)
        self.finance = FinanceAgent()
        self.ranking = RankingAgent(db) # ✅ INICIALIZAMOS AL ANALISTA DE DATOS

    def _extraer_expediente_socio(self, jugador: Player):
        """
        [PASO 7 DEL LOOP: APRENDER 📚]
        Extrae la radiografía técnica del jugador para inyectar conciencia en la Voz.
        Misión: Que Alejandro sepa quién es el socio antes de hablar.
        """
        if not jugador:
            return None
        
        # Obtenemos los nombres de las categorías donde compite literalmente
        categorias_nombres = [c.name for c in jugador.categories] if jugador.categories else ["General"]
        
        # Construimos el paquete de datos de "Conciencia Situacional"
        return {
            "nombre_oficial": jugador.name,
            "xp_legado": int(jugador.eternal_points),
            "creditos_wallet": float(jugador.wallet_balance),
            "victorias": jugador.wins,
            "derrotas": jugador.losses,
            "categorias_activas": ", ".join(categorias_nombres),
            "logros": jugador.achievements if jugador.achievements else {}
        }

    def procesar_intencion(self, intencion: dict):
        """
        MOTOR AGÉNTICO V17.5 - EDICIÓN ANALÍTICA Y PREDICTIVA.
        Misión: Gestión autónoma total con distinción de privilegios y análisis de competencia.
        """
        tipo = intencion.get("tipo")
        datos_nuevos = intencion.get("datos", {})
        telefono = self.contexto.get("telefono")
        club_id = self.contexto.get("club_id")
        rol = self.contexto.get("rol")
        nombre_contexto = self.contexto.get("nombre", "Socio")
        
        # ============================================================
        # 🛡️ CAPA 1: SEGURIDAD (WHITELIST)
        # ============================================================
        if rol == "NO_AUTORIZADO":
            return {
                "status": "access_denied",
                "orden_ia": "ORDEN: Informe con distinción que el acceso es exclusivo para socios autorizados."
            }

        # 1. [OBSERVAR] - Identificación de Usuario y Memoria Persistente
        usuario_db = self.db.query(WhatsAppUser).filter_by(phone_number=telefono).first()
        if not usuario_db:
            usuario_db = WhatsAppUser(phone_number=telefono, memory={"step": "idle", "slots_reto": {}})
            self.db.add(usuario_db); self.db.commit(); self.db.refresh(usuario_db)

        if not usuario_db.memory: 
            usuario_db.memory = {"step": "idle", "slots_reto": {}}
        if "slots_reto" not in usuario_db.memory: 
            usuario_db.memory["slots_reto"] = {}
            flag_modified(usuario_db, "memory")

        jugador = usuario_db.players[0] if usuario_db and usuario_db.players else None
        
        # ============================================================
        # 📚 PASO 7 DEL LOOP: APRENDER (CONCIENCIA DE PERFIL)
        # ============================================================
        expediente = self._extraer_expediente_socio(jugador)
        if expediente:
            print(f"\033[1;95m[LOOP: PASO 7 - APRENDER 📚] -> Alejandro cargó el expediente de {jugador.name}: {expediente['xp_legado']} XP.\033[0m")

        # ============================================================
        # 🛠️ CAPA 2: COMANDOS ADMINISTRATIVOS (GLOBALES / CEO)
        # ============================================================
        
        # A. AUTORIZAR NUEVO SOCIO
        if tipo == "autorizar_socio" and rol in ["SUPER_ADMIN", "ADMIN"]:
            tel_a_autorizar = datos_nuevos.get("telefono_a_autorizar")
            nombre_invitado = datos_nuevos.get("nombre_a_autorizar") or "Socio Invitado"
            if not tel_a_autorizar:
                return {"status": "info", "perfil_socio": expediente, "orden_ia": "ORDEN: Solicite el número de teléfono."}
            try:
                print(f"\033[1;31m⚡ [COMANDO CEO] -> Autorizando acceso para: {tel_a_autorizar}\033[0m")
                nueva_aut = WhiteList(phone_number=tel_a_autorizar, full_name=nombre_invitado, club_id=club_id, is_active=True)
                self.db.add(nueva_aut); self.db.commit()
                print(f"\033[1;32m🔐 [DB_ACTION] -> WhiteList actualizada.\033[0m")
                return {"status": "auth_success", "perfil_socio": expediente, "orden_ia": f"ORDEN: Confirme que el socio {nombre_invitado} ha sido habilitado."}
            except Exception as e:
                self.db.rollback(); return {"status": "error", "orden_ia": "ORDEN: Error técnico en autorización."}

        # B. CONFIGURAR MENÚ DE CATEGORÍAS
        if tipo == "configurar_categorias" and rol in ["SUPER_ADMIN", "ADMIN"]:
            nuevas_cats = datos_nuevos.get("lista_categorias", [])
            if nuevas_cats:
                print(f"\033[1;34m[RELEVO] -> Orquestador DELEGA a DB la actualización de categorías.\033[0m")
                try:
                    self.db.query(Category).filter_by(club_id=club_id).delete()
                    for c in nuevas_cats: self.db.add(Category(name=c.strip().capitalize(), club_id=club_id))
                    self.db.commit()
                    return {"status": "config_success", "perfil_socio": expediente, "orden_ia": f"ORDEN: Confirme que las categorías ({', '.join(nuevas_cats)}) han sido habilitadas."}
                except Exception as e:
                    self.db.rollback(); return {"status": "error", "orden_ia": "ORDEN: Error técnico en configuración."}

        # ============================================================
        # 📊 CAPA 3: ANÁLISIS ESTRATÉGICO Y PREDICTIVO (WOW EFFECT)
        # ============================================================
        if tipo == "consultar_analitica" and jugador:
            print(f"\033[1;34m[RELEVO/LOOP 3] -> Orquestador DELEGA a RankingAgent para análisis predictivo.\033[0m")
            objetivo = datos_nuevos.get("objetivo_analitico")
            rival_ref = datos_nuevos.get("rival_referencia")
            
            # El analista de datos hace su magia matemática
            reporte_analista = self.ranking.analizar_competencia(jugador.id, rival_ref)
            
            print(f"\033[1;32m[RETORNO/LOOP 6] <- RankingAgent entrega proyección de éxito para {jugador.name}.\033[0m")
            
            return {
                "status": "reporte_analitico",
                "perfil_socio": expediente,
                "analisis": reporte_analista,
                "orden_ia": f"ORDEN: Actúe como un estratega de élite. Use los datos {json.dumps(reporte_analista)} para motivar al socio y mostrarle su camino exacto a la cima del ranking."
            }

        # ============================================================
        # 🛡️ CAPA 4: REGISTRO Y ONBOARDING
        # ============================================================
        if not jugador and rol in ["SOCIO_NUEVO", "SUPER_ADMIN"]:
            print(f"\033[1;34m[RELEVO] -> Orquestador DELEGA a MembershipAgent para registro inicial.\033[0m")
            return self.membership.registrar_jugador(nombre_contexto, telefono, club_id)

        if not jugador: return {"status": "chat", "orden_ia": "ORDEN: Sincronizando acceso de socio."}

        paso_actual = usuario_db.memory.get("step", "idle")
        tiene_foto = True if (jugador and jugador.avatar_url) else False

        # ACCIÓN: UNIRSE A CATEGORÍA
        if tipo == "unirse_categoria" or (paso_actual == "waiting_category" and datos_nuevos.get("categoria")):
            print(f"\033[1;34m[RELEVO] -> Orquestador DELEGA a Membership para cambio de categoría.\033[0m")
            res_vinculo = self.membership.vincular_categoria(telefono, datos_nuevos.get("categoria"))
            res_vinculo["perfil_socio"] = self._extraer_expediente_socio(jugador)
            return res_vinculo

        if tipo == "enviar_comprobante":
            if not tiene_foto:
                return self.membership.actualizar_foto(telefono, f"static/profiles/{telefono}.jpg")
            else:
                reporte_pago = self.finance.auditar_recibo(f"static/profiles/{telefono}.jpg")
                if reporte_pago:
                    return {"status": "payment_audited", "perfil_socio": expediente, "datos_visuales": reporte_pago["analisis_visual"], "veredicto": reporte_pago["veredicto"], "orden_ia": "ORDEN: Confirme pago."}

        if not tiene_foto: return {"status": "remind_selfie", "orden_ia": f"ORDEN: Pida la selfie obligatoria."}

        # ============================================================
        # 🚀 SECCIÓN DE ACCIONES DE CAMPO (DUELOS Y CORTESÍA)
        # ============================================================
        print(f"\033[1;36m[CEREBRO/ORQUESTADOR] -> Analizando acción de {jugador.name} | Intento: {tipo}\033[0m")

        if tipo == "agradecimiento":
            print(f"\033[1;93m✨ [EMPATÍA] -> Respondiendo a la cortesía de {jugador.name}.\033[0m")
            return {"status": "agradecimiento_final", "perfil_socio": expediente, "orden_ia": "ORDEN: Responda con elegancia humana y despídase como anfitrión."}

        if tipo == "crear_reto":
            slots = usuario_db.memory.get("slots_reto", {})
            for k in ["rival", "dia", "hora", "fecha_iso", "categoria"]:
                val = datos_nuevos.get(k)
                if val and str(val).lower() not in ["null", "none", "unknown"]: slots[k] = val
            usuario_db.memory["slots_reto"] = slots
            flag_modified(usuario_db, "memory"); self.db.commit()

            if not slots.get("rival"): return {"status": "explain_challenge", "perfil_socio": expediente, "orden_ia": "ORDEN: Pida el rival."}
            categorias_club = self.db.query(Category).filter_by(club_id=club_id).all()
            if len(categorias_club) > 1 and not slots.get("categoria"):
                return {"status": "ask_category", "perfil_socio": expediente, "orden_ia": f"ORDEN: Pregunte la categoría: {', '.join([c.name for c in categorias_club])}."}
            if not slots.get("dia"): return {"status": "ask_date", "perfil_socio": expediente, "orden_ia": f"ORDEN: ¿Qué día para el reto contra {slots['rival']}?"}
            if not slots.get("hora"): return {"status": "ask_time", "perfil_socio": expediente, "orden_ia": f"ORDEN: ¿A qué hora el reto?"}

            print(f"\033[1;34m[RELEVO] -> Orquestador DELEGA a BookingAgent: {jugador.name} vs {slots['rival']}\033[0m")
            res_reto = self.booking.agendar_reto(jugador.name, slots["rival"], slots["fecha_iso"], club_id)
            if res_reto["status"] == "challenge_proposed":
                usuario_db.memory["slots_reto"] = {}; flag_modified(usuario_db, "memory"); self.db.commit()
                return {"status": "challenge_scheduled", "perfil_socio": expediente, "notificar_a": res_reto["telefono_rival"], "mensaje_proactivo": f"🎾 ¡Hola {res_reto['rival']}! {jugador.name} le envió un reto.", "orden_ia": "ORDEN: Confirma el envío del reto."}
            if res_reto["status"] in ["warning", "error"]: return {"status": "info", "perfil_socio": expediente, "orden_ia": f"ORDEN: Informe: {res_reto.get('reply')}"}
            return res_reto

        if tipo == "aceptar_reto":
            match_p = self.db.query(Match).filter(Match.player_2_id == jugador.id, Match.status == "proposed", Match.is_finished == False).first()
            if match_p:
                match_p.status = "scheduled"; self.db.commit()
                return {"status": "challenge_confirmed", "perfil_socio": expediente, "notificar_a": match_p.player_1.owner.phone_number, "mensaje_proactivo": f"✅ ¡Duelo confirmado! {jugador.name} aceptó.", "orden_ia": "ORDEN: Celebra la confirmación."}
            return {"status": "chat", "perfil_socio": expediente, "orden_ia": "ORDEN: No hay retos pendientes."}

        # --- RESPUESTA POR DEFECTO ---
        return {
            "status": "chat_asistente",
            "perfil_socio": expediente,
            "orden_ia": f"ORDEN: Saluda cordialmente a {jugador.name}. Ofrécele lanzar un reto o ver su progreso."
        }
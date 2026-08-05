from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from models import Player, Match, Club
from datetime import datetime, timedelta # ✅ Añadido timedelta para el cálculo de turnos
import unicodedata
import pytz # ✅ Indispensable para la expansión global

class BookingAgent:
    def __init__(self, db: Session):
        self.db = db

    def _normalizar(self, texto):
        if not texto: return ""
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto.lower().strip()

    def _buscar_jugador_inteligente(self, nombre_buscado, jugadores_club):
        target = self._normalizar(nombre_buscado)
        print(f"\033[1;94m🔍 [BOOKING/DETECTIVE] -> Rastreando a: '{nombre_buscado}'\033[0m")
        for p in jugadores_club:
            if self._normalizar(p.name) == target: return p
        for p in jugadores_club:
            nombre_real = self._normalizar(p.name)
            if target in nombre_real or nombre_real in target: return p
        return None

    # --- 🛡️ LOGICA PARA EL CHAT ---
    def agendar_reto(self, retador_nombre, rival_nombre, fecha_iso, club_id):
        jugadores = self.db.query(Player).filter_by(club_id=club_id).all()
        p1 = self._buscar_jugador_inteligente(retador_nombre, jugadores)
        p2 = self._buscar_jugador_inteligente(rival_nombre, jugadores)
        if not p1 or not p2:
            return {"status": "error", "reply": "Identidad no localizada en la Arena."}
        return self.lanzar_desafio_tactico(p1.id, p2.id, fecha_iso, club_id)

    # --- 🚀 METODO: TAP-TO-DUEL DE PADEL (DRAFT ABIERTO) ---
    def lanzar_desafio_tactico(self, retador_id, rival_id, fecha_iso, club_id, court_number=None):
        """
        Misión: Registro de duelo directo en Padel con sillas vacías para la comunidad.
        """
        # 1. Obtener Club y su Zona Horaria
        club = self.db.query(Club).filter_by(id=club_id).first()
        tz_name = club.settings.get("timezone", "America/Bogota") if club.settings else "America/Bogota"
        tz = pytz.timezone(tz_name)
        ahora_local = datetime.now(tz)

        # 2. Verificar Identidades
        p1 = self.db.query(Player).filter_by(id=retador_id).first()
        p2 = self.db.query(Player).filter_by(id=rival_id).first()

        if not p1 or not p2:
            return {"status": "error", "reply": "Sistemas de identidad desincronizados."}
        if p1.id == p2.id:
            return {"status": "error", "reply": "Un guerrero no puede desafiarse a sí mismo."}

        # 3. Coordenada Temporal
        fecha_obj = None
        try:
            if fecha_iso:
                if "Z" in fecha_iso: fecha_iso = fecha_iso.replace("Z", "")
                fecha_naive = datetime.fromisoformat(fecha_iso)
                fecha_obj = tz.localize(fecha_naive)
            else:
                fecha_obj = ahora_local
        except:
            return {"status": "error", "reply": "Coordenada temporal inválida."}

        # 4. Regla de Oro: Exclusividad de Combate
        guerreros_ocupados = self.db.query(Match).filter(
            Match.club_id == club_id,
            Match.is_finished == False,
            or_(
                Match.player_1_id == p1.id, 
                Match.player_2_id == p1.id,
                Match.player_3_id == p1.id,
                Match.player_4_id == p1.id,
                Match.player_1_id == p2.id,
                Match.player_2_id == p2.id,
                Match.player_3_id == p2.id,
                Match.player_4_id == p2.id
            )
        ).first()

        if guerreros_ocupados:
            envolucrado = p1.name if (
                guerreros_ocupados.player_1_id == p1.id or 
                guerreros_ocupados.player_2_id == p1.id or
                guerreros_ocupados.player_3_id == p1.id or
                guerreros_ocupados.player_4_id == p1.id
            ) else p2.name
            return {
                "status": "warning", 
                "reply": f"⚠️ Bloqueo de Arena: {envolucrado} ya tiene un duelo activo pendiente."
            }

        # 5. Crear el registro del duelo en la BD
        # ✅ CORRECCIÓN RED SOCIAL: player_2 y player_4 quedan vacíos (None)
        nuevo_match = Match(
            player_1_id=p1.id, 
            player_2_id=None, 
            player_3_id=p2.id,
            player_4_id=None,
            club_id=club_id,
            score="VS", 
            is_finished=False, 
            scheduled_time=fecha_obj
        )
        
        try:
            self.db.add(nuevo_match)
            self.db.commit()
            self.db.refresh(nuevo_match)
            print(f"\033[1;32m⚔️ [TOH ARENA] Duelo registrado: {p1.name} vs {p2.name}\033[0m")
            
            return {
                "status": "challenge_proposed", 
                "match_id": nuevo_match.id,
                "retador": p1.name,
                "rival": p2.name,
                "reply": f"¡Guante lanzado! 🚀 Desafío registrado contra {p2.name}."
            }
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error DB Booking: {e}")
            return {"status": "error", "reply": "Fallo en la persistencia del duelo."}

    # ============================================================
    # 📊 GENERADOR DE GRID (MULTICANCHA)
    # ============================================================
    def obtener_grid_disponibilidad(self, club_id, fecha_str):
        club = self.db.query(Club).filter_by(id=club_id).first()
        if not club: return {"status": "error", "reply": "Club no encontrado."}

        settings = club.settings or {}
        booking_config = settings.get("booking", {})
        
        courts_count = booking_config.get("courts_count", 6)
        open_time = booking_config.get("open_time", 6)
        close_time = booking_config.get("close_time", 22)
        slot_minutes = booking_config.get("slot_minutes", 90) # Padel suele ser de 90 min
        
        tz_name = settings.get("timezone", "America/Bogota")
        tz = pytz.timezone(tz_name)

        try:
            fecha_base = datetime.strptime(fecha_str, "%Y-%m-%d")
        except:
            fecha_base = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

        inicio_dia = tz.localize(fecha_base.replace(hour=0, minute=0, second=0))
        fin_dia = tz.localize(fecha_base.replace(hour=23, minute=59, second=59))

        partidos_del_dia = self.db.query(Match).filter(
            Match.club_id == club_id,
            Match.scheduled_time >= inicio_dia,
            Match.scheduled_time <= fin_dia,
            Match.is_finished == False
        ).all()

        grid = []
        hora_actual = fecha_base.replace(hour=open_time, minute=0, second=0)
        hora_cierre = fecha_base.replace(hour=close_time, minute=0, second=0)

        while hora_actual < hora_cierre:
            hora_str = hora_actual.strftime("%H:%M")
            hora_iso = tz.localize(hora_actual).isoformat()
            
            fila = {
                "hora": hora_str,
                "hora_iso": hora_iso,
                "canchas":[]
            }

            for cancha_idx in range(1, courts_count + 1):
                # Filtro de partidos para la cancha
                match_en_cancha = next((m for m in partidos_del_dia if m.player_1_id and m.scheduled_time.hour == hora_actual.hour and m.scheduled_time.minute == hora_actual.minute), None)
                
                if match_en_cancha:
                    p1_name = match_en_cancha.player_1.name.split(' ')[0] if match_en_cancha.player_1 else "N/A"
                    p3_name = match_en_cancha.p3.name.split(' ')[0] if match_en_cancha.p3 else "N/A"
                    
                    fila["canchas"].append({
                        "numero": cancha_idx,
                        "estado": "ocupada",
                        "label": f"{p1_name} vs {p3_name}"
                    })
                else:
                    fila["canchas"].append({
                        "numero": cancha_idx,
                        "estado": "libre",
                        "label": "LIBRE"
                    })

            grid.append(fila)
            hora_actual += timedelta(minutes=slot_minutes)

        return {
            "status": "success",
            "fecha": fecha_base.strftime("%Y-%m-%d"),
            "canchas_totales": courts_count,
            "grid": grid
        }
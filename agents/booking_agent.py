from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from models import Player, Match, WhatsAppUser
from datetime import datetime
import unicodedata

class BookingAgent:
    def __init__(self, db: Session):
        self.db = db

    def _normalizar(self, texto):
        if not texto: return ""
        # Quita tildes, espacios extra y lo pasa a minúsculas
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto.lower().strip()

    def _buscar_jugador_inteligente(self, nombre_buscado, jugadores_club):
        """
        Lógica de 'Gafas Inteligentes': 
        Busca coincidencias parciales si no encuentra una exacta.
        """
        target = self._normalizar(nombre_buscado)
        
        # 🎨 LOG DE BÚSQUEDA - Azul para el pensamiento
        print(f"\033[1;94m🔍 [PENSAMIENTO/BOOKING] -> Buscando a: '{nombre_buscado}'\033[0m")

        # 1. Intentar coincidencia exacta primero
        for p in jugadores_club:
            if self._normalizar(p.name) == target:
                print(f"\033[1;92m✅ [ÉXITO] -> Coincidencia exacta encontrada: {p.name}\033[0m")
                return p
        
        # 2. Intentar coincidencia parcial (Si 'Daniel' está dentro de 'Daniel CEO')
        for p in jugadores_club:
            nombre_real = self._normalizar(p.name)
            if target in nombre_real or nombre_real in target:
                print(f"\033[1;92m✅ [ÉXITO] -> Coincidencia parcial detectada: '{nombre_buscado}' parece ser '{p.name}'\033[0m")
                return p
        
        print(f"\033[1;91m❌ [ERROR] -> No se encontró a nadie que se parezca a '{nombre_buscado}'\033[0m")
        return None

    def agendar_reto(self, retador_nombre, rival_nombre, fecha_iso, club_id):
        """
        Inicia la negociación de un reto con búsqueda inteligente de guerreros.
        """
        # 1. [OBSERVAR] - Traer a todos los jugadores del club para comparar
        jugadores = self.db.query(Player).filter_by(club_id=club_id).all()
        
        # 2. Buscar al Retador y al Rival con nuestras nuevas gafas
        p1 = self._buscar_jugador_inteligente(retador_nombre, jugadores)
        p2 = self._buscar_jugador_inteligente(rival_nombre, jugadores)

        if not p1 or not p2:
            nombre_fallido = rival_nombre if p1 else retador_nombre
            return {
                "status": "error", 
                "reply": f"❌ Lo siento, no encuentro a ningún jugador llamado '{nombre_fallido}' en el ranking. ¿Te aseguraste de escribir bien su nombre?"
            }

        # 3. [INTERPRETAR] - Validar Fecha
        fecha_obj = None
        if fecha_iso:
            try: 
                # Intentamos limpiar la ISO si viene con milisegundos o cosas raras de la IA
                if "Z" in fecha_iso: fecha_iso = fecha_iso.replace("Z", "")
                fecha_obj = datetime.fromisoformat(fecha_iso)
            except Exception as e:
                print(f"⚠️ Error fecha: {e}")
        
        if not fecha_obj:
            return {"status": "error", "reply": "📅 Necesito que me digas el día y la hora exacta para reservar la cancha."}

        # 4. [RAZONAR] - Validación de Canchas (Capacidad: 2)
        partidos_misma_hora = self.db.query(Match).filter(
            Match.scheduled_time == fecha_obj,
            Match.is_finished == False
        ).count()

        if partidos_misma_hora >= 2:
            return {
                "status": "warning", 
                "reply": f"🚫 Las 2 canchas están ocupadas el {fecha_obj.strftime('%d/%m a las %I:%M %p')}. ¿Te sirve otra hora?"
            }

        # 5. [VERIFICAR] - ¿Ya existe este duelo pendiente?
        duelo_previo = self.db.query(Match).filter(
            or_(
                (Match.player_1_id == p1.id) & (Match.player_2_id == p2.id),
                (Match.player_1_id == p2.id) & (Match.player_2_id == p1.id)
            ),
            Match.is_finished == False
        ).first()

        if duelo_previo:
            return {"status": "warning", "reply": f"⚠️ Ya existe un duelo pendiente entre ustedes. ¡Jueguen ese primero!"}

        # 6. [EJECUTAR] - Crear el partido en estado "PROPOSED"
        nuevo_match = Match(
            player_1_id=p1.id, 
            player_2_id=p2.id, 
            score="VS", 
            status="proposed", 
            is_finished=False, 
            scheduled_time=fecha_obj,
            stake=10.0 
        )
        
        try:
            self.db.add(nuevo_match)
            self.db.commit()
            self.db.refresh(nuevo_match)
            print(f"\033[1;32m🎾 [BOOKING] Reto propuesto ID {nuevo_match.id}: {p1.name} vs {p2.name}\033[0m")
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error DB: {e}")
            return {"status": "error", "reply": "Tuve un problema al guardar el reto en la base de datos."}

        # Retornamos datos para el Handshake Proactivo
        return {
            "status": "challenge_proposed", 
            "match_id": nuevo_match.id,
            "retador": p1.name,
            "rival": p2.name,
            "telefono_rival": p2.owner.phone_number if p2.owner else None,
            "fecha_humana": fecha_obj.strftime("%d/%m %I:%M %p"),
            "reply": f"¡Reto enviado! 🚀 He contactado a {p2.name} para confirmar el duelo del {fecha_obj.strftime('%d/%m %I:%M %p')}. Te avisaré cuando acepte."
        }
from sqlalchemy.orm import Session
from models import Player, Match, Tournament, Club
import unicodedata

class TournamentAgent:
    def __init__(self, db: Session):
        self.db = db

    def _normalizar(self, texto):
        if not texto: return ""
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

    def importar_resultado_pasado(self, p1_name, p2_name, marcador, parciales, categoria, torneo_nombre, club_id):
        """
        Función maestra para subir los partidos de ayer y que afecten el ranking real.
        """
        # 1. Asegurar que el torneo exista en la DB
        torneo = self.db.query(Tournament).filter_by(name=torneo_nombre, club_id=club_id).first()
        if not torneo:
            torneo = Tournament(name=torneo_nombre, club_id=club_id, category=categoria, status="finished")
            self.db.add(torneo)
            self.db.commit()
            self.db.refresh(torneo)

        # 2. Buscar a los jugadores
        jugadores = self.db.query(Player).filter_by(club_id=club_id).all()
        p1 = next((p for p in jugadores if self._normalizar(p.name) == self._normalizar(p1_name)), None)
        p2 = next((p for p in jugadores if self._normalizar(p.name) == self._normalizar(p2_name)), None)

        if not p1 or not p2:
            return {"status": "error", "mensaje": f"No encontré a {p1_name} o {p2_name}"}

        # 3. Determinar ganador por marcador (ej: "3-0")
        sets = marcador.split('-')
        win_id = p1.id if int(sets[0]) > int(sets[1]) else p2.id

        # 4. Crear el registro del partido
        nuevo_match = Match(
            player_1_id=p1.id,
            player_2_id=p2.id,
            winner_id=win_id,
            score=marcador,
            parciales=parciales,
            match_type="tournament",
            tournament_id=torneo.id,
            is_finished=True,
            status="finished"
        )

        # 5. ACTUALIZAR RANKING (Economía y victorias)
        ganador = p1 if win_id == p1.id else p2
        perdedor = p2 if win_id == p1.id else p1
        
        ganador.wins += 1
        perdedor.losses += 1
        ganador.wallet_balance += 100 # Bono por victoria en torneo oficial
        
        self.db.add(nuevo_match)
        self.db.commit()
        return {"status": "success", "mensaje": f"Partido {p1_name} vs {p2_name} integrado al ranking."}
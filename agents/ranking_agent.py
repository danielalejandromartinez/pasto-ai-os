from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from models import Player, PointTransaction, Category, Season
from datetime import datetime

class RankingAgent:
    """
    EL ESTRATEGA DE LA ARENA:
    Analiza posiciones, calcula brechas de puntos y proyecta victorias.
    """
    def __init__(self, db: Session):
        self.db = db

    def analizar_competencia(self, jugador_id: int, rival_nombre_buscado: str = None):
        """
        Analiza la posición del jugador respecto a su categoría y rivales.
        """
        # 1. Obtener al jugador y su categoría principal
        jugador = self.db.query(Player).filter_by(id=jugador_id).first()
        if not jugador or not jugador.categories:
            return {"error": "Jugador sin categoría asignada"}

        categoria = jugador.categories[0] # Tomamos la primera liga activa
        
        # 2. Traer el Ranking real de esa categoría (Ordenado por puntos de temporada)
        # Nota: Usamos la lógica de puntos de temporada para la estrella
        ranking_raw = self.db.query(Player).join(Player.categories).filter(Category.id == categoria.id).all()
        
        # Calculamos puntos de temporada para todos en la liga
        tabla = []
        for p in ranking_raw:
            pts = sum(t.points_earned for t in p.point_history) # Simplificado para el demo
            tabla.append({"id": p.id, "nombre": p.name, "puntos": pts})
        
        # Ordenar ranking
        tabla.sort(key=lambda x: x["puntos"], reverse=True)

        # 3. Localizar mi puesto y mis vecinos
        mi_posicion = next((i for i, x in enumerate(tabla) if x["id"] == jugador.id), 0) + 1
        mi_puntaje = next((x["puntos"] for x in tabla if x["id"] == jugador.id), 0)
        
        lider = tabla[0]
        perseguidor = tabla[mi_posicion] if mi_posicion < len(tabla) else None
        puesto_arriba = tabla[mi_posicion - 2] if mi_posicion > 1 else None

        # 4. Cálculo de Brechas (Gap Analysis)
        gap_al_lider = lider["puntos"] - mi_puntaje
        victorias_necesarias = int(gap_al_lider / 10) + (1 if gap_al_lider % 10 > 0 else 0)

        # 5. Generar reporte para la Voz
        return {
            "mi_puesto": mi_posicion,
            "mi_puntaje": mi_puntaje,
            "categoria_nombre": categoria.name,
            "lider_actual": lider["nombre"],
            "puntos_lider": lider["puntos"],
            "gap_al_lider": gap_al_lider,
            "victorias_para_cima": victorias_necesarias,
            "quien_me_sigue": perseguidor["nombre"] if perseguidor else "Nadie por ahora",
            "puesto_arriba": puesto_arriba["nombre"] if puesto_arriba else "Usted es el líder"
        }
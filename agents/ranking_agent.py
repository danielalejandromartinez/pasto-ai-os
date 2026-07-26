from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from models import Player, PointTransaction, Category
from datetime import datetime

class RankingAgent:
    """
    EL ESTRATEGA DE LA ARENA v2.0:
    Analiza posiciones, calcula brechas de puntos y proyecta victorias.
    Cumple con la Constitución de 8 Pasos Pasto.AI.
    """
    def __init__(self, db: Session):
        self.db = db

    def analizar_competencia(self, jugador_id: int, rival_nombre_buscado: str = None):
        """
        Analiza la posición del jugador respecto a su categoría y rivales.
        Misión: Proveer datos para el Expediente Táctico (Pilar 12).
        """
        # [PASO 1: OBSERVAR] - Traer al guerrero de la base de datos
        jugador = self.db.query(Player).filter_by(id=jugador_id).first()
        
        # [PASO 6: VERIFICAR] - Validar que tenga ligas asignadas con el nuevo nombre
        if not jugador or not jugador.player_categories_list:
            print(f"\033[1;31m⚠️ [RANKING/ALERTA] -> Jugador {jugador_id} sin ligas activas.\033[0m")
            return {"error": "Jugador sin categoría asignada"}

        # ✅ SINCRONIZACIÓN: Usamos player_categories_list para evitar el Error 500
        categoria = jugador.player_categories_list[0] 
        
        # [PASO 3: RAZONAR] - Construir la tabla de posiciones en tiempo real
        # Unimos los puntos históricos con la racha actual
        ranking_raw = self.db.query(Player).join(Player.player_categories_list).filter(Category.id == categoria.id).all()
        
        tabla = []
        for p in ranking_raw:
            # Calculamos puntos totales del legado para el ranking de demo
            pts = sum(t.points_earned for t in p.point_history)
            tabla.append({"id": p.id, "nombre": p.name, "puntos": pts})
        
        # Ordenar ranking: El que tiene más puntos de gloria va arriba
        tabla.sort(key=lambda x: x["puntos"], reverse=True)

        # [PASO 4: PLANIFICAR] - Localizar mi puesto y mis vecinos de celda
        mi_posicion = next((i for i, x in enumerate(tabla) if x["id"] == jugador.id), 0) + 1
        mi_puntaje = next((x["puntos"] for x in tabla if x["id"] == jugador.id), 0)
        
        lider = tabla[0]
        perseguidor = tabla[mi_posicion] if mi_posicion < len(tabla) else None
        puesto_arriba = tabla[mi_posicion - 2] if mi_posicion > 1 else None

        # [PASO 8: AJUSTAR] - Cálculo de brechas estratégicas (Dopamina de Reto)
        gap_al_lider = lider["puntos"] - mi_puntaje
        # Calculamos cuántas victorias de 10 puntos faltan para ser el #1
        victorias_necesarias = int(gap_al_lider / 10) + (1 if gap_al_lider % 10 > 0 else 0)

        print(f"\033[1;32m📊 [RANKING/ÉXITO] -> Análisis completado para {jugador.name}. Puesto: #{mi_posicion}\033[0m")

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
    
    
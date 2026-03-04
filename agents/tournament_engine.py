import math
import random

class TournamentEngine:
    """
    EL MOTOR LÍQUIDO DE PASTO.AI V1.0
    Misión: Generar cuadros de torneo flexibles (Grupos + Playoffs) 
    sin importar el deporte de raqueta.
    """

    def __init__(self):
        print("\033[1;32m⚙️ [MOTOR/TORNEO] -> Sistema de Algoritmos Inicializado.\033[0m")

    def generar_grupos(self, lista_jugadores, num_grupos):
        """
        Divide a los jugadores en grupos de forma equilibrada.
        """
        random.shuffle(lista_jugadores) # Sorteo inicial
        grupos = {f"Grupo {chr(65+i)}": [] for i in range(num_grupos)}
        
        for i, jugador in enumerate(lista_jugadores):
            nombre_grupo = f"Grupo {chr(65 + (i % num_grupos))}"
            grupos[nombre_grupo].append(jugador)
            
        print(f"📊 [MOTOR] -> {len(lista_jugadores)} jugadores repartidos en {num_grupos} grupos.")
        return grupos

    def generar_calendario_round_robin(self, grupo_jugadores):
        """
        Genera todos los partidos posibles (Todos contra todos) dentro de un grupo.
        """
        partidos = []
        n = len(grupo_jugadores)
        for i in range(n):
            for j in range(i + 1, n):
                partidos.append({
                    "p1": grupo_jugadores[i],
                    "p2": grupo_jugadores[j],
                    "estado": "pendiente",
                    "resultado": None
                })
        return partidos

    def calcular_posiciones(self, jugadores, resultados_partidos):
        """
        LA LÓGICA DEL JUEZ (Tu lógica PG y DS):
        Calcula quién va primero basado en victorias y diferencia de sets.
        """
        tabla = {p: {"nombre": p, "PG": 0, "PP": 0, "SF": 0, "SC": 0, "DS": 0} for p in jugadores}
        
        for p in resultados_partidos:
            if p["estado"] == "finalizado":
                res = p["resultado"].split("-") # ej: "3-0"
                s1, s2 = int(res[0]), int(res[1])
                
                # Sumar Sets
                tabla[p["p1"]]["SF"] += s1
                tabla[p["p1"]]["SC"] += s2
                tabla[p["p2"]]["SF"] += s2
                tabla[p["p2"]]["SC"] += s1
                
                # Victoria / Derrota
                if s1 > s2:
                    tabla[p["p1"]]["PG"] += 1
                    tabla[p["p2"]]["PP"] += 1
                else:
                    tabla[p["p2"]]["PG"] += 1
                    tabla[p["p1"]]["PP"] += 1

        # Calcular Diferencia de Sets (DS)
        for p in tabla:
            tabla[p]["DS"] = tabla[p]["SF"] - tabla[p]["SC"]

        # Ordenar por PG (Puntos) y luego por DS (Diferencia de Sets)
        ranking = list(tabla.values())
        ranking.sort(key=lambda x: (x["PG"], x["DS"]), reverse=True)
        
        return ranking

    def generar_llaves_playoff(self, clasificados_por_grupo):
        """
        Toma a los mejores de cada grupo y arma la llave de eliminación.
        """
        print(f"🌳 [MOTOR] -> Generando árbol de PlayOffs con {len(clasificados_por_grupo)} guerreros.")
        llaves = []
        # Lógica simple: 1ro vs Último, 2do vs Penúltimo
        n = len(clasificados_por_grupo)
        for i in range(n // 2):
            llaves.append({
                "ronda": "Eliminatoria",
                "p1": clasificados_por_grupo[i]["nombre"],
                "p2": clasificados_por_grupo[n - 1 - i]["nombre"],
                "estado": "esperando"
            })
        return llaves

# ============================================================
# 🧪 LABORATORIO DE PRUEBAS (SOLO PARA TESTEAR)
# ============================================================
if __name__ == "__main__":
    engine = TournamentEngine()
    
    # 1. Imaginemos 11 jugadores como dijiste
    guerreros = [f"Jugador {i+1}" for i in range(11)]
    
    # 2. El Jefe quiere 2 grupos (uno de 5 y otro de 6)
    mis_grupos = engine.generar_grupos(guerreros, 2)
    
    for nombre, lista in mis_grupos.items():
        print(f"\n🔹 {nombre}: {lista}")
        # Generar partidos de ese grupo
        partidos = engine.generar_calendario_round_robin(lista)
        print(f"   📅 Partidos programados: {len(partidos)}")
        
        # Simulamos un resultado para el primer partido
        partidos[0]["estado"] = "finalizado"
        partidos[0]["resultado"] = "3-0"
        
        # Calcular tabla
        tabla = engine.calcular_posiciones(lista, partidos)
        print(f"   🏆 Líder actual: {tabla[0]['nombre']} (PG: {tabla[0]['PG']} | DS: {tabla[0]['DS']})")
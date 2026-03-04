from database import SessionLocal
from models import Player, WhatsAppUser, Tournament, Match, Club
from sqlalchemy import or_, func
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime
import unicodedata

# --- FUNCIÓN DE LIMPIEZA (QUITAR TILDES) ---
def normalizar(texto):
    if not texto: return ""
    # Quita tildes y pasa a minúsculas (Ej: "Martínez" -> "martinez")
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def ejecutar(decision: dict):
    accion = decision.get("accion")
    datos = decision.get("datos", {})
    db = SessionLocal()
    resultado = {"status": "error", "mensaje": "Acción no reconocida"}

    try:
        # --- MANO 1: CREAR JUGADOR ---
        if accion == "crear_perfil_db":
            nombre = datos.get("nombre")
            categoria = datos.get("categoria")
            telefono_padrino = datos.get("padrino_telefono")
            club_id = datos.get("club_id")
            
            # Búsqueda normalizada
            jugadores = db.query(Player).filter_by(club_id=club_id).all()
            existe = next((p for p in jugadores if normalizar(p.name) == normalizar(nombre)), None)
            
            if existe:
                # --- NUEVO: RETORNAR ID DEL JUGADOR CREADO ---
                # Esto es vital para que el Admin sepa a quién asignarle la foto
                resultado = {
                    "status": "warning", 
                    "mensaje": f"El jugador {nombre} ya existe.",
                    "jugador_id": existe.id # <--- ID PARA MEMORIA
                }
            else:
                padrino = db.query(WhatsAppUser).filter_by(phone_number=telefono_padrino).first()
                if not padrino:
                    padrino = WhatsAppUser(phone_number=telefono_padrino); db.add(padrino); db.commit()
                nuevo = Player(name=nombre, category=categoria, club_id=club_id, owner_id=padrino.id)
                db.add(nuevo); db.commit()
                
                resultado = {
                    "status": "success", 
                    "mensaje": f"Jugador {nombre} creado.",
                    "jugador_id": nuevo.id # <--- ID PARA MEMORIA
                }

        # --- MANO 2: AGENDAR RETO (BLINDADO) ---
        elif accion == "agendar_reto_db":
            retador_nombre = datos.get("retador")
            rival_nombre = datos.get("rival")
            club_id = datos.get("club_id")

            # Búsqueda inteligente
            jugadores = db.query(Player).filter_by(club_id=club_id).all()
            p1 = next((p for p in jugadores if normalizar(p.name) == normalizar(retador_nombre)), None)
            p2 = next((p for p in jugadores if normalizar(p.name) == normalizar(rival_nombre)), None)
            
            fecha_str = datos.get("fecha_iso")
            fecha_obj = None
            if fecha_str:
                try: fecha_obj = datetime.fromisoformat(fecha_str)
                except: pass

            if p1 and p2:
                reto_existente = db.query(Match).filter(
                    or_(
                        (Match.player_1_id == p1.id) & (Match.player_2_id == p2.id),
                        (Match.player_1_id == p2.id) & (Match.player_2_id == p1.id)
                    ),
                    Match.is_finished == False
                ).first()

                if reto_existente:
                    resultado = {"status": "warning", "mensaje": f"⚠️ Ya existe un reto pendiente entre {p1.name} y {p2.name}."}
                else:
                    match = Match(
                        player_1_id=p1.id, 
                        player_2_id=p2.id, 
                        score="VS", 
                        status="scheduled", 
                        is_finished=False,
                        scheduled_time=fecha_obj
                    )
                    db.add(match)
                    db.commit()
                    msg_fecha = fecha_obj.strftime("%d/%m %I:%M %p") if fecha_obj else "Fecha por definir"
                    resultado = {"status": "success", "mensaje": f"Reto agendado: {p1.name} vs {p2.name} ({msg_fecha})"}
            else:
                faltante = ""
                if not p1: faltante += f"No encuentro a '{retador_nombre}'. "
                if not p2: faltante += f"No encuentro a '{rival_nombre}'."
                resultado = {"status": "error", "mensaje": f"❌ {faltante} Revisa la ortografía."}

        # --- MANO 3: CREAR TORNEO ---
        elif accion == "crear_torneo_db":
            club_id = datos.get("club_id")
            anteriores = db.query(Tournament).filter_by(club_id=club_id, status="inscription").all()
            for t in anteriores: t.status = "finished"
            nuevo = Tournament(name=datos.get("nombre"), club_id=club_id, status="inscription", smart_data={"inscritos": []})
            db.add(nuevo); db.commit()
            resultado = {"status": "success", "mensaje": f"Torneo creado."}

        # --- MANO 4: INSCRIBIR EN TORNEO ---
        elif accion == "inscribir_torneo_db":
            nombre = datos.get("nombre_jugador")
            club_id = datos.get("club_id")
            padrino_tel = datos.get("padrino_telefono")

            torneo = db.query(Tournament).filter_by(club_id=club_id, status="inscription").first()
            if not torneo:
                resultado = {"status": "error", "mensaje": "No hay torneo abierto."}
            else:
                jugadores = db.query(Player).filter_by(club_id=club_id).all()
                jugador = next((p for p in jugadores if normalizar(p.name) == normalizar(nombre)), None)
                
                if not jugador:
                    padrino = db.query(WhatsAppUser).filter_by(phone_number=padrino_tel).first()
                    if not padrino:
                        padrino = WhatsAppUser(phone_number=padrino_tel); db.add(padrino); db.commit()
                    jugador = Player(name=nombre, category="General", club_id=club_id, owner_id=padrino.id)
                    db.add(jugador); db.commit()

                db.refresh(torneo)
                smart_data = dict(torneo.smart_data) if torneo.smart_data else {"inscritos": []}
                lista = list(smart_data.get("inscritos", []))
                
                if jugador.id not in lista:
                    lista.append(jugador.id)
                    smart_data["inscritos"] = lista
                    torneo.smart_data = smart_data
                    flag_modified(torneo, "smart_data")
                    db.add(torneo); db.commit()
                    resultado = {"status": "success", "mensaje": f"{nombre} inscrito en {torneo.name}."}
                else:
                    resultado = {"status": "warning", "mensaje": f"{nombre} ya estaba inscrito."}

        # --- MANO 5: GENERAR CUADROS ---
        elif accion == "generar_cuadros_db":
            club_id = datos.get("club_id")
            torneo = db.query(Tournament).filter_by(club_id=club_id, status="inscription").first()
            if torneo:
                ids = torneo.smart_data.get("inscritos", [])
                if len(ids) >= 2:
                    jugadores = db.query(Player).filter(Player.id.in_(ids)).order_by(Player.elo.desc()).all()
                    n = len(jugadores)
                    for i in range(n // 2):
                        p1 = jugadores[i]
                        p2 = jugadores[n - 1 - i]
                        match = Match(player_1_id=p1.id, player_2_id=p2.id, tournament_id=torneo.id, score="VS", is_finished=False)
                        db.add(match)
                    torneo.status = "playing"
                    db.commit()
                    resultado = {"status": "success", "mensaje": "Cuadros generados."}
                else:
                    resultado = {"status": "error", "mensaje": "Faltan jugadores."}
            else:
                resultado = {"status": "error", "mensaje": "No hay torneo en inscripción."}

        # --- MANO 6: REGISTRAR RESULTADOS (THE ARENA) ---
        elif accion == "registrar_resultado_db":
            reportante_nombre = datos.get("reportante")
            marcador = datos.get("marcador")
            club_id = datos.get("club_id")
            
            jugadores = db.query(Player).filter_by(club_id=club_id).all()
            jugador = next((p for p in jugadores if normalizar(p.name) == normalizar(reportante_nombre)), None)
            
            if not jugador:
                resultado = {"status": "error", "mensaje": "No encuentro tu perfil."}
            else:
                match = db.query(Match).filter(
                    or_(Match.player_1_id == jugador.id, Match.player_2_id == jugador.id),
                    Match.is_finished == False
                ).first()
                
                if not match:
                    resultado = {"status": "warning", "mensaje": "No tienes ningún partido pendiente por jugar."}
                else:
                    ganador = jugador
                    perdedor = match.player_2 if match.player_1_id == jugador.id else match.player_1
                    
                    apuesta = match.stake 
                    comision = apuesta * 0.10 
                    premio_neto = apuesta - comision 
                    
                    ganador.wallet_balance += premio_neto
                    perdedor.wallet_balance -= apuesta
                    ganador.wins += 1
                    perdedor.losses += 1
                    
                    club = db.query(Club).filter_by(id=club_id).first()
                    club.jackpot_balance += comision
                    
                    match.is_finished = True
                    match.winner_id = ganador.id
                    match.score = marcador
                    match.status = "finished"
                    
                    db.commit()
                    
                    resultado = {"status": "success", "mensaje": f"✅ ¡Resultado registrado!\n\n💰 {ganador.name}: +{premio_neto} SQC\n📉 {perdedor.name}: -{apuesta} SQC\n🏦 Pozo del Club: +{comision} SQC"}

        # --- MANO 7: CREAR CLUB SAAS ---
        elif accion == "crear_club_saas":
            nuevo = Club(name=datos.get("nombre"), admin_phone=datos.get("admin_phone"))
            db.add(nuevo); db.commit()
            resultado = {"status": "success", "mensaje": "Club creado."}

        # --- MANO 8: CONSULTAR RANKING ---
        elif accion == "consultar_ranking_db":
            club_id = datos.get("club_id")
            jugadores = db.query(Player).filter_by(club_id=club_id).order_by(Player.wallet_balance.desc()).limit(10).all()
            lista = "\n".join([f"{i+1}. {p.name} (💰 {p.wallet_balance})" for i, p in enumerate(jugadores)])
            resultado = {"status": "success", "mensaje": f"🏆 Ranking (The Arena):\n{lista}"}

        # --- MANO 9: RESPUESTAS SIMPLES ---
        elif accion == "generar_respuesta_ia":
            resultado = {"status": "chat", "mensaje": "Chat"}
        elif accion == "responder_texto":
             resultado = {"status": "info", "mensaje": decision.get("respuesta")}

    except Exception as e:
        print(f"❌ Error DB: {e}")
        resultado = {"status": "error", "mensaje": "Error técnico."}
    finally:
        db.close()
    
    return resultado
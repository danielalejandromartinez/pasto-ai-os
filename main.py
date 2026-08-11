import os
import uvicorn
import time
import unicodedata
import json
import base64 # ✅ Para encriptar fotos de forma persistente en la BD
import shutil # ✅ Para el manejo físico de selfies
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks, Form, File, UploadFile # ✅ Formato de datos web
from fastapi.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from dotenv import load_dotenv

# --- ÓRGANOS DEL AGENTE ---
from database import engine, Base, get_db, SessionLocal
from models import Club, Player, Match, WhatsAppUser, MessageHistory, PointTransaction, Category, WhiteList, Country, City
from whatsapp_service import enviar_whatsapp
from connection_manager import manager
import media_service

# --- MÓDULOS DEL CEREBRO ---
import user_classifier
import intent_resolver
import generar_respuesta_humana
from agents.orchestrator import Orchestrator 
from agents.membership_agent import MembershipAgent # ✅ Para Step 3
from agents.booking_agent import BookingAgent # ✅ Para Step 4

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "pasto_ai_token")

# --- IDENTIFICADORES VISUALES DEL LOOP (NASA STANDARDS) ---
C_OBS = "\033[1;94m" # 1. OBSERVAR (Azul)
C_INT = "\033[1;95m" # 2. INTERPRETAR (Magenta)
C_REA = "\033[1;96m" # 3. RAZONAR (Cian)
C_PLA = "\033[1;93m" # 4. PLANIFICAR (Amarillo)
C_EXE = "\033[1;92m" # 5. EJECUTAR (Verde)
C_VER = "\033[1;32m" # 6. VERIFICAR (Verde Oscuro)
C_LEA = "\033[1;90m" # 7. APRENDER (Gris)
C_ADJ = "\033[1;97m" # 8. AJUSTAR COMPORTAMIENTO (Blanco)
C_END = "\033[0m"

# --- UTILIDAD DE NORMALIZACIÓN ---
def _norm(t):
    if not t: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower().strip()

# ============================================================
# 🛡️ API: REGISTRO TÁCTICO PWA (ONBOARDING 2050 - STEP 3)
# ============================================================
@app.post("/api/player/register")
async def registrar_guerrero_web(
    telefono: str = Form(...), nombre: str = Form(...), club_id: int = Form(...),
    foto: UploadFile = File(...), db: Session = Depends(get_db)
):
    try:
        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️] -> Intento de Registro Web: {nombre}{C_END}")
        folder = "static/profiles"
        if not os.path.exists(folder): os.makedirs(folder)
        path_destino = f"{folder}/{telefono}.jpg"
        with open(path_destino, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
            
        agent = MembershipAgent(db)
        print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡] -> Sincronizando identidad táctica...{C_END}")
        agent.registrar_jugador(nombre, telefono, club_id)
        agent.actualizar_foto(telefono, path_destino, es_demo=True)
        
        await manager.broadcast("update", club_id)
        print(f"{C_VER}[LOOP: PASO 6 - VERIFICANDO ✅] -> Guerrero activado físicamente.{C_END}")
        return {"status": "success", "mensaje": "Tarjeta Activada."}
    except Exception as e:
        print(f"❌ Error Registro: {e}")
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 🛡️ API: SOLICITUD DE ADMISIÓN DESDE LA PWA CON USUARIO Y PIN (TOH SYSTEM)
# ============================================================
@app.post("/api/player/register/request")
async def solicitar_ingreso_toh(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        nombre = data.get("nombre")
        username = _norm(data.get("username")) 
        pin_code = data.get("pin")
        categoria_nombre = data.get("categoria")
        club_id = int(data.get("club_id"))

        usuario_existente = db.query(Player).filter(Player.username == username).first()
        if usuario_existente:
            return {"status": "error", "mensaje": "Este Nombre de Usuario ya está ocupado. Intenta con otro."}

        nuevo_jugador = Player(
            name=nombre, 
            username=username,
            pin_code=pin_code,
            club_id=club_id, 
            is_approved=False 
        )
        
        categoria_db = db.query(Category).filter(and_(Category.club_id == club_id, Category.name == categoria_nombre)).first()
        if categoria_db:
            nuevo_jugador.player_categories_list.append(categoria_db)
            
        db.add(nuevo_jugador)
        db.commit()
        db.refresh(nuevo_jugador) 

        await manager.broadcast("update", club_id)
        return {"status": "success", "mensaje": "Solicitud enviada de manera correcta.", "player_id": nuevo_jugador.id}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 🛡️ NUEVA API: VERIFICACIÓN DE INGRESO DESDE LA PWA (LOGIN TOH)
# ============================================================
@app.post("/api/player/login")
async def verificar_ingreso_toh(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        username = _norm(data.get("username"))
        pin_code = data.get("pin")

        jugador = db.query(Player).filter(Player.username == username).first()
        if not jugador:
            return {"status": "error", "mensaje": "Nombre de usuario no localizado en la Arena."}

        if jugador.pin_code != pin_code:
            return {"status": "error", "mensaje": "PIN de seguridad incorrecto."}

        if not jugador.is_approved:
            return {"status": "pending", "mensaje": "Tu perfil está pendiente de aprobación por la administración del club."}

        categoria_nombre = jugador.player_categories_list[0].name if jugador.player_categories_list else "General"

        return {
            "status": "success",
            "player_id": jugador.id,
            "nombre": jugador.name,
            "categoria": categoria_nombre,
            "mensaje": f"¡Bienvenido de vuelta, {jugador.name}! ⚔️"
        }
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 🛡️ NUEVA API: CARGA DE FOTO DE PERFIL ENCRIPTADA EN BASE64 (DURABILIDAD 100%)
# ============================================================
@app.post("/api/player/upload-photo")
async def subir_foto_perfil_toh(
    player_id: int = Form(...),
    foto: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️] -> Guardando foto persistente en DB para Jugador ID: {player_id}{C_END}")
        
        jugador = db.query(Player).filter(Player.id == player_id).first()
        if not jugador: return {"status": "error", "mensaje": "Jugador no localizado."}
        
        contenido_imagen = await foto.read()
        base64_encoded = base64.b64encode(contenido_imagen).decode('utf-8')
        
        jugador.avatar_url = f"data:image/jpeg;base64,{base64_encoded}"
        db.commit()
        
        print(f"{C_VER}[LOOP: PASO 6 - VERIFICANDO ✅] -> Foto guardada exitosamente en la base de datos de PostgreSQL.{C_END}")
        
        await manager.broadcast("update", jugador.club_id)
        return {"status": "success", "mensaje": "¡Foto de perfil activada!"}
    except Exception as e:
        print(f"❌ Error Carga Foto: {e}")
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# ⚔️ API: LANZAR DESAFÍO TÁCTICO (TAP-TO-DUEL)
# ============================================================
@app.post("/api/challenge/create")
async def lanzar_desafio_pwa(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        retador_id = data.get("challenger_id")
        rival_id = data.get("opponent_id")
        club_id = data.get("club_id", 1)

        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️] -> Petición de Duelo Táctico: ID {retador_id} vs ID {rival_id}{C_END}")
        
        if not retador_id or not rival_id:
            return {"status": "error", "mensaje": "Identidades incompletas para el duelo."}

        agent = BookingAgent(db)
        resultado = agent.lanzar_desafio_tactico(
            retador_id=int(retador_id), 
            rival_id=int(rival_id), 
            fecha_iso=None, 
            club_id=int(club_id)
        )

        if resultado["status"] == "challenge_proposed":
            print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡] -> Duelo registrado. Sincronizando Arena...{C_END}")
            await manager.broadcast("update", club_id)
            return {"status": "success", "mensaje": resultado["reply"]}
        else:
            return {"status": "error", "mensaje": resultado.get("reply", "Error en el desafío.")}

    except Exception as e:
        print(f"❌ Error API Duelo: {e}")
        return {"status": "error", "mensaje": "Fallo en la conexión táctica de la Arena."}

# ============================================================
# 🛡️ API: ACEPTAR DESAFÍO DIRECTO DESDE LA PWA (HANDSHAKE)
# ============================================================
@app.post("/api/challenge/accept/{match_id}")
async def aceptar_desafio_toh(match_id: int, db: Session = Depends(get_db)):
    try:
        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️] -> Confirmando desafío para Match ID: {match_id}{C_END}")
        
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match: return {"status": "error", "mensaje": "Duelo no localizado."}
        
        match.scheduled_time = datetime.now()
        match.is_confirmed = True
        db.commit()
        
        print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡] -> Desafío confirmado.{C_END}")
        await manager.broadcast("update", match.club_id)
        return {"status": "success", "mensaje": "¡Duelo confirmado! Prepárate para entrar a la Arena."}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 🤝 API: UNIRSE AL DRAFT ABIERTO (LA RED SOCIAL TOH)
# ============================================================
@app.post("/api/challenge/join/{match_id}")
async def unirse_desafio_toh(match_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        player_id = int(data.get("player_id"))
        team = data.get("team") 

        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️] -> Jugador {player_id} solicitando silla en Match {match_id} (Equipo {team}){C_END}")

        match = db.query(Match).filter(Match.id == match_id).first()
        if not match: return {"status": "error", "mensaje": "Duelo no localizado."}
        
        if player_id in [match.player_1_id, match.player_2_id, match.player_3_id, match.player_4_id]:
            return {"status": "error", "mensaje": "Ya tienes una silla reservada en esta batalla."}

        print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡] -> Asignando asiento en el Draft...{C_END}")
        
        if team == "A":
            if match.player_2_id is None: match.player_2_id = player_id
            else: return {"status": "error", "mensaje": "La pareja de este jugador ya está completa."}
        elif team == "B":
            if match.player_4_id is None: match.player_4_id = player_id
            else: return {"status": "error", "mensaje": "La pareja de este jugador ya está completa."}
        else:
            return {"status": "error", "mensaje": "Equipo no válido."}

        db.commit()
        
        print(f"{C_VER}[LOOP: PASO 6 - VERIFICANDO ✅] -> Silla asignada correctamente.{C_END}")
        await manager.broadcast("update", match.club_id)
        return {"status": "success", "mensaje": "¡Te has unido a la batalla con éxito!"}
    except Exception as e:
        print(f"❌ Error al unirse: {e}")
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 📅 API: GESTIÓN DE RESERVAS
# ============================================================
@app.get("/api/booking/grid/{club_id}")
async def obtener_grid(club_id: int, fecha: str = None, db: Session = Depends(get_db)):
    try:
        if not fecha: fecha = datetime.now().strftime("%Y-%m-%d")
        return BookingAgent(db).obtener_grid_disponibilidad(club_id, fecha)
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

@app.post("/api/booking/reserve")
async def reservar_cancha(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        new_res = Match(
            player_1_id=data.get("player_id"),
            club_id=data.get("club_id"),
            court_number=data.get("court_number"),
            scheduled_time=datetime.fromisoformat(data.get("scheduled_time")),
            status="scheduled",
            is_finished=False,
            match_type="friendly"
        )
        db.add(new_res); db.commit()
        await manager.broadcast("update", data.get("club_id"))
        return {"status": "success", "mensaje": "Reserva confirmada en la Arena."}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 🚪 EL PORTAL DE BIENVENIDA TOH (Powered by Pasto.AI)
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    paises = db.query(Country).all()
    return templates.TemplateResponse("index.html", {"request": request, "paises": paises})

# ============================================================
# 🗺️ APIS DE GEOGRAFÍA PARA SELECTORES DINÁMICOS
# ============================================================
@app.get("/api/geo/cities/{country_id}")
def obtener_ciudades_pwa(country_id: int, db: Session = Depends(get_db)):
    ciudades = db.query(City).filter(City.country_id == country_id).all()
    return [{"id": c.id, "name": c.name} for c in ciudades]

@app.get("/api/geo/clubs/{city_id}")
def obtener_clubes_pwa(city_id: int, db: Session = Depends(get_db)):
    clubes = db.query(Club).filter(Club.city_id == city_id).all()
    return [{"id": c.id, "name": c.name} for c in clubes]

# ============================================================
# ⚙️ VISTAS DE ADMINISTRACIÓN AUTOGESTIONABLE (DASHBOARD)
# ============================================================
@app.get("/club/{club_id}/admin", response_class=HTMLResponse)
async def ver_dashboard_admin(request: Request, club_id: int, db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club: return HTMLResponse(content="Club no encontrado", status_code=404)
    
    pendientes = db.query(Player).filter(and_(Player.club_id == club_id, Player.is_approved == False)).all()
    
    return templates.TemplateResponse("admin.html", {
        "request": request, "club": club, "pendientes": pendientes, "settings": club.settings or {}
    })

@app.post("/api/admin/approve/{player_id}")
async def aprobar_jugador(player_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        aprobado = data.get("aprobado")
        
        jugador = db.query(Player).filter(Player.id == player_id).first()
        if not jugador: return {"status": "error", "mensaje": "Jugador no localizado."}
        
        if aprobado:
            jugador.is_approved = True
            db.commit()
            await manager.broadcast("update", jugador.club_id)
            return {"status": "success", "mensaje": f"{jugador.name} ha sido admitido en la Arena con éxito."}
        else:
            db.delete(jugador)
            db.commit()
            return {"status": "success", "mensaje": "Solicitud de admisión rechazada."}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

@app.post("/api/admin/club/update/{club_id}")
async def actualizar_configuracion_club(club_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club: return {"status": "error", "mensaje": "Club no encontrado."}
        
        club.name = data.get("name")
        
        settings = dict(club.settings) if club.settings else {}
        settings["primary_color"] = data.get("primary_color")
        settings["logo_url"] = data.get("logo_url")
        club.settings = settings
        
        db.commit()
        await manager.broadcast("update", club_id)
        return {"status": "success", "mensaje": "Configuración guardada."}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 🏆 NUEVAS APIS: CIERRE DE CICLOS Y GAMIFICACIÓN (TOH ADMIN)
# ============================================================
@app.post("/api/admin/close-month/{club_id}")
async def cerrar_mes(club_id: int, db: Session = Depends(get_db)):
    """ Reparte medallas a los líderes de cada categoría y resetea los puntos mensuales a cero. """
    try:
        print(f"\n{C_PLA}[LOOP: PASO 4 - PLANIFICAR 📋] -> Iniciando Cierre de Mes (Club ID: {club_id}){C_END}")
        
        categorias = db.query(Category).filter(Category.club_id == club_id).all()
        campeones_nombres = []

        for categoria in categorias:
            # Buscamos al jugador con más puntos mensuales en esta categoría
            lider = db.query(Player).filter(
                and_(Player.club_id == club_id, Player.is_approved == True, Player.player_categories_list.any(id=categoria.id))
            ).order_by(desc(Player.monthly_points)).first()

            if lider and lider.monthly_points > 0:
                lider.medals += 1
                campeones_nombres.append(f"{lider.name} ({categoria.name})")

        # Resetear todos los puntos mensuales del club a 0
        jugadores = db.query(Player).filter(Player.club_id == club_id).all()
        for j in jugadores:
            j.monthly_points = 0.0

        db.commit()
        await manager.broadcast("update", club_id)
        
        resumen = ", ".join(campeones_nombres) if campeones_nombres else "Nadie sumó puntos este mes."
        return {"status": "success", "mensaje": f"Cierre de mes completado. Medallas entregadas a: {resumen}"}
    except Exception as e:
        print(f"❌ Error Cerrando Mes: {e}")
        return {"status": "error", "mensaje": str(e)}

@app.post("/api/admin/close-season/{club_id}")
async def cerrar_temporada(club_id: int, db: Session = Depends(get_db)):
    """ Reparte estrellas a los líderes de temporada y resetea puntos y medallas a cero. """
    try:
        print(f"\n{C_PLA}[LOOP: PASO 4 - PLANIFICAR 📋] -> Iniciando Cierre de Temporada (Club ID: {club_id}){C_END}")
        
        categorias = db.query(Category).filter(Category.club_id == club_id).all()
        campeones_nombres = []

        for categoria in categorias:
            lider = db.query(Player).filter(
                and_(Player.club_id == club_id, Player.is_approved == True, Player.player_categories_list.any(id=categoria.id))
            ).order_by(desc(Player.season_points)).first()

            if lider and lider.season_points > 0:
                lider.stars += 1
                campeones_nombres.append(f"{lider.name} ({categoria.name})")

        # Resetear puntos de temporada, puntos de mes y medallas a 0
        jugadores = db.query(Player).filter(Player.club_id == club_id).all()
        for j in jugadores:
            j.season_points = 0.0
            j.monthly_points = 0.0
            j.medals = 0

        db.commit()
        await manager.broadcast("update", club_id)
        
        resumen = ", ".join(campeones_nombres) if campeones_nombres else "Nadie sumó puntos esta temporada."
        return {"status": "success", "mensaje": f"¡Cierre de temporada completado! Estrellas eternas entregadas a: {resumen}"}
    except Exception as e:
        print(f"❌ Error Cerrando Temporada: {e}")
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 📡 API: FINALIZAR PARTIDO DE PADEL DESDE EL TABLERO (10/3 A 4 JUGADORES)
# ============================================================
@app.post("/api/match/finish")
async def finalizar_partido(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        winner_name = data.get("ganador")
        match_id = data.get("matchId")
        
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match: return {"status": "error", "mensaje": "Duelo no localizado."}
        
        p1, p2 = match.player_1, match.player_2
        p3, p4 = match.p3, match.p4
        winner_norm = _norm(winner_name)
        
        print(f"\n{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡] -> Repartiendo gloria y puntos en la Arena...{C_END}")
        
        nombre_p1_corto = _norm(p1.name.split(' ')[0]) if p1 else ""
        
        if nombre_p1_corto in winner_norm: 
            # 🏆 GANÓ EL EQUIPO A (P1 y P2)
            # Sumamos a todos los buckets: eternal, season y monthly
            p1.eternal_points += 10.0; p1.season_points += 10.0; p1.monthly_points += 10.0; p1.wins += 1
            if p2: p2.eternal_points += 10.0; p2.season_points += 10.0; p2.monthly_points += 10.0; p2.wins += 1
            
            p3.eternal_points += 3.0; p3.season_points += 3.0; p3.monthly_points += 3.0; p3.losses += 1
            if p4: p4.eternal_points += 3.0; p4.season_points += 3.0; p4.monthly_points += 3.0; p4.losses += 1
            
            match.winner_team = "A"
            match.winner_id = p1.id
        else: 
            # 🏆 GANÓ EL EQUIPO B (P3 y P4)
            p3.eternal_points += 10.0; p3.season_points += 10.0; p3.monthly_points += 10.0; p3.wins += 1
            if p4: p4.eternal_points += 10.0; p4.season_points += 10.0; p4.monthly_points += 10.0; p4.wins += 1
            
            p1.eternal_points += 3.0; p1.season_points += 3.0; p1.monthly_points += 3.0; p1.losses += 1
            if p2: p2.eternal_points += 3.0; p2.season_points += 3.0; p2.monthly_points += 3.0; p2.losses += 1
            
            match.winner_team = "B"
            match.winner_id = p3.id
            
        match.is_finished = True
        match.score = data.get("res")
        
        db.commit()
        await manager.broadcast("update", match.club_id)
        
        print(f"{C_VER}[LOOP: PASO 6 - VERIFICANDO ✅] -> Puntos asignados a los 4 jugadores correctamente.{C_END}")
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Error al finalizar partido: {e}")
        return {"status": "error", "mensaje": str(e)}

@app.get("/tablero")
async def ver_tablero(request: Request):
    return templates.TemplateResponse("tablero.html", {"request": request})

# ============================================================
# 📺 VISTA WEB: EL MURO DE LA FAMA (CONFIG-DRIVEN)
# ============================================================
@app.get("/club/{club_id}")
async def ver_club(request: Request, club_id: int, db: Session = Depends(get_db)):
    try:
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club: return HTMLResponse(content="Club no encontrado", status_code=404)
        
        settings = club.settings if club.settings else {}
        identidad_visual = {
            "activo": True, "nombre": club.name, "logo": settings.get("logo_url", "/static/logo_pasto.jpg"),
            "whatsapp": club.admin_phone, "mensaje": f"Hola, quiero información del club {club.name}.",
            "color": settings.get("primary_color", "#00f2ff"), "cta": "Inscribirme"
        }

        cats_db = db.query(Category).filter_by(club_id=club_id).all()
        cats_procesadas = [{"id": c.id, "name": c.name} for c in cats_db] if cats_db else [{"id": 0, "name": "General"}]
        
        jugadores_raw = db.query(Player).filter(and_(Player.club_id == club_id, Player.is_approved == True)).all()
        
        jugadores_procesados = []
        for p in jugadores_raw:
            mis_categorias = [c.name for c in p.player_categories_list]
            if not mis_categorias: mis_categorias = ["General"]
            jugadores_procesados.append({
                "id": p.id, "name": p.name, "avatar_url": p.avatar_url, 
                "eternal_points": int(p.eternal_points),
                "season_points": int(p.season_points),
                "monthly_points": int(p.monthly_points),
                "stars": p.stars,
                "medals": p.medals,
                "categorias": mis_categorias, "rank": p.prestige_rank
            })

        # ORDENAR POR PUNTOS DE TEMPORADA (Regla de Oro de Gamificación TOH)
        jugadores_procesados.sort(key=lambda x: x["season_points"], reverse=True)
        retos_db = db.query(Match).filter(Match.is_finished == False).all()

        return templates.TemplateResponse("ranking.html", {
            "request": request, "jugadores": jugadores_procesados, "retos": retos_db, 
            "club_id": club_id, "sponsor": identidad_visual, "categorias": cats_procesadas
        })
    except Exception as e:
        print(f"❌ Error visualizando web: {e}")
        return HTMLResponse(content="Error en Muro de la Fama", status_code=500)

@app.get("/api/player/{player_id}/stats")
async def obtener_expediente_tactico(player_id: int, db: Session = Depends(get_db)):
    try:
        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️] -> Extrayendo Expediente Táctico para ID: {player_id}{C_END}")
        
        jugador = db.query(Player).filter(Player.id == player_id).first()
        if not jugador: return {"status": "error", "mensaje": "Guerrero no localizado."}

        batallas = db.query(Match).filter(
            and_(
                or_(
                    Match.player_1_id == player_id, 
                    Match.player_2_id == player_id,
                    Match.player_3_id == player_id,
                    Match.player_4_id == player_id
                ), 
                Match.is_finished == True
            )
        ).all()

        print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡] -> Expediente compilado.{C_END}")
        
        return {
            "status": "success",
            "perfil": {
                "id": jugador.id,
                "nombre": jugador.name,
                "rango": jugador.prestige_rank,
                "wins": jugador.wins,
                "losses": jugador.losses,
                "total": jugador.wins + jugador.losses,
                "avatar_url": jugador.avatar_url or "/static/logo_pasto.jpg"
            },
            "recientes": []
        }
    except Exception as e:
        print(f"❌ Error en Expediente: {e}")
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 🛡️ RESET NUCLEAR: LIENZO EN BLANCO (SOCIOS VACÍOS)
# ============================================================
@app.get("/nuclear-reset")
def nuclear_reset():
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        
        from models import Country, City, Club, WhiteList, Category
        
        # 1. Crear geografía
        colombia = Country(name="Colombia")
        db.add(colombia); db.flush()
        
        pasto = City(name="Pasto", country_id=colombia.id)
        db.add(pasto); db.flush()
        
        # 2. Crear Club de Padel (Muro vacío)
        club = Club(name="Pasto Padel Club", admin_phone="573152405542", city_id=pasto.id)
        db.add(club); db.flush()
        
        # 3. Crear Categorías Oficiales de TOH Padel
        categorias_nombres = [
            "Primera Categoría", "Segunda Categoría", "Tercera Categoría", 
            "Cuarta Categoría", "Quinta Categoría", "Sexta Categoría", 
            "Séptima Categoría", "Octava Categoría", "Damas", "Infantil"
        ]
        
        for nombre_cat in categorias_nombres:
            nueva_cat = Category(name=nombre_cat, club_id=club.id)
            db.add(nueva_cat)
            
        db.flush()
        
        # 4. Guardar en WhiteList para Daniel
        db.add(WhiteList(phone_number="573152405542", full_name="Daniel (CEO)", club_id=club.id))
        
        db.commit()
        db.close()
        return {"status": "success", "message": "Arena oficial TOH configurada en limpio. ¡Muro vacío y listo para recibir guerreros!"}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

async def procesar_mensaje_ia(telefono: str, texto: str, tipo: str, enviar_real: bool = False, media_id: str = None):
    # (Mantener igual...)
    pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
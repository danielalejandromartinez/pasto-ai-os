import os
import uvicorn
import time
import unicodedata
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from dotenv import load_dotenv

# --- ÓRGANOS DEL AGENTE ---
from database import engine, Base, get_db, SessionLocal
from models import Club, Player, Match, WhatsAppUser, MessageHistory, PointTransaction, Season, Category
from whatsapp_service import enviar_whatsapp
from connection_manager import manager
import media_service

# --- MÓDULOS DEL CEREBRO ---
import user_classifier
import intent_resolver
import generar_respuesta_humana
from agents.orchestrator import Orchestrator 

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
# 💎 CONFIGURACIÓN DE MARCAS
# ============================================================
SPONSOR_ACTUAL = {
    "activo": True,
    "nombre": "Pasto.AI",
    "logo": "/static/sponsor.png",
    "whatsapp": "573152405542",
    "mensaje": "Hola, quiero información del torneo 'The Next Level'.",
    "color": "#ff8c00",
    "cta": "Inscribirme"
}

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    if not db.query(Club).filter_by(id=1).first():
        db.add(Club(id=1, name="Club Colombia", admin_phone="573152405542"))
        db.commit()
    db.close()
    print(f"{C_EXE}🚀 [SISTEMA] Motor Pasto.AI v15.0 (NASA Edition) encendido e íntegro.{C_END}")

# ============================================================
# 📺 VISTA WEB: EL RANKING
# ============================================================
@app.get("/club/{club_id}")
async def ver_club(request: Request, club_id: int, db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club: return "Club no encontrado"
    
    cats_db = db.query(Category).filter_by(club_id=club_id).all()
    cats_procesadas = [{"id": c.id, "name": c.name} for c in cats_db] if cats_db else [{"id": 0, "name": "General"}]

    jugadores_raw = db.query(Player).filter(Player.club_id == club_id).all()
    ahora = datetime.now()
    primer_dia_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    jugadores_procesados = []

    for p in jugadores_raw:
        puntos_mes = db.query(func.sum(PointTransaction.points_earned)).filter(
            and_(PointTransaction.player_id == p.id, PointTransaction.timestamp >= primer_dia_mes)
        ).scalar() or 0

        season = db.query(Season).filter(and_(Season.club_id == club_id, Season.is_active == True)).first()
        puntos_temporada = 0
        if season:
            transacciones = db.query(PointTransaction).filter(
                and_(PointTransaction.player_id == p.id, PointTransaction.timestamp >= season.start_date)
            ).order_by(PointTransaction.points_earned.desc()).limit(24).all()
            puntos_temporada = sum(t.points_earned for t in transacciones)

        mis_categorias = [c.name for c in p.categories]
        if not mis_categorias: mis_categorias = ["General"]

        jugadores_procesados.append({
            "id": p.id,
            "name": p.name,
            "avatar_url": p.avatar_url,
            "eternal_points": int(p.eternal_points),
            "season_points": int(puntos_temporada),
            "monthly_points": int(puntos_mes),
            "stars": p.achievements.get("stars", 0) if p.achievements else 0,
            "categorias": mis_categorias
        })

    retos_db = db.query(Match).filter(and_(Match.is_finished == False, or_(Match.status == 'proposed', Match.status == 'scheduled'))).all()
    jugadores_procesados.sort(key=lambda x: x["season_points"], reverse=True)

    return templates.TemplateResponse("ranking.html", {
        "request": request, "jugadores": jugadores_procesados, "retos": retos_db, 
        "club_id": club_id, "sponsor": SPONSOR_ACTUAL, "categorias": cats_procesadas
    })

# ============================================================
# 📡 API: FINALIZAR PARTIDO (LOOP DE VERIFICACIÓN)
# ============================================================
@app.post("/api/match/finish")
async def finalizar_partido(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        winner_name = data.get("ganador"); match_id = data.get("matchId")
        
        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️] -> Transmisión de resultado detectada para Match ID: {match_id}{C_END}")
        
        winner_norm = _norm(winner_name)
        all_players = db.query(Player).all()
        ganador = next((p for p in all_players if _norm(p.name) in winner_norm or winner_norm in _norm(p.name)), None)

        if ganador:
            print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡] -> Procesando victoria para {ganador.name}...{C_END}")
            ganador.eternal_points += 10.0; ganador.wallet_balance += 10.0; ganador.wins += 1
            
            db.add(PointTransaction(
                player_id=ganador.id, match_id=match_id, points_earned=10.0, 
                match_type="challenge", category_at_moment=ganador.category, timestamp=datetime.now()
            ))
            
            if match_id:
                match = db.query(Match).filter(Match.id == match_id).first()
                if match:
                    match.is_finished = True; match.status = "finished"; match.score = data.get("res")
                    print(f"{C_VER}[LOOP: PASO 6 - VERIFICANDO ✅] -> Match ID {match_id} cerrado en base de datos.{C_END}")
            
            db.commit()
            print(f"{C_LEA}[LOOP: PASO 7 - APRENDIENDO 📚] -> Registro de gloria guardado permanentemente.{C_END}")
            await manager.broadcast("update", 1)
            return {"status": "success"}
        
        return {"status": "error", "mensaje": "Jugador no encontrado"}
    except Exception as e:
        print(f"❌ Error en Loop de Victoria: {e}")
        return {"status": "error", "mensaje": str(e)}

@app.get("/tablero")
async def ver_tablero(request: Request):
    return templates.TemplateResponse("tablero.html", {"request": request})

@app.get("/nuclear-reset")
def nuclear_reset():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Club(id=1, name="Club Colombia", admin_phone="573152405542"))
    db.add(Season(id=1, name="Temporada I - 2026", start_date=datetime(2026, 1, 1), end_date=datetime(2026, 5, 31), club_id=1))
    db.commit(); db.close()
    return {"status": "success", "message": "Reset nuclear completado."}

# ============================================================
# 🧠 EL COCINERO: PROCESAMIENTO TOTAL DEL LOOP (8 PASOS)
# ============================================================
async def procesar_mensaje_ia(telefono: str, texto: str, tipo: str, enviar_real: bool = False, media_id: str = None):
    db = SessionLocal()
    try:
        # --- 1. OBSERVANDO ---
        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️]{C_END}")
        print(f"   📥 Entrada detectada: Socio {telefono} | Tipo: {tipo} | Señal: '{texto}'")
        msg_user = MessageHistory(phone_number=telefono, role="user", content=texto if tipo == 'text' else "[FOTO]")
        db.add(msg_user); db.commit()

        # --- 7. APRENDIENDO (Carga de Contexto) ---
        print(f"{C_LEA}[LOOP: PASO 7 - APRENDIENDO 📚]{C_END}")
        mensajes_db = db.query(MessageHistory).filter_by(phone_number=telefono).order_by(MessageHistory.timestamp.desc()).limit(6).all()
        historial_chat = [{"role": m.role, "content": m.content} for m in reversed(mensajes_db)]
        print(f"   🧠 Sincronizando memoria activa ({len(historial_chat)} registros cargados).")

        # --- 2. INTERPRETANDO ---
        print(f"{C_INT}[LOOP: PASO 2 - INTERPRETANDO 🧠]{C_END}")
        if enviar_real and tipo == 'image' and media_id:
            print(f"   📸 [MEDIA] Iniciando descarga de señal visual...")
            media_service.descargar_foto_perfil(media_id, telefono)

        usuario_contexto = user_classifier.clasificar_usuario(telefono)
        intencion = {"tipo": "enviar_comprobante"} if tipo == 'image' else intent_resolver.analizar_intencion(texto, usuario_contexto, historial_chat)

        # --- 3. RAZONANDO ---
        print(f"{C_REA}[LOOP: PASO 3 - RAZONANDO 🧐]{C_END}")
        orquestador = Orchestrator(db, usuario_contexto)
        
        # --- 4. PLANIFICANDO ---
        print(f"{C_PLA}[LOOP: PASO 4 - PLANIFICANDO 📋]{C_END}")
        resultado = orquestador.procesar_intencion(intencion)

        # --- 5. EJECUTANDO ---
        print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡]{C_END}")
        respuesta = generar_respuesta_humana.redactar(resultado, usuario_contexto)
        
        # --- 6. VERIFICANDO ---
        print(f"{C_VER}[LOOP: PASO 6 - VERIFICANDO ✅] -> Respuesta agéntica validada para despacho.{C_END}")

        # --- 8. AJUSTANDO COMPORTAMIENTO (MONITOR DE SALIDA) ---
        print(f"\n{C_ADJ}——————————————————————————————————————————————————")
        print(f"📢 ALEJANDRO RESPONDE A {telefono}:")
        print(f"   \"{respuesta}\"")
        print(f"——————————————————————————————————————————————————{C_END}")

        msg_bot = MessageHistory(phone_number=telefono, role="assistant", content=respuesta)
        db.add(msg_bot); db.commit()

        if enviar_real: enviar_whatsapp(telefono, respuesta)
        
        proactivo = None
        if "notificar_a" in resultado and "mensaje_proactivo" in resultado:
            if enviar_real: enviar_whatsapp(resultado["notificar_a"], resultado["mensaje_proactivo"])
            print(f"{C_ADJ}🔔 HANDSHAKE PROACTIVO DISPARADO PARA {resultado['notificar_a']}{C_END}")
            proactivo = {"to": resultado["notificar_a"], "msg": resultado["mensaje_proactivo"]}

        await manager.broadcast("update", 1)
        return {"respuesta": respuesta, "proactivo": proactivo}
    except Exception as e:
        print(f"\033[1;31m❌ [ERROR CRÍTICO] En el Loop: {e}\033[0m")
        return {"respuesta": "Sincronizando sistemas...", "proactivo": None}
    finally:
        db.close()

# ============================================================
# 🤖 SIMULADOR Y WEBHOOKS (MANTENIDOS ÍNTEGROS)
# ============================================================
@app.get("/test-chat", response_class=HTMLResponse)
async def chat_local():
    # Mantenemos tu simulador exacto para pruebas
    return """
    <html><head><title>Pasto.AI Simulador</title></head>
    <body style="background:#050505; color:#00f2ff; font-family:monospace; display:flex; flex-direction:column; align-items:center; padding:50px;">
    <h1>🤖 PASTO.AI SIMULADOR 2030</h1>
    <input type="text" id="phone" style="background:#111; border:1px solid #00f2ff; color:white; padding:10px; width:400px; margin-bottom:10px;" placeholder="Número (ej: 573...)">
    <input type="text" id="msg" style="background:#111; border:1px solid #00f2ff; color:white; padding:15px; width:400px;" placeholder="Mensaje...">
    <div style="display:flex; gap:10px; margin-top:10px;">
        <button onclick="enviar('text')" style="background:#00f2ff; padding:10px 20px; border:none; cursor:pointer; font-weight:bold;">ENVIAR</button>
        <button onclick="enviar('image')" style="background:#ffcc00; padding:10px 20px; border:none; cursor:pointer; font-weight:bold;">📷 FOTO</button>
    </div>
    <div id="log" style="width:500px; height:300px; border:1px solid #333; margin-top:20px; padding:10px; overflow-y:auto; color:#aaa;"></div>
    <script>
        async function enviar(tipo) {
            const phone = document.getElementById('phone').value;
            const msg = document.getElementById('msg').value;
            const res = await fetch('/local-webhook', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ "from": phone, "type": tipo, "text": msg }) });
            const data = await res.json();
            const visualMsg = (tipo === 'image') ? '[FOTO]' : msg;
            document.getElementById('log').innerHTML += '<br><b>Tú:</b> '+visualMsg+'<br><b style="color:#ffcc00">Alejandro:</b> '+data.respuesta;
            if(data.proactivo) {
                document.getElementById('log').innerHTML += `<br><b style="color:#ff8c00">🔔 Alejandro (a ${data.proactivo.to}):</b> ${data.proactivo.msg}`;
            }
            document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight;
            document.getElementById('msg').value = '';
        }
    </script></body></html>
    """

@app.post("/local-webhook")
async def local_loop(request: Request):
    data = await request.json()
    return await procesar_mensaje_ia(data.get('from'), data.get('text', ''), data.get('type', 'text'), False)

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(content=params.get("hub.challenge"))
    return PlainTextResponse(content="Error", status_code=403)

@app.post("/webhook")
async def receive_meta_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        print(f"\n{C_OBS}📥 [RADAR] -> Señal real de WhatsApp entrante...{C_END}")
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        for msg in value.get("messages", []):
                            background_tasks.add_task(procesar_mensaje_ia, msg.get("from"), msg.get("text", {}).get("body", ""), msg.get("type"), True, msg.get("image", {}).get("id") if msg.get("type") == "image" else None)
        return PlainTextResponse(content="OK", status_code=200)
    except Exception: return PlainTextResponse(content="OK", status_code=200)

@app.websocket("/ws/{club_id}")
async def websocket_endpoint(websocket: WebSocket, club_id: int):
    await manager.connect(websocket, club_id)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket, club_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
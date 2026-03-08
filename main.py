import os
import uvicorn
import time
import unicodedata
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from dotenv import load_dotenv

# --- ÓRGANOS DEL AGENTE ---
from database import engine, Base, get_db, SessionLocal
from models import Club, Player, Match, WhatsAppUser, MessageHistory, PointTransaction, Season, Category, WhiteList
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
# 🚪 EL PORTERO DEL LOBBY (REDIRECCIÓN DE RAÍZ)
# ============================================================
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/club/1")

# ============================================================
# 📺 VISTA WEB: EL MURO DE LA FAMA (CONFIG-DRIVEN)
# ============================================================
@app.get("/club/{club_id}")
async def ver_club(request: Request, club_id: int, db: Session = Depends(get_db)):
    try:
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club: return HTMLResponse(content="Club no encontrado", status_code=404)
        
        # --- 🎨 MOTOR DE IDENTIDAD DINÁMICA ---
        settings = club.settings if club.settings else {}
        identidad_visual = {
            "activo": True,
            "nombre": club.name,
            "logo": settings.get("logo_url", "/static/logo_pasto.jpg"),
            "whatsapp": club.admin_phone,
            "mensaje": f"Hola, quiero información del club {club.name}.",
            "color": settings.get("primary_color", "#00f2ff"),
            "cta": "Inscribirme"
        }

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

            avatar = p.avatar_url if p.avatar_url else None

            jugadores_procesados.append({
                "id": p.id,
                "name": p.name,
                "avatar_url": avatar,
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
            "club_id": club_id, "sponsor": identidad_visual, "categorias": cats_procesadas
        })
    except Exception as e:
        print(f"❌ Error visualizando web: {e}")
        return HTMLResponse(content="Error en Muro de la Fama", status_code=500)

# ============================================================
# 📡 API: FINALIZAR PARTIDO (MOTOR DE INCENTIVOS 10/3)
# ============================================================
@app.post("/api/match/finish")
async def finalizar_partido(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        winner_name = data.get("ganador"); match_id = data.get("matchId")
        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️] -> Transmisión de resultado para Match ID: {match_id}{C_END}")
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match: return {"status": "error", "mensaje": "Duelo no localizado."}

        p1, p2 = match.player_1, match.player_2
        winner_norm = _norm(winner_name)
        if _norm(p1.name) in winner_norm or winner_norm in _norm(p1.name):
            ganador, participante = p1, p2
        else:
            ganador, participante = p2, p1

        print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡] -> Aplicando lógica 10/3: {ganador.name} (W) vs {participante.name} (P){C_END}")
        ganador.eternal_points += 10.0; ganador.wins += 1
        db.add(PointTransaction(player_id=ganador.id, match_id=match_id, points_earned=10.0, match_type="challenge", timestamp=datetime.now()))
        participante.eternal_points += 3.0; participante.losses += 1
        db.add(PointTransaction(player_id=participante.id, match_id=match_id, points_earned=3.0, match_type="challenge", timestamp=datetime.now()))
        match.is_finished = True; match.status = "finished"; match.score = data.get("res"); match.winner_id = ganador.id
        db.commit()
        print(f"{C_VER}[LOOP: PASO 6 - VERIFICANDO ✅] -> Muro de la Fama actualizado.{C_END}")
        await manager.broadcast("update", 1)
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Error crítico en el Juez: {e}")
        return {"status": "error", "mensaje": str(e)}

@app.get("/tablero")
async def ver_tablero(request: Request):
    return templates.TemplateResponse("tablero.html", {"request": request})

# ============================================================
# ☢️ RESET NUCLEAR (PRE-AUTORIZACIÓN DE 10 SOCIOS PARA DEMO)
# ============================================================
@app.get("/nuclear-reset")
def nuclear_reset():
    try:
        Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        demo_players = [
            ("Daniel (CEO)", "573152405542"), ("Paula", "573186597045"), ("Maria Paula", "573133969908"),
            ("Fernando", "573001112233"), ("Andres", "573002223344"), ("Carlos", "573003334455"),
            ("Diana", "573004445566"), ("Elena", "573005556677"), ("Gabriel", "573006667788"), ("Hugo", "573007778899")
        ]
        db.add(Club(id=1, name="Club Colombia", admin_phone="573152405542"))
        db.add(Season(id=1, name="Temporada I - 2026", start_date=datetime(2026, 1, 1), end_date=datetime(2026, 5, 31), club_id=1))
        for name, phone in demo_players:
            db.add(WhiteList(phone_number=phone, full_name=name, club_id=1, is_active=True))
        db.commit(); db.close()
        print(f"{C_EXE}🚀 [SISTEMA] Reset nuclear completado con 10 identidades.{C_END}")
        return {"status": "success", "message": "Reset nuclear completado con 10 identidades habilitadas."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================
# 🧠 EL COCINERO: PROCESAMIENTO TOTAL DEL LOOP (8 PASOS)
# ============================================================
async def procesar_mensaje_ia(telefono: str, texto: str, tipo: str, enviar_real: bool = False, media_id: str = None):
    db = SessionLocal()
    try:
        print(f"\n{C_LEA}[LOOP: PASO 7 - APRENDIENDO 📚]{C_END}")
        mensajes_db = db.query(MessageHistory).filter_by(phone_number=telefono).order_by(MessageHistory.timestamp.desc()).limit(6).all()
        historial_chat = [{"role": m.role, "content": m.content} for m in reversed(mensajes_db)]
        
        print(f"{C_INT}[LOOP: PASO 2 - INTERPRETANDO 🧠]{C_END}")
        if tipo == 'image':
            if enviar_real and media_id: media_service.descargar_foto_perfil(media_id, telefono)
            else: media_service.activar_foto_demo(telefono)

        usuario_contexto = user_classifier.clasificar_usuario(telefono)
        intencion = {"tipo": "enviar_comprobante"} if tipo == 'image' else intent_resolver.analizar_intencion(texto, usuario_contexto, historial_chat)
        intencion["es_demo"] = not enviar_real 

        orquestador = Orchestrator(db, usuario_contexto)
        resultado = orquestador.procesar_intencion(intencion)

        respuesta = generar_respuesta_humana.redactar(resultado, usuario_contexto)
        
        # 📢 LOG DE RESPUESTA AGÉNTICA (PASO 8)
        print(f"\n{C_ADJ}——————————————————————————————————————————————————")
        print(f"📢 [LOOP: PASO 8 - AJUSTAR COMPORTAMIENTO 🔄]")
        print(f"   ALEJANDRO RESPONDE A {usuario_contexto.get('nombre')}:")
        print(f"   \"{respuesta}\"")
        print(f"——————————————————————————————————————————————————{C_END}")

        msg_bot = MessageHistory(phone_number=telefono, role="assistant", content=respuesta)
        db.add(msg_bot); db.commit()

        if enviar_real: enviar_whatsapp(telefono, respuesta)
        
        proactivo = None
        if "notificar_a" in resultado and "mensaje_proactivo" in resultado:
            if enviar_real: enviar_whatsapp(resultado["notificar_a"], resultado["mensaje_proactivo"])
            proactivo = {"to": resultado["notificar_a"], "msg": resultado["mensaje_proactivo"]}

        await manager.broadcast("update", 1)
        return {"respuesta": respuesta, "proactivo": proactivo}
    except Exception as e:
        print(f"\033[1;31m❌ [ERROR CRÍTICO] Loop falló: {e}\033[0m")
        return {"respuesta": "Sistema en mantenimiento de prestigio...", "proactivo": None}
    finally: db.close()

# ============================================================
# 🤖 SIMULADOR PROFESIONAL PASTO.AI 2030 (v3.1 - AUTO-SCROLL)
# ============================================================
@app.get("/test-chat", response_class=HTMLResponse)
async def chat_local():
    return """
    <html>
    <head>
        <title>Pasto.AI | Agentic Sandbox</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
        <style>
            :root { --neon: #00f2ff; --bg: #050505; }
            body { background: var(--bg); color: white; font-family: 'Rajdhani', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-image: radial-gradient(circle at 50% 50%, #1a1a1a 0%, #050505 100%); }
            .terminal { width: 480px; height: 90vh; background: rgba(255,255,255,0.02); border: 1px solid rgba(0,242,255,0.2); border-radius: 32px; display: flex; flex-direction: column; backdrop-filter: blur(30px); box-shadow: 0 0 100px rgba(0,0,0,1); overflow: hidden; }
            .header { padding: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: center; }
            .header h1 { font-family: 'Orbitron'; font-size: 14px; letter-spacing: 6px; color: var(--neon); margin: 0; text-shadow: 0 0 15px var(--neon); }
            .chat-box { flex: 1; overflow-y: auto; padding: 25px; display: flex; flex-direction: column; gap: 15px; scrollbar-width: thin; scrollbar-color: var(--neon) transparent; scroll-behavior: smooth; }
            .msg { max-width: 85%; padding: 14px 20px; border-radius: 18px; font-size: 14px; line-height: 1.6; word-wrap: break-word; }
            .user { align-self: flex-end; background: var(--neon); color: black; font-weight: 800; border-bottom-right-radius: 2px; }
            .bot { align-self: flex-start; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-bottom-left-radius: 2px; color: #eee; }
            .input-area { padding: 25px; border-top: 1px solid rgba(255,255,255,0.05); background: rgba(0,0,0,0.4); }
            select, input { width: 100%; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 14px; color: white; border-radius: 12px; outline: none; font-family: 'Rajdhani'; margin-bottom: 12px; font-size: 16px; }
            select { color: var(--neon); font-family: 'Orbitron'; font-size: 10px; font-weight: bold; letter-spacing: 2px; height: 50px; cursor: pointer; }
            .btns { display: flex; gap: 12px; }
            button { flex: 1; padding: 16px; border: none; border-radius: 12px; font-family: 'Orbitron'; font-size: 10px; cursor: pointer; transition: 0.3s; letter-spacing: 3px; font-weight: 900; }
            .btn-send { background: var(--neon); color: black; }
            .btn-photo { background: transparent; border: 1px solid #ffcc00; color: #ffcc00; }
            button:hover { transform: translateY(-4px); filter: brightness(1.2); }
        </style>
    </head>
    <body>
        <div class="terminal">
            <div class="header">
                <h1>SANDBOX_OS_2030</h1>
                <div style="font-size: 8px; opacity: 0.3; margin-top: 8px;">VIRTUAL_WHATSAPP_SIMULATOR</div>
            </div>
            <div id="chat" class="chat-box">
                <div class="msg bot">Vínculo establecido. Seleccione una identidad para transmitir su señal.</div>
            </div>
            <div class="input-area">
                <select id="phone-select">
                    <option value="573152405542">👤 DANIEL (CEO) - 573152405542</option>
                    <option value="573186597045">👤 PAULA - 573186597045</option>
                    <option value="573133969908">👤 MARIA PAULA - 573133969908</option>
                    <option value="573001112233">👤 FERNANDO - 573001112233</option>
                    <option value="573002223344">👤 ANDRES - 573002223344</option>
                    <option value="573003334455">👤 CARLOS - 573003334455</option>
                    <option value="573004445566">👤 DIANA - 573004445566</option>
                    <option value="573005556677">👤 ELENA - 573005556677</option>
                    <option value="573006667788">👤 GABRIEL - 573006667788</option>
                    <option value="573007778899">👤 HUGO - 573007778899</option>
                </select>
                <input type="text" id="msg" placeholder="ENVIAR COMANDO..." onkeypress="if(event.key==='Enter') enviar('text')">
                <div class="btns">
                    <button class="btn-photo" onclick="enviar('image')">📷 SIMULAR_MEDIA</button>
                    <button class="btn-send" onclick="enviar('text')">EJECUTAR</button>
                </div>
            </div>
        </div>
        <script>
            async function enviar(tipo) {
                const phone = document.getElementById('phone-select').value;
                const msgInput = document.getElementById('msg');
                const text = msgInput.value;
                if(!text && tipo === 'text') return;
                const chat = document.getElementById('chat');
                const userDiv = document.createElement('div'); userDiv.className = 'msg user';
                userDiv.innerText = tipo === 'image' ? '📸 [MEDIA_SIGNAL_SENT]' : text;
                chat.appendChild(userDiv);
                msgInput.value = ''; chat.scrollTop = chat.scrollHeight;
                try {
                    const res = await fetch('/local-webhook', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ "from": phone, "type": tipo, "text": text }) });
                    const data = await res.json();
                    const botDiv = document.createElement('div'); botDiv.className = 'msg bot';
                    botDiv.innerText = data.respuesta; chat.appendChild(botDiv);
                    if(data.proactivo) {
                        const proDiv = document.createElement('div'); proDiv.className = 'msg bot'; proDiv.style.color = '#ff8c00';
                        proDiv.innerHTML = `<i>🔔 Notificación a ${data.proactivo.to}:</i><br>${data.proactivo.msg}`;
                        chat.appendChild(proDiv);
                    }
                    chat.scrollTop = chat.scrollHeight;
                } catch(e) { console.error("Error núcleo."); }
            }
        </script>
    </body>
    </html>
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
async def receive_meta_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        print(f"\n{C_OBS}📥 [RADAR] -> Señal real de WhatsApp entrante...{C_END}")
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        for msg in value.get("messages", []):
                            wamid = msg.get("id")
                            telefono = msg.get("from")
                            texto = msg.get("text", {}).get("body", "")
                            tipo = msg.get("type")
                            existe = db.query(MessageHistory).filter_by(whatsapp_msg_id=wamid).first()
                            if existe: continue 
                            nuevo_registro = MessageHistory(whatsapp_msg_id=wamid, phone_number=telefono, role="user", content=texto if tipo == 'text' else f"[{tipo.upper()}]")
                            db.add(nuevo_registro); db.commit() 
                            background_tasks.add_task(procesar_mensaje_ia, telefono, texto, tipo, True, msg.get("image", {}).get("id") if tipo == "image" else None)
        return PlainTextResponse(content="OK", status_code=200) 
    except Exception as e: return PlainTextResponse(content="OK", status_code=200)

@app.websocket("/ws/{club_id}")
async def websocket_endpoint(websocket: WebSocket, club_id: int):
    await manager.connect(websocket, club_id)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket, club_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
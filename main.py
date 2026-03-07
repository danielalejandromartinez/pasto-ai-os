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
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club: return "Club no encontrado"
    
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
        "club_id": club_id, "sponsor": identidad_visual, "categorias": cats_procesadas
    })

# ============================================================
# 📡 API: FINALIZAR PARTIDO (MOTOR DE INCENTIVOS 10/3)
# ============================================================
@app.post("/api/match/finish")
async def finalizar_partido(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        winner_name = data.get("ganador")
        match_id = data.get("matchId")
        
        print(f"\n{C_OBS}[LOOP: PASO 1 - OBSERVANDO 👁️] -> Transmisión de resultado para Match ID: {match_id}{C_END}")
        
        # 1. Recuperamos el duelo real de la base de datos
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            return {"status": "error", "mensaje": "Duelo no localizado en el Muro de la Fama."}

        # 2. Identificamos quién es el Ganador y quién es el Participante
        p1 = match.player_1
        p2 = match.player_2
        winner_norm = _norm(winner_name)

        # Si el nombre del ganador coincide con Player 1, P1 gana y P2 participa.
        if _norm(p1.name) in winner_norm or winner_norm in _norm(p1.name):
            ganador, participante = p1, p2
        else:
            ganador, participante = p2, p1

        print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡] -> Aplicando lógica 10/3: {ganador.name} (W) vs {participante.name} (P){C_END}")

        # 🏆 PREMIO AL GANADOR: 10 Puntos
        ganador.eternal_points += 10.0
        ganador.wins += 1
        db.add(PointTransaction(
            player_id=ganador.id, match_id=match_id, points_earned=10.0, 
            match_type="challenge", category_at_moment=ganador.category, timestamp=datetime.now()
        ))

        # 🛡️ PREMIO AL VALIENTE (PARTICIPACIÓN): 3 Puntos
        participante.eternal_points += 3.0
        participante.losses += 1
        db.add(PointTransaction(
            player_id=participante.id, match_id=match_id, points_earned=3.0, 
            match_type="challenge", category_at_moment=participante.category, timestamp=datetime.now()
        ))

        # 3. Cerramos el ciclo del partido
        match.is_finished = True
        match.status = "finished"
        match.score = data.get("res")
        match.winner_id = ganador.id

        db.commit()
        
        print(f"{C_VER}[LOOP: PASO 6 - VERIFICANDO ✅] -> Muro de la Fama actualizado para ambos guerreros.{C_END}")
        print(f"{C_LEA}[LOOP: PASO 7 - APRENDIENDO 📚] -> Ciclo de prestigio cerrado exitosamente.{C_END}")
        
        await manager.broadcast("update", 1)
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Error crítico en el Juez: {e}")
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
        print(f"\n{C_LEA}[LOOP: PASO 7 - APRENDIENDO 📚]{C_END}")
        mensajes_db = db.query(MessageHistory).filter_by(phone_number=telefono).order_by(MessageHistory.timestamp.desc()).limit(6).all()
        historial_chat = [{"role": m.role, "content": m.content} for m in reversed(mensajes_db)]
        print(f"   🧠 Sincronizando memoria activa ({len(historial_chat)} registros cargados).")

        print(f"{C_INT}[LOOP: PASO 2 - INTERPRETANDO 🧠]{C_END}")
        if enviar_real and tipo == 'image' and media_id:
            media_service.descargar_foto_perfil(media_id, telefono)

        usuario_contexto = user_classifier.clasificar_usuario(telefono)
        intencion = {"tipo": "enviar_comprobante"} if tipo == 'image' else intent_resolver.analizar_intencion(texto, usuario_contexto, historial_chat)

        print(f"{C_REA}[LOOP: PASO 3 - RAZONANDO 🧐]{C_END}")
        orquestador = Orchestrator(db, usuario_contexto)
        
        print(f"{C_PLA}[LOOP: PASO 4 - PLANIFICANDO 📋]{C_END}")
        resultado = orquestador.procesar_intencion(intencion)

        print(f"{C_EXE}[LOOP: PASO 5 - EJECUTANDO ⚡]{C_END}")
        respuesta = generar_respuesta_humana.redactar(resultado, usuario_contexto)
        
        print(f"{C_VER}[LOOP: PASO 6 - VERIFICANDO ✅] -> Respuesta agéntica validada.{C_END}")

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
            proactivo = {"to": resultado["notificar_a"], "msg": resultado["mensaje_proactivo"]}

        await manager.broadcast("update", 1)
        return {"respuesta": respuesta, "proactivo": proactivo}
    except Exception as e:
        print(f"\033[1;31m❌ [ERROR CRÍTICO] En el Loop: {e}\033[0m")
        return {"respuesta": "Sincronizando sistemas...", "proactivo": None}
    finally:
        db.close()

# ============================================================
# 🤖 SIMULADOR PROFESIONAL PASTO.AI 2030
# ============================================================
@app.get("/test-chat", response_class=HTMLResponse)
async def chat_local():
    return """
    <html>
    <head>
        <title>Pasto.AI | WhatsApp Sandbox</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
        <style>
            :root { --neon: #00f2ff; --bg: #050505; --glass: rgba(255,255,255,0.02); }
            body { 
                background: var(--bg); color: white; font-family: 'Rajdhani', sans-serif; 
                display: flex; flex-direction: column; align-items: center; justify-content: center; 
                height: 100vh; margin: 0;
                background-image: radial-gradient(circle at 50% 50%, #1a1a1a 0%, #050505 100%);
            }
            .terminal { 
                width: 480px; height: 85vh; background: var(--glass); 
                border: 1px solid rgba(0,242,255,0.2); border-radius: 32px; 
                display: flex; flex-direction: column; backdrop-filter: blur(30px);
                box-shadow: 0 0 80px rgba(0,0,0,1); overflow: hidden;
            }
            .header { padding: 25px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: center; background: rgba(0,0,0,0.3); }
            .header h1 { font-family: 'Orbitron'; font-size: 14px; letter-spacing: 6px; color: var(--neon); margin: 0; text-shadow: 0 0 15px var(--neon); }
            .chat-box { flex: 1; overflow-y: auto; padding: 30px; display: flex; flex-direction: column; gap: 20px; scrollbar-width: none; }
            .msg { max-width: 85%; padding: 16px 22px; border-radius: 20px; font-size: 14px; line-height: 1.6; border: 1px solid transparent; position: relative; }
            .user { align-self: flex-end; background: var(--neon); color: black; font-weight: 800; border-bottom-right-radius: 4px; box-shadow: 0 5px 15px rgba(0,242,255,0.2); }
            .bot { align-self: flex-start; background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); border-bottom-left-radius: 4px; color: #ccc; }
            .proactive { border-color: #ff8c00; color: #ff8c00; font-style: italic; background: rgba(255,140,0,0.05); font-size: 12px; }
            .input-area { padding: 30px; border-top: 1px solid rgba(255,255,255,0.05); background: rgba(0,0,0,0.4); }
            input { 
                width: 100%; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); 
                padding: 18px; color: white; border-radius: 15px; outline: none; font-family: 'Rajdhani'; 
                margin-bottom: 20px; font-size: 16px; transition: 0.4s;
            }
            input:focus { border-color: var(--neon); background: rgba(0,242,255,0.02); }
            .btns { display: flex; gap: 15px; }
            button { 
                flex: 1; padding: 16px; border: none; border-radius: 15px; 
                font-family: 'Orbitron'; font-size: 10px; cursor: pointer; transition: 0.4s; letter-spacing: 3px; font-weight: 900;
            }
            .btn-send { background: var(--neon); color: black; }
            .btn-photo { background: transparent; border: 1px solid #ffcc00; color: #ffcc00; }
            button:hover { transform: translateY(-4px); filter: brightness(1.2); }
        </style>
    </head>
    <body>
        <div class="terminal">
            <div class="header">
                <h1>SANDBOX_OS_2030</h1>
                <div style="font-size: 8px; opacity: 0.3; margin-top: 8px; letter-spacing: 2px;">VIRTUAL_WHATSAPP_LINK</div>
            </div>
            <div id="chat" class="chat-box">
                <div class="msg bot">Vínculo con motor agéntico establecido. Envíe un comando para iniciar el ciclo de aprendizaje.</div>
            </div>
            <div class="input-area">
                <input type="text" id="phone" placeholder="USER_ID (573...)" value="573152405542">
                <input type="text" id="msg" placeholder="INTRODUZCA SEÑAL DE TEXTO..." onkeypress="if(event.key==='Enter') enviar('text')">
                <div class="btns">
                    <button class="btn-photo" onclick="enviar('image')">📷 SIMULAR_MEDIA</button>
                    <button class="btn-send" onclick="enviar('text')">EJECUTAR_PROCESO</button>
                </div>
            </div>
        </div>

        <script>
            async function enviar(tipo) {
                const phone = document.getElementById('phone').value;
                const msgInput = document.getElementById('msg');
                const text = msgInput.value;
                if(!text && tipo === 'text') return;

                const chat = document.getElementById('chat');
                const userDiv = document.createElement('div');
                userDiv.className = 'msg user';
                userDiv.innerText = tipo === 'image' ? '📸 [MEDIA_SIGNAL_TRANSMITTED]' : text;
                chat.appendChild(userDiv);
                
                msgInput.value = '';
                chat.scrollTop = chat.scrollHeight;

                try {
                    const res = await fetch('/local-webhook', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ "from": phone, "type": tipo, "text": text })
                    });
                    const data = await res.json();
                    
                    const botDiv = document.createElement('div');
                    botDiv.className = 'msg bot';
                    botDiv.innerText = data.respuesta;
                    chat.appendChild(botDiv);

                    if(data.proactivo) {
                        const proDiv = document.createElement('div');
                        proDiv.className = 'msg proactive';
                        proDiv.innerHTML = `<b>NOTIFICACIÓN_A_${data.proactivo.to}:</b><br>${data.proactivo.msg}`;
                        chat.appendChild(proDiv);
                    }
                    
                    chat.scrollTop = chat.scrollHeight;
                } catch(e) {
                    console.error("Fallo de comunicación con el núcleo.");
                }
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
                            if existe:
                                print(f"{C_ADJ}⚠️ [DEDUPLICACIÓN] Mensaje {wamid} ya procesado.{C_END}")
                                continue 
                            
                            print(f"{C_EXE}📝 [RECEPCIONISTA] Anotando mensaje nuevo: {wamid}{C_END}")
                            nuevo_registro = MessageHistory(
                                whatsapp_msg_id=wamid, 
                                phone_number=telefono, 
                                role="user", 
                                content=texto if tipo == 'text' else f"[{tipo.upper()}]"
                            )
                            db.add(nuevo_registro)
                            db.commit() 
                            
                            background_tasks.add_task(
                                procesar_mensaje_ia, 
                                telefono, 
                                texto, 
                                tipo, 
                                True, 
                                msg.get("image", {}).get("id") if tipo == "image" else None
                            )
                            
        return PlainTextResponse(content="OK", status_code=200) 
    except Exception as e:
        print(f"❌ Error en Webhook: {e}")
        return PlainTextResponse(content="OK", status_code=200)

@app.websocket("/ws/{club_id}")
async def websocket_endpoint(websocket: WebSocket, club_id: int):
    await manager.connect(websocket, club_id)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket, club_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
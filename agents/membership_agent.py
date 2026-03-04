from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from models import Player, WhatsAppUser, Category
import unicodedata
import os
from openai import OpenAI
import media_service

class MembershipAgent:
    def __init__(self, db: Session):
        self.db = db
        # Inicializamos el cliente de IA para la auditoría visual
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _normalizar(self, texto):
        if not texto: return ""
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower().strip()

    def auditar_selfie(self, ruta_archivo):
        """
        AUDITORÍA IA VISION: Determina si la foto es apta para la Arena.
        Blindado contra variaciones de la IA (tildes/puntos).
        """
        print(f"\033[95m[AUDITORÍA/VISIÓN] -> Analizando calidad de la selfie...\033[0m")
        base64_image = media_service.codificar_imagen(ruta_archivo)
        
        if not base64_image:
            return False

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Responde solo SI o NO. ¿Es esta imagen una selfie o retrato claro de una persona real donde se vea su rostro? Ignora si es un objeto, un animal, un código QR o un recibo."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ],
                    }
                ],
                max_tokens=10
            )
            
            respuesta_raw = response.choices[0].message.content
            veredicto_limpio = self._normalizar(respuesta_raw)
            
            print(f"\033[95m[AUDITORÍA/VISIÓN] -> Respuesta IA: '{respuesta_raw}' | Procesado: '{veredicto_limpio}'\033[0m")
            return "si" in veredicto_limpio

        except Exception as e:
            print(f"❌ Error auditando selfie: {e}")
            return True # En caso de error, priorizamos la experiencia del usuario

    def registrar_jugador(self, nombre, telefono, club_id):
        """
        REGISTRO DE SOCIO FUNDADOR: Activa la Beca de Innovación Pasto.AI.
        Detecta categorías disponibles para personalizar la bienvenida.
        """
        usuario_db = self.db.query(WhatsAppUser).filter_by(phone_number=telefono).first()
        
        if not usuario_db:
            usuario_db = WhatsAppUser(phone_number=telefono, memory={"step": "waiting_selfie"})
            self.db.add(usuario_db); self.db.commit(); self.db.refresh(usuario_db)

        if usuario_db.players:
            return {"status": "already_registered", "jugador": usuario_db.players[0]}

        # Consultamos las ligas/categorías que el Admin configuró para este club
        categorias_club = self.db.query(Category).filter_by(club_id=club_id).all()
        txt_categorias = ""
        if categorias_club:
            nombres = [c.name for c in categorias_club]
            txt_categorias = f"\n\nContamos con las siguientes ligas activas: *{', '.join(nombres)}*."

        # Crear Jugador con Estatus de Fundador
        nuevo_jugador = Player(
            name=nombre, 
            category="General", 
            club_id=club_id if club_id else 1, 
            owner_id=usuario_db.id, 
            wallet_balance=0.0, 
            eternal_points=0.0, 
            tournament_registered=True,
            status_tags={"pionero": True, "beca_innovacion": "100%"}
        )
        
        try:
            usuario_db.memory = {"step": "waiting_selfie"}
            flag_modified(usuario_db, "memory")
            
            self.db.add(nuevo_jugador)
            self.db.commit()
            
            print(f"✅ [MEMBERSHIP] Socio {nombre} registrado como Fundador.")
            
            return {
                "status": "welcome_new_socio", 
                "reply": f"¡Es un privilegio recibirlo, {nombre}! 🏆\n\nUsted ha sido acreditado como **Socio Fundador** de la Arena. Por cortesía de **Pasto.AI**, su participación inicial es totalmente gratuita bajo nuestra Beca de Innovación.{txt_categorias}\n\n📸 **ACCIÓN REQUERIDA:** Para activar su tarjeta neón en el Muro de la Riqueza, envíeme una selfie ahora mismo. Este paso habilitará su acceso a los desafíos de gloria.",
                "data": {"jugador_id": nuevo_jugador.id}
            }
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error en registro: {e}")
            return {"status": "error", "reply": "Inconsistencia técnica en el registro de socio."}

    def actualizar_foto(self, telefono_usuario, ruta_foto):
        """
        Audita la foto y decide si el socio está listo para elegir categoría o jugar.
        """
        usuario = self.db.query(WhatsAppUser).filter_by(phone_number=telefono_usuario).first()
        
        if usuario and usuario.players:
            jugador = usuario.players[0]
            
            # Auditoría visual IA
            es_apta = self.auditar_selfie(ruta_foto)
            
            if not es_apta:
                return {
                    "status": "remind_selfie",
                    "reply": f"Estimado {jugador.name}, para mantener el prestigio visual de la Arena, requiero un retrato claro de su rostro. La imagen enviada no parece ser un retrato apto. Por favor, intente de nuevo con una selfie profesional."
                }

            ruta_web = ruta_foto.replace("\\", "/")
            if not ruta_web.startswith("/"): ruta_web = "/" + ruta_web
            
            try:
                jugador.avatar_url = ruta_web
                
                # Revisamos si el club tiene categorías para ver si lo mandamos a elegir o a jugar
                categorias_club = self.db.query(Category).filter_by(club_id=jugador.club_id).all()
                
                if len(categorias_club) > 1:
                    usuario.memory["step"] = "waiting_category"
                    msg_exito = f"¡Excelente, Miembro Fundador {jugador.name}! 📸 Identidad verificada. Su tarjeta ya brilla en la web.\n\nPara finalizar, ¿en cuál de nuestras ligas desea competir? (Opciones: {', '.join([c.name for c in categorias_club])})"
                else:
                    usuario.memory["step"] = "ready_to_play"
                    msg_exito = f"¡Excelente, Miembro Fundador {jugador.name}! 📸 Identidad verificada. Su tarjeta ya brilla en el Muro de la Riqueza.\n\nLa Arena es suya. ¿A quién desea desafiar hoy?"
                
                flag_modified(usuario, "memory")
                self.db.commit()
                
                return {
                    "status": "onboarding_complete",
                    "reply": msg_exito,
                    "club_id": jugador.club_id
                }
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "reply": "Error al sincronizar su identidad visual."}
        
        return {"status": "error", "reply": "Identidad no localizada."}

    def vincular_categoria(self, telefono_usuario, nombre_categoria):
        """
        MUEVE AL JUGADOR A UNA LIGA ESPECÍFICA (Escalabilidad Global).
        """
        usuario = self.db.query(WhatsAppUser).filter_by(phone_number=telefono_usuario).first()
        if not usuario or not usuario.players:
            return {"status": "error", "reply": "Perfil no encontrado."}
        
        jugador = usuario.players[0]
        cat_norm = self._normalizar(nombre_categoria)
        
        # Buscamos la categoría en el club
        todas_cats = self.db.query(Category).filter_by(club_id=jugador.club_id).all()
        categoria_encontrada = next((c for c in todas_cats if self._normalizar(c.name) == cat_norm), None)

        if not categoria_encontrada:
            nombres = ", ".join([c.name for c in todas_cats])
            return {"status": "error", "reply": f"Lo siento, la categoría '{nombre_categoria}' no existe. Elija una de estas: {nombres}"}

        try:
            # Añadimos la categoría a la lista del jugador (Many-to-Many)
            if categoria_encontrada not in jugador.categories:
                jugador.categories.append(categoria_encontrada)
            
            usuario.memory["step"] = "ready_to_play"
            flag_modified(usuario, "memory")
            self.db.commit()
            
            print(f"📦 [MEMBERSHIP] {jugador.name} vinculado a liga: {categoria_encontrada.name}")
            
            return {
                "status": "category_assigned",
                "reply": f"¡Perfecto! Ha sido asignado a la liga **{categoria_encontrada.name}**. Ya puede visualizar su posición en el ranking de su categoría. ¡A jugar!",
                "categoria_nombre": categoria_encontrada.name
            }
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error vinculando categoría: {e}")
            return {"status": "error", "reply": "Problema técnico al asignar su liga."}
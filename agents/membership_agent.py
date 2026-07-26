from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from models import Player, WhatsAppUser, Category, WhiteList # ✅ Añadido WhiteList
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
            return "si" in veredicto_limpio
        except Exception as e:
            print(f"❌ Error auditando selfie: {e}")
            return True # Priorizamos experiencia de usuario en caso de caída de API

    def registrar_jugador(self, nombre, telefono, club_id):
        """
        REGISTRO DE SOCIO: Compatible con WhatsApp y PWA 2050.
        """
        # 1. Verificar si ya es un usuario de WhatsApp conocido
        usuario_db = self.db.query(WhatsAppUser).filter_by(phone_number=telefono).first()
        
        # 🛡️ REGLA DE ORO: Si no existe, lo creamos pero verificando la WhiteList
        if not usuario_db:
            print(f"🔍 [MEMBERSHIP] Nuevo usuario detectado. Sincronizando con WhiteList...")
            invitado_vip = self.db.query(WhiteList).filter_by(phone_number=telefono).first()
            
            # Si está en WhiteList, usamos el nombre oficial para mantener el estatus
            nombre_final = invitado_vip.full_name if invitado_vip else nombre
            
            usuario_db = WhatsAppUser(phone_number=telefono, memory={"step": "waiting_selfie"})
            self.db.add(usuario_db)
            self.db.commit()
            self.db.refresh(usuario_db)
        else:
            nombre_final = nombre

        # 2. Evitar duplicidad de jugadores para el mismo usuario
        if usuario_db.players:
            print(f"⚠️ [MEMBERSHIP] El usuario {telefono} ya tiene un perfil activo.")
            return {"status": "already_registered", "jugador": usuario_db.players[0]}

        # 3. Consultar ligas para personalizar bienvenida
        categorias_club = self.db.query(Category).filter_by(club_id=club_id).all()
        txt_categorias = ""
        if categorias_club:
            nombres = [c.name for c in categorias_club]
            txt_categorias = f"\n\nLigas activas: *{', '.join(nombres)}*."

        # 4. Crear el Guerrero con Estatus Inicial
        nuevo_jugador = Player(
            name=nombre_final, 
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
            
            print(f"✅ [MEMBERSHIP] Socio {nombre_final} registrado con éxito.")
            
            return {
                "status": "welcome_new_socio", 
                "reply": f"¡Bienvenido a la Arena, {nombre_final}! 🏆{txt_categorias}",
                "data": {"jugador_id": nuevo_jugador.id}
            }
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error en registro DB: {e}")
            return {"status": "error", "reply": "Error técnico en el registro."}

    def actualizar_foto(self, telefono_usuario, ruta_foto, es_demo=False):
        """
        Vincula la identidad visual del guerrero.
        """
        usuario = self.db.query(WhatsAppUser).filter_by(phone_number=telefono_usuario).first()
        
        if usuario and usuario.players:
            jugador = usuario.players[0]
            
            # Auditoría solo si no es una demo rápida (Ahorro de IA)
            if not es_demo:
                if not self.auditar_selfie(ruta_foto):
                    return {"status": "remind_selfie", "reply": "Requiero un retrato claro de su rostro."}

            # Normalización de ruta para la web
            ruta_web = "/" + ruta_foto.replace("\\", "/").lstrip("/")
            
            try:
                jugador.avatar_url = ruta_web
                
                # Decidir siguiente paso según configuración del club
                categorias_club = self.db.query(Category).filter_by(club_id=jugador.club_id).all()
                
                if len(categorias_club) > 1:
                    usuario.memory["step"] = "waiting_category"
                    msg = "Identidad verificada. ¿En qué liga deseas competir?"
                else:
                    usuario.memory["step"] = "ready_to_play"
                    msg = "Identidad verificada. ¡La Arena es tuya!"
                
                flag_modified(usuario, "memory")
                self.db.commit()
                
                return {"status": "onboarding_complete", "reply": msg, "club_id": jugador.club_id}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "reply": "Error al sincronizar foto."}
        
        return {"status": "error", "reply": "Identidad no localizada."}

    def vincular_categoria(self, telefono_usuario, nombre_categoria):
        """
        MUEVE AL JUGADOR A UNA LIGA ESPECÍFICA.
        """
        usuario = self.db.query(WhatsAppUser).filter_by(phone_number=telefono_usuario).first()
        if not usuario or not usuario.players:
            return {"status": "error", "reply": "Perfil no encontrado."}
        
        jugador = usuario.players[0]
        cat_norm = self._normalizar(nombre_categoria)
        todas_cats = self.db.query(Category).filter_by(club_id=jugador.club_id).all()
        
        categoria_encontrada = next((c for c in todas_cats if self._normalizar(c.name) == cat_norm), None)

        if not categoria_encontrada:
            return {"status": "error", "reply": "La categoría no existe."}

        try:
            if categoria_encontrada not in jugador.player_categories_list:
                jugador.player_categories_list.append(categoria_encontrada)
            
            usuario.memory["step"] = "ready_to_play"
            flag_modified(usuario, "memory")
            self.db.commit()
            return {"status": "category_assigned", "reply": f"Asignado a la liga {categoria_encontrada.name}."}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "reply": "Error técnico al asignar liga."}
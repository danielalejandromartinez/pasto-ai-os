from database import SessionLocal
from models import WhatsAppUser, Player, Club, WhiteList
import os

# --- PROTOCOLO DE AUTORIDAD SUPREMA ---
SUPER_ADMIN_PHONE = "573152405542" 

def clasificar_usuario(telefono: str):
    """
    SISTEMA DE IDENTIFICACIÓN Y ACCESO PASTO.AI V14.0.
    Misión: Garantizar Identidad Nominal Instantánea (Nivel de Lujo 5 Estrellas).
    Paso del Loop: [1. OBSERVAR 👁️] & [2. INTERPRETAR 🧠]
    """
    db = SessionLocal()
    
    # 🎨 [LOOP: PASO 1 - OBSERVAR 👁️]
    print(f"\n\033[1;94m" + "—"*60)
    print(f"🛡️ [PORTERO/OBSERVAR] -> Escaneando identidad nominal: {telefono}")
    print("—"*60 + "\033[0m")

    try:
        # [PASO 2: INTERPRETAR 🧠] - Buscamos primero en la lista de Invitados VIP (WhiteList)
        # Este es nuestro "Libro de Oro" donde están los nombres reales.
        vip_invitado = db.query(WhiteList).filter_by(phone_number=telefono, is_active=True).first()
        nombre_vip = vip_invitado.full_name if vip_invitado else "Desconocido"

        # 1. REGLA DE AUTORIDAD (Super Admin)
        if telefono == SUPER_ADMIN_PHONE:
            print(f"\033[1;92m👑 [PORTERO/VERIFICAR ✅] -> ¡ACCESO TOTAL! El CEO está en la Arena.\033[0m")
            
            # Buscamos si tiene perfil, pero priorizamos el nombre de la WhiteList si existe
            usuario_db = db.query(WhatsAppUser).filter_by(phone_number=telefono).first()
            jugador = usuario_db.players[0] if usuario_db and usuario_db.players else None
            
            # [PASO 8: AJUSTAR 🔄] -> Usamos el nombre más prestigioso
            nombre_final = nombre_vip if nombre_vip != "Desconocido" else (jugador.name if jugador else "Daniel (CEO)")

            return {
                "telefono": telefono,
                "nombre": nombre_final,
                "rol": "SUPER_ADMIN",
                "club_id": jugador.club_id if jugador else 1,
                "es_nuevo": False if jugador else True,
                "jugador_id": jugador.id if jugador else None
            }

        # 2. VERIFICACIÓN DE SOCIO AUTORIZADO (WhiteList)
        if vip_invitado:
            print(f"\033[1;94m📖 [PORTERO/VERIFICAR ✅] -> Socio localizado en WhiteList: {nombre_vip}\033[0m")
            
            usuario_db = db.query(WhatsAppUser).filter_by(phone_number=telefono).first()
            jugador = usuario_db.players[0] if usuario_db and usuario_db.players else None
            
            if jugador:
                print(f"\033[1;32m✅ [PORTERO/ROLES] -> Jugador Activo identificado por nombre VIP: {nombre_vip}\033[0m")
                return {
                    "telefono": telefono,
                    "nombre": nombre_vip, # Siempre usamos el nombre de la WhiteList para mantener el lujo
                    "rol": "JUGADOR",
                    "club_id": jugador.club_id,
                    "es_nuevo": False,
                    "jugador_id": jugador.id
                }
            else:
                print(f"\033[1;33m🆕 [PORTERO/ROLES] -> Invitado VIP sin perfil. Onboarding para: {nombre_vip}\033[0m")
                return {
                    "telefono": telefono,
                    "nombre": nombre_vip,
                    "rol": "SOCIO_NUEVO",
                    "club_id": vip_invitado.club_id,
                    "es_nuevo": True,
                    "jugador_id": None
                }

        # 3. PROTOCOLO DE RECHAZO (No está en la lista)
        print(f"\033[1;91m🚫 [PORTERO/RECHAZAR ❌] -> ACCESO DENEGADO: {telefono} no es invitado VIP.\033[0m")
        return {
            "telefono": telefono,
            "nombre": "Desconocido",
            "rol": "NO_AUTORIZADO",
            "club_id": 1,
            "es_nuevo": True,
            "jugador_id": None
        }

    except Exception as e:
        print(f"\033[1;31m❌ [PORTERO/FALLO CRÍTICO] -> Error en el sistema de identificación: {e}\033[0m")
        return {"telefono": telefono, "nombre": "Error Sistema", "rol": "NO_AUTORIZADO", "club_id": 1, "es_nuevo": True, "jugador_id": None}

    finally:
        db.close()
from database import SessionLocal
from models import WhatsAppUser, Player, Club, WhiteList
import os

# --- PROTOCOLO DE AUTORIDAD SUPREMA ---
SUPER_ADMIN_PHONE = "573152405542" 

def clasificar_usuario(telefono: str):
    """
    SISTEMA DE IDENTIFICACIÓN Y ACCESO PASTO.AI V13.0.
    Misión: Validar identidad en tiempo real con trazabilidad total para la Demo.
    """
    db = SessionLocal()
    
    # 🎨 LOG DE OBSERVABILIDAD - Paso 1 del Loop: [OBSERVAR]
    print(f"\n\033[1;94m" + "—"*40)
    print(f"🛡️ [PORTERO/OBSERVAR] -> Escaneando identidad: {telefono}")
    print(f"—"*40 + "\033[0m")

    try:
        # 1. REGLA DE DIOS (Super Admin)
        if telefono == SUPER_ADMIN_PHONE:
            print(f"\033[1;92m👑 [PORTERO/VERIFICAR] -> ¡ACCESO TOTAL! El CEO está en la Arena.\033[0m")
            
            usuario_db = db.query(WhatsAppUser).filter_by(phone_number=telefono).first()
            jugador = usuario_db.players[0] if usuario_db and usuario_db.players else None
            
            return {
                "telefono": telefono,
                "nombre": jugador.name if jugador else "Daniel (CEO)",
                "rol": "SUPER_ADMIN",
                "club_id": jugador.club_id if jugador else 1,
                "es_nuevo": False if jugador else True,
                "jugador_id": jugador.id if jugador else None
            }

        # 2. VERIFICACIÓN DINÁMICA (Consulta en tiempo real a la WhiteList)
        # Esto permite que si el CEO autoriza a alguien por WhatsApp, el Portero lo reconozca al milisegundo.
        socio_autorizado = db.query(WhiteList).filter_by(phone_number=telefono, is_active=True).first()

        if socio_autorizado:
            print(f"\033[1;94m📖 [PORTERO/VERIFICAR] -> Socio localizado en WhiteList: {socio_autorizado.full_name}\033[0m")
            
            # Buscamos si ya tiene un perfil de jugador creado en el sistema agéntico
            usuario_db = db.query(WhatsAppUser).filter_by(phone_number=telefono).first()
            jugador = usuario_db.players[0] if usuario_db and usuario_db.players else None
            
            if jugador:
                print(f"\033[1;32m✅ [PORTERO/ROLES] -> Jugador Activo: {jugador.name}\033[0m")
                return {
                    "telefono": telefono,
                    "nombre": jugador.name,
                    "rol": "JUGADOR",
                    "club_id": jugador.club_id,
                    "es_nuevo": False,
                    "jugador_id": jugador.id
                }
            else:
                print(f"\033[1;33m🆕 [PORTERO/ROLES] -> Socio Autorizado sin perfil. Iniciando Onboarding para: {socio_autorizado.full_name}\033[0m")
                return {
                    "telefono": telefono,
                    "nombre": socio_autorizado.full_name,
                    "rol": "SOCIO_NUEVO",
                    "club_id": socio_autorizado.club_id,
                    "es_nuevo": True,
                    "jugador_id": None
                }

        # 3. PROTOCOLO DE RECHAZO (No está en la lista)
        print(f"\033[1;91m🚫 [PORTERO/RECHAZAR] -> ACCESO DENEGADO: El número {telefono} no es socio autorizado.\033[0m")
        return {
            "telefono": telefono,
            "nombre": "Desconocido",
            "rol": "NO_AUTORIZADO",
            "club_id": 1,
            "es_nuevo": True,
            "jugador_id": None
        }

    except Exception as e:
        print(f"\033[1;31m❌ [PORTERO/ERROR] -> Fallo crítico en el sistema de seguridad: {e}\033[0m")
        # Fallback de seguridad: Rechazar acceso en caso de error de DB
        return {"telefono": telefono, "nombre": "Error Sistema", "rol": "NO_AUTORIZADO", "club_id": 1, "es_nuevo": True, "jugador_id": None}

    finally:
        db.close()
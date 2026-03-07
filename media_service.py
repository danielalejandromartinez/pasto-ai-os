import os
import requests
import base64
import shutil # 🆕 Nueva herramienta para copiar archivos
from dotenv import load_dotenv

load_dotenv()
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

def descargar_foto_perfil(media_id, telefono_usuario):
    """
    EL RECAUDADOR DE IMÁGENES REALES (Meta -> Render)
    """
    try:
        print(f"\n\033[1;94m📸 [FOTÓGRAFO/MEDIA] -> Solicitando selfie real a Meta para: {telefono_usuario}\033[0m")

        if not WHATSAPP_TOKEN:
            print("❌ [ERROR] No hay WHATSAPP_TOKEN configurado.")
            return None

        url_info = f"https://graph.facebook.com/v21.0/{media_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        
        r_info = requests.get(url_info, headers=headers)
        if r_info.status_code != 200:
            print(f"❌ [ERROR META INFO]: {r_info.text}")
            return None
            
        url_imagen = r_info.json().get("url")
        if not url_imagen: return None

        print(f"⏳ [FOTÓGRAFO/MEDIA] -> Bajando archivos desde Meta...")
        r_img = requests.get(url_imagen, headers=headers)
        
        if r_img.status_code != 200: return None

        folder = "static/profiles"
        if not os.path.exists(folder): os.makedirs(folder)
            
        filename = f"{telefono_usuario}.jpg"
        path_fisico = os.path.join(folder, filename)
        
        with open(path_fisico, "wb") as f:
            f.write(r_img.content)
            
        if os.path.exists(path_fisico) and os.path.getsize(path_fisico) > 0:
            print(f"\033[1;92m✅ [ÉXITO] Selfie guardada: {path_fisico}\033[0m")
            return f"/static/profiles/{filename}"
        return None

    except Exception as e:
        print(f"❌ Critical Error en Media: {e}")
        return None

def activar_foto_demo(telefono_usuario):
    """
    🆕 LA CÁMARA MÁGICA:
    Si estamos en el simulador, usa una foto profesional de respaldo
    para que el workflow no se rompa y el inversor vea su tarjeta iluminada.
    """
    try:
        print(f"\033[1;33m🎭 [DEMO_MODE] -> Activando Avatar Táctico para {telefono_usuario}...\033[0m")
        
        folder = "static/profiles"
        if not os.path.exists(folder): os.makedirs(folder)

        # Ruta donde queremos que quede la foto del socio
        destino = os.path.join(folder, f"{telefono_usuario}.jpg")
        
        # Ruta de nuestra foto de lujo (el logo del club sirve como avatar pro)
        origen = "static/logo_pasto.jpg" 

        if os.path.exists(origen):
            shutil.copy(origen, destino)
            print(f"\033[1;32m✨ [ÉXITO] Avatar asignado correctamente.\033[0m")
            return f"/static/profiles/{telefono_usuario}.jpg"
        else:
            print("⚠️ [ADVERTENCIA] No encontré 'logo_pasto.jpg' para usar como avatar.")
            return None
    except Exception as e:
        print(f"❌ Fallo al activar foto demo: {e}")
        return None

def codificar_imagen(path_imagen):
    """
    PREPARADOR VISUAL PARA IA
    """
    try:
        path_local = path_imagen.lstrip('/')
        if not os.path.exists(path_local): return None
        with open(path_local, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        return None
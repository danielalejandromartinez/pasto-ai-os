import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

def descargar_foto_perfil(media_id, telefono_usuario):
    """
    EL RECAUDADOR DE IMÁGENES:
    Conecta con Meta, descarga la selfie real y la guarda en el búnker local.
    """
    try:
        # 🎨 [LOG DE OBSERVABILIDAD] - Azul para el Fotógrafo
        print(f"\n\033[1;94m📸 [FOTÓGRAFO/MEDIA] -> Solicitando selfie real a Meta para: {telefono_usuario}\033[0m")

        if not WHATSAPP_TOKEN:
            print("❌ [ERROR] No hay WHATSAPP_TOKEN configurado en el .env")
            return None

        # 1. Obtener la URL de descarga desde los servidores de Meta
        # Usamos v21.0 que es la versión más estable actualmente
        url_info = f"https://graph.facebook.com/v21.0/{media_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        
        r_info = requests.get(url_info, headers=headers)
        if r_info.status_code != 200:
            print(f"❌ [ERROR META INFO]: {r_info.text}")
            return None
            
        url_imagen = r_info.json().get("url")
        
        if not url_imagen:
            print("❌ [ERROR] Meta no entregó una URL de descarga válida.")
            return None

        # 2. Descargar los bytes reales de la imagen
        print(f"⏳ [FOTÓGRAFO/MEDIA] -> Bajando archivos desde Meta...")
        r_img = requests.get(url_imagen, headers=headers)
        
        if r_img.status_code != 200:
            print(f"❌ [ERROR DOWNLOAD]: No se pudo descargar el contenido de la imagen.")
            return None

        # 3. Guardar en la carpeta física del servidor
        folder = "static/profiles"
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        filename = f"{telefono_usuario}.jpg"
        path_fisico = os.path.join(folder, filename)
        
        # Guardado atómico
        with open(path_fisico, "wb") as f:
            f.write(r_img.content)
            
        # Verificar que el archivo realmente se guardó y tiene tamaño
        if os.path.exists(path_fisico) and os.path.getsize(path_fisico) > 0:
            print(f"\033[1;92m✅ [ÉXITO] Selfie guardada físicamente: {path_fisico} ({os.path.getsize(path_fisico)} bytes)\033[0m")
            # Devolvemos la ruta WEB correcta para que el navegador la encuentre
            return f"/static/profiles/{filename}"
        else:
            print("❌ [ERROR] El archivo se creó vacío o no se guardó correctamente.")
            return None

    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Media Service falló: {e}")
        return None

def codificar_imagen(path_imagen):
    """
    PREPARADOR VISUAL:
    Convierte la imagen en código base64 para que el cerebro de gpt-4o pueda 'mirarla'.
    """
    try:
        # Limpieza de ruta: quitamos la barra inicial para que el SO la encuentre localmente
        path_local = path_imagen.lstrip('/')
        
        if not os.path.exists(path_local):
            print(f"❌ [ERROR] Archivo no localizado para la IA: {path_local}")
            return None

        with open(path_local, "rb") as image_file:
            # Codificamos a base64 (el idioma que habla la visión de la IA)
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    except Exception as e:
        print(f"❌ [ERROR] Fallo al codificar para Visión AI: {e}")
        return None
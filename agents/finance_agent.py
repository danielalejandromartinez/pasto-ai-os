import os
import json
from openai import OpenAI
import media_service

class FinanceAgent:
    def __init__(self):
        # Usamos la llave de entorno cargada en main.py
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def auditar_recibo(self, ruta_imagen, precio_esperado=65000):
        """
        Ojos de Auditor Forense: Extrae hasta el último detalle para el EFECTO WOW.
        Misión: Que Alejandro pueda decir exactamente qué vio en el papel.
        """
        if not os.path.exists(ruta_imagen):
            print(f"❌ [FINANCE] Archivo no encontrado: {ruta_imagen}")
            return {"status": "error", "mensaje": "Imagen no encontrada"}

        # Convertimos la imagen para que la IA la vea (Nervio óptico)
        base64_image = media_service.codificar_imagen(ruta_imagen)

        # Prompt Maestro para Auditoría Visual de Pasto.AI
        prompt_auditoria = f"""
        Eres el Auditor Financiero Senior de Pasto.AI. Tu misión es leer este recibo de pago 
        con precisión quirúrgica para generar un reporte que deje al cliente impresionado.

        REGLAS DE NEGOCIO (Para validación interna):
        - Monto oficial: {precio_esperado} COP.
        - Beneficiario oficial: Daniel Martinez o número 3152405542 o Ricardo Ormaza.
        - Fecha válida: Mes de febrero de 2026.

        TU MISIÓN:
        Extrae la información EXACTA del recibo. Si algo no está, pon "No visible".
        1. MONTO: Valor con símbolos.
        2. FECHA: Fecha y hora exacta si aparece.
        3. REFERENCIA: El número de comprobante o transacción.
        4. DESTINATARIO: Quién recibió el dinero.
        5. REMITENTE: Quién envió el dinero (Busca el nombre del cliente).

        Responde ÚNICAMENTE en este formato JSON para procesamiento agéntico:
        {{
            "analisis_visual": {{
                "monto": "ej: $65.000,00",
                "fecha": "ej: 20 de febrero de 2026 a las 02:30 PM",
                "referencia": "ej: 12154875",
                "destinatario": "ej: Ricardo Ormaza",
                "remitente": "ej: Daniel Martinez"
            }},
            "veredicto": {{
                "es_valido": true/false,
                "error_motivo": "monto_incorrecto / fecha_vieja / destinatario_erroneo / ninguno",
                "explicacion_detallada": "Escribe un resumen humano de lo que viste."
            }}
        }}
        """

        try:
            print(f"\033[93m[FINANCE/VISION] -> Alejandro está analizando el recibo de pago...\033[0m")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_auditoria},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }],
                response_format={ "type": "json_object" }
            )
            
            reporte = json.loads(response.choices[0].message.content)
            print(f"\033[92m[FINANCE/VISION] -> Auditoría completada con éxito.\033[0m")
            return reporte

        except Exception as e:
            print(f"❌ Error crítico en FinanceAgent: {e}")
            return None
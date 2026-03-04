from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        # Diccionario: { club_id: [lista_de_conexiones] }
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, club_id: int):
        await websocket.accept()
        if club_id not in self.active_connections:
            self.active_connections[club_id] = []
        self.active_connections[club_id].append(websocket)

    def disconnect(self, websocket: WebSocket, club_id: int):
        if club_id in self.active_connections:
            if websocket in self.active_connections[club_id]:
                self.active_connections[club_id].remove(websocket)

    # --- ESTA ES LA FUNCIÓN QUE FALTABA ---
    async def broadcast(self, message: str, club_id: int):
        """
        Envía un mensaje a todas las pantallas conectadas a un club específico.
        """
        if club_id in self.active_connections:
            # Iteramos sobre una copia de la lista para evitar errores si alguien se desconecta
            for connection in list(self.active_connections[club_id]):
                try:
                    await connection.send_text(message)
                except Exception:
                    # Si la conexión está muerta, la sacamos
                    self.disconnect(connection, club_id)

manager = ConnectionManager()
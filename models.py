from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON, Float, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# --- TABLA INTERMEDIA: JUGADORES Y CATEGORÍAS (Escalabilidad Many-to-Many) ---
player_categories = Table(
    "player_categories",
    Base.metadata,
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)

class Club(Base):
    __tablename__ = "clubs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    admin_phone = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    jackpot_balance = Column(Float, default=0.0) 
    settings = Column(JSON, default={"currency": "SQC", "timezone": "America/Bogota"})
    
    players = relationship("Player", back_populates="club")
    tournaments = relationship("Tournament", back_populates="club")
    agent_logs = relationship("AgentMemory", back_populates="club")
    system_tasks = relationship("TaskQueue", back_populates="club")
    seasons = relationship("Season", back_populates="club")
    
    # Conexión con el menú de ligas del club
    categories = relationship("Category", back_populates="club")

class Category(Base):
    """
    LA LLAVE DE LA FLEXIBILIDAD MUNDIAL:
    Configurable por cada club (Primera, Segunda, Damas, etc.)
    """
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) 
    club_id = Column(Integer, ForeignKey("clubs.id"))
    
    club = relationship("Club", back_populates="categories")
    players = relationship("Player", secondary=player_categories, back_populates="player_categories_list")

class WhatsAppUser(Base):
    __tablename__ = "whatsapp_users"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    memory = Column(JSON, default={"step": "idle"}) 
    is_admin = Column(Boolean, default=False)
    players = relationship("Player", back_populates="owner")

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    eternal_points = Column(Float, default=0.0) 
    
    # 🛡️ MEJORA DE ROBUSTEZ: Cambiamos 'rank' por 'prestige_rank' para evitar errores de Postgres
    prestige_rank = Column(String, default="BRONCE")
    
    achievements = Column(JSON, default={"stars": 0, "medals": 0, "badges": []})
    wallet_balance = Column(Float, default=0.0)
    elo = Column(Integer, default=1000)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    status_tags = Column(JSON, default={}) 
    tournament_registered = Column(Boolean, default=False) 
    
    category = Column(String, default="General") 
    avatar_url = Column(String, nullable=True)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    
    club_id = Column(Integer, ForeignKey("clubs.id"))
    club = relationship("Club", back_populates="players")
    owner_id = Column(Integer, ForeignKey("whatsapp_users.id"))
    owner = relationship("WhatsAppUser", back_populates="players")
    point_history = relationship("PointTransaction", back_populates="player")
    
    # Relación con sus categorías asignadas
    player_categories_list = relationship("Category", secondary=player_categories, back_populates="players")

    def actualizar_prestigio(self):
        """
        Lógica automática de ascenso de rango
        """
        xp = self.eternal_points
        if xp <= 500: self.prestige_rank = "BRONCE"
        elif xp <= 1500: self.prestige_rank = "PLATA"
        elif xp <= 3000: self.prestige_rank = "ORO"
        else: self.prestige_rank = "LEYENDA"

class Season(Base):
    __tablename__ = "seasons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) 
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    club = relationship("Club", back_populates="seasons")

class PointTransaction(Base):
    __tablename__ = "point_transactions"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    points_earned = Column(Float) 
    match_type = Column(String) 
    category_at_moment = Column(String) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    player = relationship("Player", back_populates="point_history")

class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(String, default="inscription") 
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = Column(String, default="General")
    config_json = Column(JSON, default={"min_matches": 15})
    club_id = Column(Integer, ForeignKey("clubs.id"))
    club = relationship("Club", back_populates="tournaments")
    matches = relationship("Match", back_populates="tournament")

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    player_1_id = Column(Integer, ForeignKey("players.id"))
    player_2_id = Column(Integer, ForeignKey("players.id"))
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    score = Column(String, nullable=True) 
    parciales = Column(String, nullable=True) 
    match_type = Column(String, default="challenge") 
    status = Column(String, default="proposed") 
    is_finished = Column(Boolean, default=False)
    scheduled_time = Column(DateTime, nullable=True)
    stake = Column(Float, default=50.0) 

    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=True)
    tournament = relationship("Tournament", back_populates="matches")
    player_1 = relationship("Player", foreign_keys=[player_1_id])
    player_2 = relationship("Player", foreign_keys=[player_2_id])

class TaskQueue(Base):
    __tablename__ = "task_queue"
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    task_type = Column(String) 
    target_id = Column(Integer) 
    scheduled_for = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    club = relationship("Club", back_populates="system_tasks")

class AgentMemory(Base):
    __tablename__ = "agent_memory"
    id = Column(Integer, primary_key=True, index=True)
    accion = Column(String, index=True)
    telefono = Column(String, index=True)
    exito = Column(Boolean, default=True)
    razon = Column(String, nullable=True) 
    club_id = Column(Integer, ForeignKey("clubs.id"))
    club = relationship("Club", back_populates="agent_logs")
    timestamp = Column(DateTime, default=datetime.utcnow)

class MessageHistory(Base):
    __tablename__ = "message_history"
    id = Column(Integer, primary_key=True, index=True)
    whatsapp_msg_id = Column(String, unique=True, index=True, nullable=True)
    phone_number = Column(String, index=True)
    role = Column(String) 
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class WhiteList(Base):
    __tablename__ = "whitelist"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    full_name = Column(String)
    club_id = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
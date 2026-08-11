from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON, Float, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# --- TABLA INTERMEDIA: JUGADORES Y CATEGORÍAS ---
player_categories = Table(
    "player_categories",
    Base.metadata,
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    cities = relationship("City", back_populates="country")

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"))
    country = relationship("Country", back_populates="cities")
    clubs = relationship("Club", back_populates="city")

class Club(Base):
    __tablename__ = "clubs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    admin_phone = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)
    city = relationship("City", back_populates="clubs")
    
    # Configuración única para Padel (Autogestionable por el club)
    settings = Column(JSON, default={
        "currency": "COP", 
        "timezone": "America/Bogota",
        "primary_color": "#00f2ff",
        "logo_url": "/static/logo_pasto.jpg",
        "booking": {"enabled": True, "courts_count": 6, "slot_minutes": 90} 
    })
    
    players = relationship("Player", back_populates="club")
    tournaments = relationship("Tournament", back_populates="club")
    categories = relationship("Category", back_populates="club")
    matches = relationship("Match", back_populates="club")

class Category(Base):
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
    memory = Column(JSON, default={"step": "idle"}) 
    players = relationship("Player", back_populates="owner")

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    # 🛡️ MOTOR DE IDENTIDAD TOH (PWA LOGIN)
    username = Column(String, unique=True, index=True, nullable=True) # Nombre de usuario único
    pin_code = Column(String, nullable=True) # PIN de 4 dígitos para login rápido
    
    # 🏆 SISTEMA DE PUNTOS Y GAMIFICACIÓN (NUEVO)
    eternal_points = Column(Float, default=0.0) # Histórico (XP Eterno)
    season_points = Column(Float, default=0.0)  # Puntos de Temporada (Se borra en Junio/Diciembre)
    monthly_points = Column(Float, default=0.0) # Puntos del Mes (Se borra a fin de mes)
    
    stars = Column(Integer, default=0) # 🌟 Campeón de Temporada (Eternas)
    medals = Column(Integer, default=0) # 🏅 Campeón del Mes (Temporales, se borran a fin de temporada)
    
    prestige_rank = Column(String, default="BRONCE")
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    avatar_url = Column(String, nullable=True)
    
    # 🛡️ FILTRO DE ADMISIÓN (SaaS Security)
    is_approved = Column(Boolean, default=False)
    
    club_id = Column(Integer, ForeignKey("clubs.id"))
    club = relationship("Club", back_populates="players")
    owner_id = Column(Integer, ForeignKey("whatsapp_users.id"))
    owner = relationship("WhatsAppUser", back_populates="players")
    point_history = relationship("PointTransaction", back_populates="player")
    player_categories_list = relationship("Category", secondary=player_categories, back_populates="players")

    def actualizar_prestigio(self):
        xp = self.eternal_points
        if xp <= 500: self.prestige_rank = "BRONCE"
        elif xp <= 1500: self.prestige_rank = "PLATA"
        else: self.prestige_rank = "ORO"

class PointTransaction(Base):
    __tablename__ = "point_transactions"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    points_earned = Column(Float) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    player = relationship("Player", back_populates="point_history")

class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    club = relationship("Club", back_populates="tournaments")
    matches = relationship("Match", back_populates="tournament")

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    club = relationship("Club", back_populates="matches")
    
    # Jugadores para Padel (Parejas)
    player_1_id = Column(Integer, ForeignKey("players.id"))
    player_2_id = Column(Integer, ForeignKey("players.id"), nullable=True) # Pareja de P1
    player_3_id = Column(Integer, ForeignKey("players.id")) # Rival 1
    player_4_id = Column(Integer, ForeignKey("players.id"), nullable=True) # Rival 2
    
    score = Column(String, nullable=True) 
    is_finished = Column(Boolean, default=False)
    
    # 🤝 INTERRUPTOR DE CONFIRMACIÓN (HANDSHAKE)
    is_confirmed = Column(Boolean, default=False)
    
    scheduled_time = Column(DateTime, nullable=True)
    
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=True)
    tournament = relationship("Tournament", back_populates="matches")

    # Declaración de relaciones explícitas para SQLite
    player_1 = relationship("Player", foreign_keys=[player_1_id])
    player_2 = relationship("Player", foreign_keys=[player_2_id])
    p3 = relationship("Player", foreign_keys=[player_3_id])
    p4 = relationship("Player", foreign_keys=[player_4_id])

class MessageHistory(Base):
    __tablename__ = "message_history"
    id = Column(Integer, primary_key=True, index=True)
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
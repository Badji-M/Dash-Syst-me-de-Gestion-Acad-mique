"""
database/models.py — Modèles SQLAlchemy du SGA
Définit toutes les entités et leurs relations.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    ForeignKey, Text, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : Students
# ─────────────────────────────────────────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    last_name     = Column(String(100), nullable=False)
    first_name    = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, nullable=False)
    birth_date    = Column(Date, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    is_active     = Column(Boolean, default=True)

    # Relations
    grades        = relationship("Grade",      back_populates="student", cascade="all, delete-orphan")
    attendances   = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Student {self.id}: {self.full_name}>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : Courses
# ─────────────────────────────────────────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    code            = Column(String(20), unique=True, nullable=False)   # ex: MATH101
    label           = Column(String(200), nullable=False)
    total_hours     = Column(Float, nullable=False, default=0.0)        # Volume horaire total prévu
    teacher         = Column(String(150), nullable=True)
    description     = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    is_active       = Column(Boolean, default=True)

    # Relations
    sessions        = relationship("Session", back_populates="course", cascade="all, delete-orphan")
    grades          = relationship("Grade",   back_populates="course", cascade="all, delete-orphan")

    @property
    def completed_hours(self):
        """Somme des durées des séances effectuées."""
        try:
            return sum(s.duration for s in self.sessions if s.duration)
        except Exception:
            return 0

    @property
    def progress_percent(self):
        """Pourcentage d'avancement par rapport au volume horaire total."""
        try:
            if not self.total_hours or self.total_hours == 0:
                return 0
            return round(min((self.completed_hours / self.total_hours) * 100, 100), 1)
        except Exception:
            return 0

    def __repr__(self):
        return f"<Course {self.code}: {self.label}>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : Sessions (séances de cours)
# ─────────────────────────────────────────────────────────────────────────────
class Session(Base):
    __tablename__ = "sessions"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    course_id   = Column(Integer, ForeignKey("courses.id"), nullable=False)
    date        = Column(Date, nullable=False)
    duration    = Column(Float, nullable=False, default=1.0)            # Durée en heures
    topic       = Column(String(300), nullable=True)                    # Thème abordé
    notes       = Column(Text, nullable=True)                           # Notes pédagogiques
    created_at  = Column(DateTime, default=datetime.utcnow)

    # Relations
    course      = relationship("Course",     back_populates="sessions")
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session {self.id}: Course {self.course_id} — {self.date}>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : Attendance (table de liaison Sessions ↔ Students — absences)
# ─────────────────────────────────────────────────────────────────────────────
class Attendance(Base):
    __tablename__ = "attendance"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    session_id  = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id  = Column(Integer, ForeignKey("students.id"), nullable=False)
    is_absent   = Column(Boolean, default=False)                        # True = absent
    is_excused  = Column(Boolean, default=False)                        # True = absence justifiée
    comment     = Column(String(300), nullable=True)

    # Contrainte d'unicité : un seul enregistrement par (session, étudiant)
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance"),
    )

    # Relations
    session     = relationship("Session", back_populates="attendances")
    student     = relationship("Student", back_populates="attendances")

    def __repr__(self):
        status = "ABSENT" if self.is_absent else "PRESENT"
        return f"<Attendance Session {self.session_id} / Student {self.student_id}: {status}>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : Grades (notes)
# ─────────────────────────────────────────────────────────────────────────────
class Grade(Base):
    __tablename__ = "grades"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    student_id  = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id   = Column(Integer, ForeignKey("courses.id"),  nullable=False)
    grade       = Column(Float, nullable=False)                         # Note /20
    coefficient = Column(Float, nullable=False, default=1.0)
    label       = Column(String(200), nullable=True)                    # ex: "Contrôle 1"
    date        = Column(Date, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    # Contrainte : un seul enregistrement par (student, course, label)
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "label", name="uq_grade"),
    )

    # Relations
    student     = relationship("Student", back_populates="grades")
    course      = relationship("Course",  back_populates="grades")

    def __repr__(self):
        return f"<Grade Student {self.student_id} / Course {self.course_id}: {self.grade}/20>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE : Users (authentification)
# ─────────────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(80),  unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role          = Column(String(50),  nullable=False, default="viewer")  # admin / teacher / viewer
    full_name     = Column(String(200), nullable=True)
    email         = Column(String(150), unique=True, nullable=True)
    is_active     = Column(Boolean, default=True)
    last_login    = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

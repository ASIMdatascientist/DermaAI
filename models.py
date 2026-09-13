from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base


class Patient(Base):

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    age = Column(Integer, nullable=False)

    gender = Column(String, nullable=False)

    contact = Column(String, nullable=True)

    # -----------------------------
    # Prediction result (saved after /predict runs)
    # -----------------------------

    predicted_disease = Column(String, nullable=True)

    confidence = Column(Float, nullable=True)

    # -----------------------------
    # Timestamp
    # -----------------------------

    created_at = Column(DateTime(timezone=True), server_default=func.now())
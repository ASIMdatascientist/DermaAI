from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

import tensorflow as tf
from PIL import Image
import numpy as np
import io

from database import engine, Base, get_db
import models

# Gemini / CrewAI
from crew import get_skin_explanation, chat_with_gemini


# =========================================
# REQUEST SCHEMA FOR /chat
# =========================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    disease: str
    confidence: float
    history: list[ChatMessage] = []
    message: str


# =========================================
# FASTAPI APP
# =========================================

app = FastAPI()

Base.metadata.create_all(bind=engine)


# =========================================
# CORS
# =========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================
# LOAD MODEL ONCE
# =========================================

model = tf.keras.models.load_model("model.h5")


# =========================================
# CLASS NAMES
# =========================================

CLASS_NAMES = [
    "Acne",
    "Eczema",
    "Vitiligo"
]


# =========================================
# STATIC FOLDER
# =========================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# =========================================
# HOME PAGE
# =========================================

@app.get("/")
def home():

    return FileResponse(
        "static/index.html"
    )


# =========================================
# PREDICTION / UPLOAD API
# =========================================

@app.post("/predict")
async def predict(
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    contact: str = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    try:

        # =================================
        # READ IMAGE
        # =================================

        contents = await image.read()

        img = Image.open(
            io.BytesIO(contents)
        ).convert("RGB")


        # =================================
        # RESIZE IMAGE
        # =================================

        img = img.resize(
            (224, 224)
        )


        # =================================
        # CONVERT TO NUMPY
        # =================================

        img_array = np.array(img)


        # =================================
        # NORMALIZE
        # =================================

        img_array = img_array / 255.0


        # =================================
        # ADD BATCH DIMENSION
        # =================================

        img_array = np.expand_dims(
            img_array,
            axis=0
        )


        # =================================
        # MODEL PREDICTION
        # =================================

        predictions = model.predict(
            img_array,
            verbose=0
        )


        # =================================
        # FIND PREDICTED CLASS
        # =================================

        predicted_index = np.argmax(
            predictions[0]
        )


        # =================================
        # DISEASE NAME
        # =================================

        predicted_class = CLASS_NAMES[
            predicted_index
        ]


        # =================================
        # CONFIDENCE
        # =================================

        confidence = (
            float(
                predictions[0][predicted_index]
            ) * 100
        )


        # =================================
        # SAVE TO DATABASE
        # =================================

        new_patient = models.Patient(
            name=name,
            age=age,
            gender=gender,
            contact=contact,
            predicted_disease=predicted_class,
            confidence=confidence
        )

        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)


        # =================================
        # GEMINI EXPLANATION (async - must
        # be awaited since it now runs
        # crew.kickoff_async() internally)
        # =================================

        explanation = await get_skin_explanation(
            predicted_class,
            confidence
        )


        # =================================
        # RETURN RESULT
        # =================================

        return {

            "id": new_patient.id,

            "prediction": predicted_class,

            "confidence": f"{confidence:.2f}%",

            "explanation": explanation

        }


    except Exception as e:

        return {
            "detail": str(e)
        }


# =========================================
# CHAT WITH GEMINI ABOUT THE PREDICTION
# =========================================

@app.post("/chat")
async def chat(payload: ChatRequest):

    try:

        reply = await chat_with_gemini(
            payload.disease,
            payload.confidence,
            [turn.dict() for turn in payload.history],
            payload.message
        )

        return {
            "reply": reply
        }

    except Exception as e:

        return {
            "detail": str(e)
        }


# =========================================
# LIST ALL SAVED RECORDS
# =========================================

@app.get("/patients")
def get_patients(
    db: Session = Depends(get_db)
):

    return db.query(
        models.Patient
    ).all()
# DermaAI - Skin Disease Classification Website

## Files
- index.html
- style.css
- script.js
- images/acne.jpeg
- images/eczema.jpeg
- images/vitiligo.jpeg

## Run the frontend
You can open index.html in a browser for the UI preview.

For the real prediction, use a backend server (Flask/FastAPI) and expose:

POST /predict

Form field:
image

Example JSON response:
{
  "prediction": "Acne",
  "confidence": 0.94
}

## Important
The three disease names in the UI are currently:
1. Acne
2. Eczema
3. Vitiligo

Verify these names against the exact class labels used by your trained model. The supplied images are used as examples in the website.

The website is an educational/demo interface and is not a medical diagnostic tool.

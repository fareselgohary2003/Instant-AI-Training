from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO
from PIL import Image
import io
import os

app = FastAPI(title='RoadVision AI')
app.mount('/static', StaticFiles(directory='static'), name='static')

MODEL_PATH = 'best.pt'
model = YOLO(MODEL_PATH)

@app.get('/')
def index():
    return {'message': 'RoadVision AI backend is running.'}

@app.post('/predict')
async def predict(file: UploadFile = File(...), confidence: float = Form(5.0)):
    if not file.filename:
        return JSONResponse({'success': False, 'detail': 'No file selected'}, status_code=400)

    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')

    results = model(img_bytes.getvalue(), conf=confidence/100, verbose=False)
    detections = []

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = result.names.get(cls, str(cls))
            detections.append({
                'class_name': label,
                'confidence': conf,
                'bbox_xyxy': [x1, y1, x2, y2]
            })

    return {'success': True, 'detections': detections, 'confidence': confidence}

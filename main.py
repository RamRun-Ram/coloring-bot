from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import logging
from typing import Optional
import hashlib
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Coloring Book Processor")

# CORS для n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageProcessor:
    @staticmethod
    def add_watermark(image: np.ndarray, text: str = "@cat") -> np.ndarray:
        """Добавляет водяной знак на изображение"""
        h, w = image.shape[:2]
        # Создаем PIL изображение для текста
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)
        
        # Размер шрифта пропорционален размеру изображения
        font_size = max(20, min(w, h) // 30)
        
        try:
            # Попытка использовать системный шрифт
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            # Fallback на дефолтный шрифт
            font = ImageFont.load_default()
        
        # Позиция водяного знака (правый нижний угол)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = w - text_width - 20
        y = h - text_height - 20
        
        # Добавляем полупрозрачный фон
        draw.rectangle(
            [(x-10, y-5), (x + text_width + 10, y + text_height + 5)],
            fill=(255, 255, 255, 200)
        )
        
        # Добавляем текст
        draw.text((x, y), text, fill=(150, 150, 150), font=font)
        
        return np.array(pil_image)
    
    @staticmethod
    def process_simple(image_bytes: bytes) -> np.ndarray:
        """Простая раскраска - меньше деталей, толще линии"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Уменьшаем размер для упрощения
        height, width = img.shape[:2]
        if width > 800:
            scale = 800 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
        
        # Преобразуем в оттенки серого
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Сильное размытие для удаления деталей
        gray = cv2.medianBlur(gray, 7)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Адаптивный порог с большими блоками
        edges = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,
            C=12
        )
        
        # Утолщаем линии
        kernel = np.ones((3,3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        # Инвертируем
        edges = cv2.bitwise_not(edges)
        
        return edges
    
    @staticmethod
    def process_detailed(image_bytes: bytes) -> np.ndarray:
        """Детальная раскраска - больше деталей, тонкие линии"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Сохраняем больший размер для деталей
        height, width = img.shape[:2]
        if width > 1200:
            scale = 1200 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
        
        # Преобразуем в оттенки серого
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Легкое размытие
        gray = cv2.medianBlur(gray, 3)
        
        # Детектор краев Canny для лучших деталей
        edges1 = cv2.Canny(gray, 50, 150)
        
        # Адаптивный порог для дополнительных деталей
        edges2 = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=7,
            C=5
        )
        
        # Комбинируем оба метода
        edges = cv2.bitwise_and(edges1, edges2)
        
        # Минимальная морфология
        kernel = np.ones((2,2), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Инвертируем
        edges = cv2.bitwise_not(edges)
        
        return edges
    
    @staticmethod
    def process_cartoon(image_bytes: bytes) -> np.ndarray:
        """Мультяшный стиль - средний уровень деталей"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Оптимальный размер
        height, width = img.shape[:2]
        if width > 1000:
            scale = 1000 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
        
        # Bilateral filter для сохранения краев
        smooth = cv2.bilateralFilter(img, 15, 80, 80)
        
        # Преобразуем в оттенки серого
        gray = cv2.cvtColor(smooth, cv2.COLOR_BGR2GRAY)
        
        # Медианное размытие
        gray = cv2.medianBlur(gray, 5)
        
        # Адаптивный порог
        edges = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            blockSize=9,
            C=8
        )
        
        # Средняя морфология
        kernel = np.ones((2,2), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Инвертируем
        edges = cv2.bitwise_not(edges)
        
        return edges

processor = ImageProcessor()

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Coloring Book Processor",
        "version": "2.0",
        "endpoints": ["/process", "/process-base64"],
        "styles": ["simple", "detailed", "cartoon"]
    }

@app.post("/process")
async def process_image(
    file: UploadFile = File(...),
    style: str = "cartoon",
    watermark: bool = True
):
    """Обработка изображения с выбором стиля"""
    try:
        logger.info(f"Processing image with style: {style}")
        
        # Проверяем размер файла (макс 10MB)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Выбираем метод обработки
        if style == "simple":
            result = processor.process_simple(contents)
        elif style == "detailed":
            result = processor.process_detailed(contents)
        else:
            result = processor.process_cartoon(contents)
        
        # Добавляем водяной знак если нужно
        if watermark:
            result = processor.add_watermark(result)
        
        # Конвертируем в PNG
        _, buffer = cv2.imencode('.png', result)
        io_buf = io.BytesIO(buffer)
        
        return StreamingResponse(
            io_buf,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=coloring_{style}.png",
                "X-Processing-Style": style
            }
        )
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-base64")
async def process_image_base64(data: dict):
    """Обработка base64 изображения"""
    try:
        image_data = base64.b64decode(data["image"])
        style = data.get("style", "cartoon")
        watermark = data.get("watermark", True)
        
        # Выбираем метод обработки
        if style == "simple":
            result = processor.process_simple(image_data)
        elif style == "detailed":
            result = processor.process_detailed(image_data)
        else:
            result = processor.process_cartoon(image_data)
        
        # Добавляем водяной знак
        if watermark:
            result = processor.add_watermark(result)
        
        # Кодируем результат
        _, buffer = cv2.imencode('.png', result)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "image": encoded_image,
            "style": style,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing base64: {str(e)}")
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

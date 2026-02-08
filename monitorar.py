import cv2 
import requests 
import numpy as np 
import os 
import time 
import base64 
from io import BytesIO 
from PIL import Image
from datetime import datetime 
from roboflow import Roboflow 

# --- CONFIGURAÇÕES ---
API_KEY = "n1oHzk5lt38xT2nDjhog"
PROJECT_ID = "water-detection-log4w-dcamk"
URL_CAPTURE = "http://10.190.87.217/capture"  # URL da ESP32-CAM
PASTA = r"C:\monitoramento_rio"
INTERVALO = 180 

os.makedirs(PASTA, exist_ok=True)

# --- INICIALIZAÇÃO IA ---
rf = Roboflow(api_key=API_KEY)
project = rf.workspace().project(PROJECT_ID)
model = project.version(2).model

def decode_mask(mask_base64):
    """Converte Base64 para matriz NumPy para segmentação semântica"""
    mask_bytes = base64.b64decode(mask_base64)
    mask_image = Image.open(BytesIO(mask_bytes))
    return np.array(mask_image)

nivel_anterior = None

while True:
    try:
        agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"\n[{agora}] Capturando...")

        # 1. Captura da ESP32
        resp = requests.get(URL_CAPTURE, timeout=35)
        resp.raise_for_status()
        img_np = np.frombuffer(resp.content, dtype=np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        if frame is not None:
            caminho_img = os.path.join(PASTA, f"{agora}.jpg")
            cv2.imwrite(caminho_img, frame)

            # 2. IA e Decodificação da Máscara
            results = model.predict(caminho_img)
            json_data = results.json()
            
    
            mask_base64 = json_data["predictions"][0]["segmentation_mask"]
            mask_array = decode_mask(mask_base64)

            # 3. Cálculo de Nível (Classes 1: River e 2: Water)
            pixels_agua = np.sum((mask_array == 1) | (mask_array == 2))
            nivel_atual = (pixels_agua / mask_array.size) * 100

            # 4. Lógica de Enchimento
            status = "ESTÁVEL"
            if nivel_anterior is not None:
                diff = nivel_atual - nivel_anterior
                if diff > 0.5: status = "ENCHENDO"
                elif diff < -0.5: status = "BAIXANDO"
            
            print(f"🌊 Nível: {nivel_atual:.2f}% | Status: {status}")
            
            # 5. Salva Máscara Visual
            vis_mask = np.where((mask_array == 1) | (mask_array == 2), 255, 0).astype(np.uint8)
            cv2.imwrite(os.path.join(PASTA, f"{agora}_MASK_{status}.png"), vis_mask)
            
            nivel_anterior = nivel_atual
            
    except Exception as e:
        print(f"❌ Erro: {e}")

    time.sleep(INTERVALO)
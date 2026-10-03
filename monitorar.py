import cv2 
import requests 
import numpy as np 
import os 
import time 
import base64 
import logging
from io import BytesIO 
from PIL import Image
from datetime import datetime 
from roboflow import Roboflow 

#CONFIGURAÇÕES 
API_KEY = ""
PROJECT_ID = ""
URL_CAPTURE = " "
PASTA = "monitoramento_rio" 
INTERVALO = 180 

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitoramento.log"),
        logging.StreamHandler()
    ]
)

# Cria a pasta se não existir
if not os.path.exists(PASTA):
    os.makedirs(PASTA)
    logging.info(f"Pasta {PASTA} criada.")

#  INICIALIZAÇÃO IA 
try:
    rf = Roboflow(api_key=API_KEY)
    project = rf.workspace().project(PROJECT_ID)
    model = project.version(2).model
    logging.info("Modelo Roboflow carregado com sucesso.")
except Exception as e:
    logging.error(f"Erro ao carregar modelo Roboflow: {e}")

def decode_mask(mask_base64):
    """Converte Base64 para matriz NumPy para segmentação semântica"""
    mask_bytes = base64.b64decode(mask_base64)
    mask_image = Image.open(BytesIO(mask_bytes))
    return np.array(mask_image)

nivel_anterior = None

while True:
    try:
        agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Iniciando ciclo de captura: {agora}")

        # Captura da ESP32
        resp = requests.get(URL_CAPTURE, timeout=35)
        resp.raise_for_status()
        img_np = np.frombuffer(resp.content, dtype=np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        if frame is None:
            logging.error("Falha ao decodificar imagem da ESP32.")
            continue

        # Salva a imagem original
        caminho_img = os.path.join(PASTA, f"{agora}.jpg")
        cv2.imwrite(caminho_img, frame)
        logging.info(f"Imagem original salva: {caminho_img}")

        # IA e Predição
        results = model.predict(caminho_img)
        json_data = results.json()
        
        # Verifica se há detecções
        if "predictions" in json_data and len(json_data["predictions"]) > 0:
            # Pega a primeira predição de segmentação
            prediction = json_data["predictions"][0]
            
            if "segmentation_mask" in prediction:
                mask_base64 = prediction["segmentation_mask"]
                mask_array = decode_mask(mask_base64)

                #  Cálculo de Nível (Classes 1: River e 2: Water)
                pixels_agua = np.sum((mask_array == 1) | (mask_array == 2))
                nivel_atual = (pixels_agua / mask_array.size) * 100

                #  Lógica de Enchimento
                status = "ESTÁVEL"
                if nivel_anterior is not None:
                    diff = nivel_atual - nivel_anterior
                    if diff > 0.5: status = "ENCHENDO"
                    elif diff < -0.5: status = "BAIXANDO"
                
                logging.info(f"Nível: {nivel_atual:.2f}% | Status: {status}")
                
                #  Salva Máscara Visual
                # Cria imagem preta e branca (255 onde é água, 0 onde não é)
                vis_mask = np.where((mask_array == 1) | (mask_array == 2), 255, 0).astype(np.uint8)
                caminho_mask = os.path.join(PASTA, f"{agora}_MASK_{status}.png")
                cv2.imwrite(caminho_mask, vis_mask)
                logging.info(f"Máscara salva: {caminho_mask}")
                
                nivel_anterior = nivel_atual
            else:
                logging.warning("Predição feita, mas nenhuma máscara de segmentação encontrada.")
        else:
            logging.warning("A IA não detectou rio nesta imagem.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de conexão com a ESP32: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}", exc_info=True)

    logging.info(f"Aguardando {INTERVALO} segundos para a próxima captura")
    time.sleep(INTERVALO)

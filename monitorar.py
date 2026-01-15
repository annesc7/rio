import cv2
import requests
import numpy as np
import time
import os
from datetime import datetime
from roboflow import Roboflow

# --- CONFIGURAÇÕES ---
API_KEY = "n1oHzk5lt38xT2nDjhog"
PROJECT_ID = "water-detection-log4w-dcamk"
URL_BASE = "http://10.80.17.217"
URL_CAPTURE = f"{URL_BASE}/capture"
INTERVALO = 180 

if not os.path.exists('monitoramento_rio'):
    os.makedirs('monitoramento_rio')

try:
    print("Conectando ao Roboflow...")
    rf = Roboflow(api_key=API_KEY)
    project = rf.workspace().project(PROJECT_ID)
    model = project.version(2).model
    print("Sistema pronto. Salvamento triplo ativado.")
except Exception as e:
    print(f" Erro ao carregar IA: {e}")
    exit()

while True:
    try:
        agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"\n[{agora}] Solicitando captura...")

        # 1. Captura a imagem da ESP32
        resp = requests.get(URL_CAPTURE, timeout=20)
        if resp.status_code == 200:
            img_np = np.frombuffer(resp.content, dtype=np.uint8)
            frame_original = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
        else:
            print(f"Falha na conexão com a ESP32: {resp.status_code}")
            frame_original = None

        if isinstance(frame_original, np.ndarray):
            # 2. IA processa a imagem
            results = model.predict(frame_original, confidence=5)
            predictions = results[0].json().get('predictions', [])
            
            # 3. SALVAR IMAGEM NORMAL (Para auditoria)
            nome_normal = f"monitoramento_rio/{agora}_1_ORIGINAL.jpg"
            cv2.imwrite(nome_normal, frame_original)

            # 4. Criar a MÁSCARA BINÁRIA (Preto e Branco)
            mascara_ia = np.zeros(frame_original.shape[:2], dtype=np.uint8)
            
            if len(predictions) > 0:
                for pred in predictions:
                    if 'points' in pred:
                        pontos = np.array([[p['x'], p['y']] for p in pred['points']], dtype=np.int32)
                        cv2.fillPoly(mascara_ia, [pontos], 255)
                
                # Salva a máscara P&B isolada
                cv2.imwrite(f"monitoramento_rio/{agora}_2_MASK_PB.jpg", mascara_ia)
                
                # 5. Salva a imagem com o OVERLAY COLORIDO da IA
                frame_overlay = results[0].plot()
                cv2.imwrite(f"monitoramento_rio/{agora}_3_IA_VISUAL.jpg", frame_overlay)
                
                print(f" Sucesso: Rio detectado. Arquivos salvos.")
            else:
                # Se a IA falhou, salvamos apenas a máscara preta para registro
                cv2.imwrite(f"monitoramento_rio/{agora}_2_IA_FALHOU_MASK.jpg", mascara_ia)
                print(f"! IA FALHOU: Verifique a foto '{agora}_1_ORIGINAL.jpg' para ver o motivo.")

        time.sleep(INTERVALO)

    except Exception as e:
        print(f"✗ Erro no ciclo: {str(e)}")
        time.sleep(10)
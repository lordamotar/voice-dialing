import os
import urllib.request
import zipfile
import shutil

URL = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
ZIP_PATH = "vosk-model-small-ru-0.22.zip"
DEST_DIR = "models"
EXTRACTED_DIR = os.path.join(DEST_DIR, "vosk-model-small-ru-0.22")

def download_and_extract():
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        
    if os.path.exists(EXTRACTED_DIR):
        print(f"[ИНФО] Модель уже существует в папке {EXTRACTED_DIR}")
        return

    print(f"[ИНФО] Скачивание модели с {URL}...")
    try:
        # Simple progress block
        def reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                s = "\r[ПРОГРЕСС] %5.1f%% (%d B)" % (percent, totalsize)
                print(s, end="", flush=True)
            else:
                print(f"\r[ПРОГРЕСС] Прочитано {readsofar} байт", end="", flush=True)

        urllib.request.urlretrieve(URL, ZIP_PATH, reporthook)
        print("\n[ИНФО] Скачивание завершено. Распаковка...")
        
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(DEST_DIR)
            
        print(f"[ИНФО] Модель успешно распакована в {EXTRACTED_DIR}")
    except Exception as e:
        print(f"\n[ОШИБКА] Произошла ошибка при скачивании или распаковке: {e}")
    finally:
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)

if __name__ == "__main__":
    download_and_extract()

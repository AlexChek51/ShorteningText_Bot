from pathlib import Path

# Определение корневой директории проекта
BASE_DIR = Path(__file__).resolve().parent

# Определение директории для загрузки файлов
UPLOAD_DIR = BASE_DIR / 'result'
UPLOAD_DIR.mkdir(exist_ok=True)  # Создаем директорию, если она не существует

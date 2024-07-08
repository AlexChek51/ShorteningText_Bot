import os
from fpdf import FPDF
from settings import UPLOAD_DIR, BASE_DIR

# Функция для получения списка файлов в директории с книгами
def get_books_list():
    books = []
    for file_name in os.listdir(UPLOAD_DIR):
        if file_name.endswith('.pdf'):
            books.append(file_name)
    return books

def save_to_pdf(text, save_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_font("Sans", style="", fname=BASE_DIR / "NotoSans-Regular.ttf", uni=True) #fname=BASE_DIR / "NotoSans-Regular.ttf" #fname="C:/NotoSans-Regular.ttf"
    pdf.set_font("Sans", size=12)

    # Текст для сохранения
    pdf.multi_cell(0, 10, text)

    # Сохранение PDF
    pdf.output(save_path)
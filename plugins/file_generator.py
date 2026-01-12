from aiogram.types import Message, BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from PIL import Image, ImageDraw, ImageFont
import io
import logging
import re
import zipfile
import json
import tempfile
import os
from messages import MENU_MSG, get_back_menu, get_main_menu

logger = logging.getLogger(__name__)

# Константы
MAX_IMAGE_SIZE = 5000
SUPPORTED_FORMATS = {
    'images': ['jpg', 'jpeg', 'png', 'gif', 'ico', 'bmp'],
    'text': ['txt', 'css', 'html', 'js', 'json'],
    'office': ['docx', 'xlsx'],
    'archives': ['zip', 'rar'],
    'video': ['mp4', 'avi'],
    'other': ['pdf', 'svg']
}
DEFAULT_COLOR = (255, 255, 255)  # Белый
TEXT_COLOR = (0, 0, 0)  # Черный

class FileGeneratorStates(StatesGroup):
    waiting_for_format = State()
    waiting_for_params = State()
    waiting_for_choice = State()

async def generate_file_command(message: Message, state: FSMContext):
    await state.set_state(FileGeneratorStates.waiting_for_format)
    
    format_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="JPG"), KeyboardButton(text="PNG"), KeyboardButton(text="GIF")],
            [KeyboardButton(text="ICO"), KeyboardButton(text="BMP"), KeyboardButton(text="SVG")],
            [KeyboardButton(text="TXT"), KeyboardButton(text="CSS"), KeyboardButton(text="HTML")],
            [KeyboardButton(text="JS"), KeyboardButton(text="JSON"), KeyboardButton(text="PDF")],
            [KeyboardButton(text="DOCX"), KeyboardButton(text="XLSX"), KeyboardButton(text="ZIP")],
            [KeyboardButton(text="RAR"), KeyboardButton(text="MP4"), KeyboardButton(text="AVI")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "🗂 Выбери формат файла для создания 👇",
        reply_markup=format_keyboard
    )

async def process_format_choice(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, выбери формат из предложенных вариантов")
        return
        
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
      
    format_map = {
        "JPG": "jpg", "JPEG": "jpg",
        "PNG": "png",
        "GIF": "gif",
        "ICO": "ico",
        "BMP": "bmp",
        "SVG": "svg",
        "TXT": "txt",
        "CSS": "css",
        "HTML": "html",
        "JS": "js",
        "JSON": "json",
        "PDF": "pdf",
        "DOCX": "docx",
        "XLSX": "xlsx",
        "ZIP": "zip",
        "RAR": "rar",
        "MP4": "mp4",
        "AVI": "avi"
    }
    
    if message.text not in format_map:
        await message.answer("ℹ️ Выбери формат из предложенных вариантов")
        return
    
    selected_format = format_map[message.text]
    await state.update_data(format=selected_format)
    await send_params_prompt(message, state)

async def send_params_prompt(message: Message, state: FSMContext):
    data = await state.get_data()
    selected_format = data['format']
    
    if selected_format in ['jpg', 'jpeg', 'png', 'gif', 'ico', 'bmp', 'svg']:
        # Изображения
        await message.answer(
            f"🖼 <b>{selected_format.upper()}</b> формат (изображение)\n\n"
            "Введи параметры изображения:\n"
            "• <code>размер</code> - для квадратного изображения\n"
            "• <code>ширина высота</code> - для прямоугольного\n"
            "• Можно добавить цвет в формате #RRGGBB\n\n"
            "Примеры:\n"
            f"<code>500</code> - квадрат 500x500\n"
            f"<code>800 600 #FF0000</code> - красный прямоугольник\n\n"
            "Введи нужные параметры в чат 👇",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад")],
                    [KeyboardButton(text="Назад в меню")]
                ],
                resize_keyboard=True
            )
        )
    elif selected_format in ['txt', 'css', 'html', 'js', 'json']:
        # Текстовые файлы
        await message.answer(
            f"📝 <b>{selected_format.upper()}</b> формат (текстовый файл)\n\n"
            "Введи содержимое файла:\n\n"
            f"Пример для {selected_format.upper()}:\n"
            f"<code>{get_text_file_example(selected_format)}</code>\n\n"
            "Введи содержимое файла в чат 👇",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад")],
                    [KeyboardButton(text="Назад в меню")]
                ],
                resize_keyboard=True
            )
        )
    elif selected_format in ['docx', 'xlsx']:
        # Office файлы
        await message.answer(
            f"📄 <b>{selected_format.upper()}</b> формат (офисный документ)\n\n"
            "Введи текст для документа (будет создан простой документ с этим текстом):\n\n"
            "Введи текст в чат 👇",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад")],
                    [KeyboardButton(text="Назад в меню")]
                ],
                resize_keyboard=True
            )
        )
    elif selected_format in ['zip', 'rar']:
        # Архивы
        await message.answer(
            f"📦 <b>{selected_format.upper()}</b> формат (архив)\n\n"
            "Будет создан пустой архив. Введи любое сообщение для продолжения:\n\n"
            "Введи любое сообщение в чат 👇",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад")],
                    [KeyboardButton(text="Назад в меню")]
                ],
                resize_keyboard=True
            )
        )
    elif selected_format in ['mp4', 'avi']:
        # Видео
        await message.answer(
            f"🎬 <b>{selected_format.upper()}</b> формат (видео)\n\n"
            "Будет создан минимальный видео файл. Введи любое сообщение для продолжения:\n\n"
            "Введи любое сообщение в чат 👇",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад")],
                    [KeyboardButton(text="Назад в меню")]
                ],
                resize_keyboard=True
            )
        )
    elif selected_format == 'pdf':
        # PDF
        await message.answer(
            f"📕 <b>PDF</b> формат (документ)\n\n"
            "Введи текст для PDF документа:\n\n"
            "Введи текст в чат 👇",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад")],
                    [KeyboardButton(text="Назад в меню")]
                ],
                resize_keyboard=True
            )
        )
    
    await state.set_state(FileGeneratorStates.waiting_for_params)

def get_text_file_example(format_type):
    examples = {
        'txt': 'Привет, это текстовый файл!',
        'css': 'body {\n  margin: 0;\n  padding: 0;\n}',
        'html': '<!DOCTYPE html>\n<html>\n<head><title>Test</title></head>\n<body><h1>Hello</h1></body>\n</html>',
        'js': 'function hello() {\n  console.log("Hello World");\n}',
        'json': '{\n  "name": "test",\n  "value": 123\n}'
    }
    return examples.get(format_type, 'Пример текста')

async def process_file_params(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текстовое сообщение", reply_markup=get_back_menu())
        return
        
    if message.text == "Назад":
        await generate_file_command(message, state)
        return
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    try:
        data = await state.get_data()
        file_format = data['format']
        file_content = None
        filename = None
        
        # Генерация файла в зависимости от формата
        if file_format in ['jpg', 'jpeg', 'png', 'gif', 'ico', 'bmp']:
            file_content, filename = await generate_image_file(message.text, file_format)
        elif file_format == 'svg':
            file_content, filename = await generate_svg_file(message.text)
        elif file_format in ['txt', 'css', 'html', 'js']:
            file_content, filename = await generate_text_file(message.text, file_format)
        elif file_format == 'json':
            file_content, filename = await generate_json_file(message.text)
        elif file_format == 'pdf':
            file_content, filename = await generate_pdf_file(message.text)
        elif file_format == 'docx':
            file_content, filename = await generate_docx_file(message.text)
        elif file_format == 'xlsx':
            file_content, filename = await generate_xlsx_file(message.text)
        elif file_format == 'zip':
            file_content, filename = await generate_zip_file()
        elif file_format == 'rar':
            file_content, filename = await generate_rar_file()
        elif file_format in ['mp4', 'avi']:
            file_content, filename = await generate_video_file(file_format)
        else:
            await message.answer(f"❌ Формат {file_format} пока не поддерживается")
            return
        
        if file_content is None:
            await message.answer("❌ Ошибка при создании файла")
            return
        
        # Отправка файла
        await send_file(message, file_content, filename, file_format)
        
        # Предложение создать ещё
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✨ Создать ещё")],
                [KeyboardButton(text="Назад в меню")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            "Хочешь создать ещё один файл?",
            reply_markup=keyboard
        )
        await state.set_state(FileGeneratorStates.waiting_for_choice)
        
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {e}\nПопробуй еще раз")
    except Exception as e:
        logger.error(f"File generation error: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка при создании файла: {str(e)}")
        await state.clear()

async def generate_image_file(params_text: str, format_type: str):
    """Генерация изображения"""
    parts = params_text.split()
    
    # Парсинг параметров (аналогично image_generator)
    if len(parts) == 1:
        size = int(parts[0])
        width = height = size
        color = DEFAULT_COLOR
    elif len(parts) == 2:
        if parts[1].startswith('#'):
            size = int(parts[0])
            width = height = size
            hex_color = parts[1]
            if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_color):
                raise ValueError("Неверный формат цвета. Используй HEX (например: #FF5733)")
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            width = int(parts[0])
            height = int(parts[1])
            color = DEFAULT_COLOR
    elif len(parts) == 3:
        width = int(parts[0])
        height = int(parts[1])
        hex_color = parts[2]
        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_color):
            raise ValueError("Неверный формат цвета. Используй HEX (например: #FF5733)")
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    else:
        raise ValueError("Неверное количество параметров")
    
    if width <= 0 or height <= 0:
        raise ValueError("Размеры должны быть положительными числами")
    if width > MAX_IMAGE_SIZE or height > MAX_IMAGE_SIZE:
        raise ValueError(f"Максимальный размер: {MAX_IMAGE_SIZE}px")
    
    # Создание изображения
    img = Image.new('RGB', (width, height), color=color)
    d = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", size=min(width, height)//10)
    except (OSError, IOError):
        font = ImageFont.load_default()
    
    text = f"{width}x{height}\n.{format_type}"
    text_bbox = d.textbbox((0, 0), text, font=font)
    x = (width - (text_bbox[2] - text_bbox[0])) / 2
    y = (height - (text_bbox[3] - text_bbox[1])) / 2
    d.text((x, y), text, font=font, fill=TEXT_COLOR)
    
    # Сохранение в BytesIO
    img_byte_arr = io.BytesIO()
    save_format = format_type.upper() if format_type != 'jpg' else 'JPEG'
    if format_type == 'ico':
        # ICO требует специальной обработки - сохраняем как PNG
        # (настоящий ICO требует специальной библиотеки, но PNG с расширением .ico будет работать)
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue(), f"image_{width}x{height}.ico"
    elif format_type == 'gif':
        # GIF требует режим 'P' для палитры
        img_p = img.convert('P')
        img_p.save(img_byte_arr, format='GIF')
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue(), f"image_{width}x{height}.gif"
    else:
        img.save(img_byte_arr, format=save_format)
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue(), f"image_{width}x{height}.{format_type}"

async def generate_svg_file(params_text: str):
    """Генерация SVG файла"""
    parts = params_text.split()
    
    if len(parts) == 1:
        size = int(parts[0])
        width = height = size
        color = "#FFFFFF"
    elif len(parts) == 2:
        if parts[1].startswith('#'):
            size = int(parts[0])
            width = height = size
            color = parts[1]
        else:
            width = int(parts[0])
            height = int(parts[1])
            color = "#FFFFFF"
    elif len(parts) == 3:
        width = int(parts[0])
        height = int(parts[1])
        color = parts[2]
    else:
        raise ValueError("Неверное количество параметров")
    
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="{color}"/>
  <text x="{width//2}" y="{height//2}" font-family="Arial" font-size="{min(width, height)//10}" text-anchor="middle" fill="#000000">{width}x{height}</text>
</svg>'''
    
    return svg_content.encode('utf-8'), f"image_{width}x{height}.svg"

async def generate_text_file(content: str, format_type: str):
    """Генерация текстового файла"""
    # Для HTML добавляем базовую структуру если её нет
    if format_type == 'html':
        # Проверяем, есть ли уже полная HTML структура
        content_lower = content.lower().strip()
        if '<html' not in content_lower and '<!doctype' not in content_lower:
            # Если это просто текст, оборачиваем в HTML
            html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <pre>{content}</pre>
</body>
</html>'''
            return html_content.encode('utf-8'), "file.html"
        else:
            # Если уже есть HTML структура, просто возвращаем как есть
            return content.encode('utf-8'), "file.html"
    
    return content.encode('utf-8'), f"file.{format_type}"

async def generate_json_file(content: str):
    """Генерация JSON файла"""
    try:
        # Попытка распарсить как JSON
        json_obj = json.loads(content)
        json_content = json.dumps(json_obj, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        # Если не JSON, создаем простой объект
        json_content = json.dumps({"content": content}, ensure_ascii=False, indent=2)
    
    return json_content.encode('utf-8'), "file.json"

async def generate_pdf_file(content: str):
    """Генерация PDF файла с поддержкой русского языка"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.units import mm
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Пытаемся использовать встроенный шрифт с поддержкой кириллицы
        # DejaVu Sans поддерживает кириллицу, но может быть не установлен
        try:
            # Пробуем найти системный шрифт с поддержкой кириллицы
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            ]
            
            font_registered = False
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
                        font_name = 'CyrillicFont'
                        font_registered = True
                        break
                except Exception:
                    continue
            
            if not font_registered:
                # Используем встроенный шрифт (может не поддерживать кириллицу полностью)
                font_name = 'Helvetica'
        except Exception:
            font_name = 'Helvetica'
        
        # Разбиваем текст на строки
        lines = content.split('\n')
        y_position = height - 30 * mm
        line_height = 6 * mm
        font_size = 12
        
        p.setFont(font_name, font_size)
        
        for line in lines[:100]:  # Ограничение количества строк
            if y_position < 30 * mm:
                p.showPage()
                y_position = height - 30 * mm
                p.setFont(font_name, font_size)
            
            # Обрезаем строку если слишком длинная (примерно 80 символов для A4)
            if len(line) > 80:
                # Разбиваем длинные строки
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) < 80:
                        current_line += word + " "
                    else:
                        if current_line:
                            p.drawString(20 * mm, y_position, current_line.strip())
                            y_position -= line_height
                            if y_position < 30 * mm:
                                p.showPage()
                                y_position = height - 30 * mm
                                p.setFont(font_name, font_size)
                        current_line = word + " "
                if current_line:
                    p.drawString(20 * mm, y_position, current_line.strip())
                    y_position -= line_height
            else:
                p.drawString(20 * mm, y_position, line)
                y_position -= line_height
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue(), "file.pdf"
    except ImportError:
        raise ValueError("Библиотека reportlab не установлена. Установите: pip install reportlab")
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
        raise ValueError(f"Ошибка при создании PDF: {str(e)}")

async def generate_docx_file(content: str):
    """Генерация DOCX файла"""
    try:
        from docx import Document
        
        doc = Document()
        
        # Разбиваем текст на параграфы
        paragraphs = content.split('\n')
        for para in paragraphs:
            if para.strip():
                doc.add_paragraph(para.strip())
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue(), "file.docx"
    except ImportError:
        raise ValueError("Библиотека python-docx не установлена. Установите: pip install python-docx")
    except Exception as e:
        logger.error(f"DOCX generation error: {e}", exc_info=True)
        raise ValueError(f"Ошибка при создании DOCX: {str(e)}")

async def generate_xlsx_file(content: str):
    """Генерация XLSX файла"""
    try:
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        
        # Разбиваем текст на строки и добавляем в ячейки
        lines = content.split('\n')
        for idx, line in enumerate(lines[:1000], start=1):  # Ограничение 1000 строк
            ws[f'A{idx}'] = line[:32767]  # Максимальная длина ячейки Excel
        
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue(), "file.xlsx"
    except ImportError:
        raise ValueError("Библиотека openpyxl не установлена. Установите: pip install openpyxl")
    except Exception as e:
        logger.error(f"XLSX generation error: {e}", exc_info=True)
        raise ValueError(f"Ошибка при создании XLSX: {str(e)}")

async def generate_zip_file():
    """Генерация ZIP архива"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("readme.txt", "Это пустой архив")
    buffer.seek(0)
    return buffer.getvalue(), "archive.zip"

async def generate_rar_file():
    """Генерация RAR архива (заглушка - создает ZIP с расширением .rar)"""
    # RAR требует специальной библиотеки, создаем ZIP с расширением .rar
    # В реальности это не настоящий RAR, но файл будет создан
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("readme.txt", "Это архив (формат RAR не полностью поддерживается)")
    buffer.seek(0)
    return buffer.getvalue(), "archive.rar"

async def generate_video_file(format_type: str):
    """Генерация минимального видео файла"""
    # Создаем минимальные валидные заголовки для видео файлов
    # Эти файлы будут иметь правильную структуру, но не будут воспроизводиться
    
    if format_type == 'mp4':
        # Минимальный MP4 файл (ftyp box)
        # Это минимальный валидный MP4 файл с базовой структурой
        mp4_header = (
            b'\x00\x00\x00\x20'  # Box size (32 bytes)
            b'ftyp'              # Box type: ftyp
            b'isom'              # Major brand: ISO Media
            b'\x00\x00\x02\x00'  # Minor version
            b'isom'              # Compatible brand
            b'iso2'              # Compatible brand
            b'mp41'              # Compatible brand
        )
        return mp4_header, "video.mp4"
        
    elif format_type == 'avi':
        # Минимальный AVI файл (RIFF заголовок)
        # Это минимальный валидный AVI файл
        avi_header = (
            b'RIFF'              # RIFF signature
            b'\x00\x00\x00\x00'  # File size (will be calculated)
            b'AVI '             # AVI signature
            b'LIST'             # LIST chunk
            b'\x00\x00\x00\x00' # Chunk size
            b'hdrl'             # hdrl list
            b'avih'             # avih chunk
            b'\x38\x00\x00\x00' # Chunk size (56 bytes)
            b'\x00\x00\x00\x00' * 14  # AVI header data (zeros for minimal file)
        )
        return avi_header, "video.avi"
    else:
        minimal_content = b''
    
    return minimal_content, f"video.{format_type}"

async def send_file(message: Message, file_content: bytes, filename: str, file_format: str):
    """Отправка файла пользователю"""
    try:
        # Убеждаемся, что file_content это bytes
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')
        
        file_input = BufferedInputFile(file=file_content, filename=filename)
        
        # Определяем метод отправки в зависимости от типа файла
        if file_format in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'ico']:
            await message.answer_photo(
                photo=file_input,
                caption=f"✅ Готово! {filename}"
            )
        else:
            # Все остальные файлы отправляем как документы
            await message.answer_document(
                document=file_input,
                caption=f"✅ Готово! {filename}"
            )
    except Exception as e:
        logger.error(f"Error sending file: {e}", exc_info=True)
        raise

async def handle_choice(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return
        
    if message.text == "✨ Создать ещё":
        await generate_file_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Пожалуйста, используй кнопки")

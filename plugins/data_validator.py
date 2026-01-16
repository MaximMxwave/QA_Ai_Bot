from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import json
import logging
import yaml
import xml.etree.ElementTree as ET
import xmltodict
from lxml import etree
from io import StringIO
from messages import MENU_MSG, get_main_menu, get_back_menu

logger = logging.getLogger(__name__)

def escape_xml_tags(text: str) -> str:
    """Экранирование XML тегов для безопасного отображения в HTML"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))

class DataValidatorStates(StatesGroup):
    waiting_for_format = State()
    waiting_for_data = State()
    waiting_for_repeat = State()

async def data_validator_command(message: Message, state: FSMContext):
    """Начало работы с валидатором данных"""
    await state.set_state(DataValidatorStates.waiting_for_format)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📑 JSON")],
            [KeyboardButton(text="📄 XML")],
            [KeyboardButton(text="📋 YAML")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📑 <b>Валидатор данных JSON XML YAML</b>\n\n"
        "Выбери формат данных для проверки:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def process_format_choice(message: Message, state: FSMContext):
    """Обработка выбора формата данных"""
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    valid_formats = ["📑 JSON", "📄 XML", "📋 YAML"]
    if message.text not in valid_formats:
        await message.answer("⚠ Пожалуйста, выбери формат из списка")
        return
    
    # Сохраняем выбранный формат в состоянии
    format_map = {
        "📑 JSON": "json",
        "📄 XML": "xml",
        "📋 YAML": "yaml"
    }
    selected_format = format_map[message.text]
    await state.update_data(format=selected_format)
    
    await state.set_state(DataValidatorStates.waiting_for_data)
    
    # Показываем примеры в зависимости от формата
    examples = {
        "json": (
            "📑 <b>Отправь JSON для проверки</b>\n\n"
            "<b>Пример:</b>\n"
            "<code>{\n  \"name\": \"Alex\",\n  \"age\": 28,\n  \"city\": \"London\"\n}</code>\n\n"
            "Я проверю:\n"
            "✅ Синтаксис\n"
            "✅ Формат\n"
            "✅ Скобки"
        ),
        "xml": (
            "📄 <b>Отправь XML для проверки</b>\n\n"
            "<b>Пример:</b>\n"
            "<code>&lt;person&gt;\n  &lt;name&gt;Alex&lt;/name&gt;\n  &lt;age&gt;28&lt;/age&gt;\n  &lt;city&gt;London&lt;/city&gt;\n&lt;/person&gt;</code>\n\n"
            "Я проверю:\n"
            "✅ Синтаксис XML\n"
            "✅ Корректность тегов\n"
            "✅ Структуру документа"
        ),
        "yaml": (
            "📋 <b>Отправь YAML для проверки</b>\n\n"
            "<b>Пример:</b>\n"
            "<code>name: Alex\nage: 28\ncity: London</code>\n\n"
            "Я проверю:\n"
            "✅ Синтаксис YAML\n"
            "✅ Отступы\n"
            "✅ Структуру данных"
        )
    }
    
    await message.answer(
        examples[selected_format],
        parse_mode="HTML",
        reply_markup=get_back_menu()
    )

async def process_data_validation(message: Message, state: FSMContext):
    """Обработка и валидация данных"""
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текстовое сообщение с данными", reply_markup=get_back_menu())
        return
        
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    # Получаем выбранный формат из состояния
    data = await state.get_data()
    selected_format = data.get('format', 'json')
    
    data_text = message.text
    
    try:
        if selected_format == "json":
            await validate_json(message, data_text)
        elif selected_format == "xml":
            await validate_xml(message, data_text)
        elif selected_format == "yaml":
            await validate_yaml(message, data_text)
        
        # Предлагаем проверить еще
        await ask_for_repeat(message, state)
        
    except Exception as e:
        logger.error(f"Data validation error: {e}", exc_info=True)
        await message.answer(
            f"❌ Неизвестная ошибка при обработке {selected_format.upper()}",
            reply_markup=get_back_menu()
        )
        await state.clear()

async def validate_json(message: Message, json_text: str):
    """Валидация JSON"""
    try:
        # Пытаемся распарсить JSON
        parsed = json.loads(json_text)
        
        # Форматируем для красивого вывода
        formatted_json = json.dumps(parsed, indent=2, ensure_ascii=False)
        
        # Получаем информацию о структуре
        structure_info = analyze_json_structure(parsed)
        
        # Отправляем результат
        await message.answer(
            "✅ <b>JSON валиден!</b>\n\n"
            f"<b>📊 Информация о структуре:</b>\n"
            f"{structure_info}",
            parse_mode="HTML"
        )
        
        # Отправляем отформатированный JSON
        # Экранируем для безопасности
        escaped_json = escape_xml_tags(formatted_json)
        
        if len(escaped_json) > 4000:
            # Разбиваем на части
            parts = []
            current_part = ""
            
            for line in escaped_json.split('\n'):
                if len(current_part) + len(line) + 1 > 4000:
                    parts.append(current_part)
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'
            
            if current_part:
                parts.append(current_part)
            
            await message.answer(
                "<b>📑 Отформатированный JSON (часть 1):</b>",
                parse_mode="HTML"
            )
            
            for i, part in enumerate(parts):
                await message.answer(
                    f"<code>{part}</code>",
                    parse_mode="HTML"
                )
                
                if i < len(parts) - 1:
                    await message.answer(
                        f"<b>📑 Отформатированный JSON (часть {i+2}):</b>",
                        parse_mode="HTML"
                    )
        else:
            await message.answer(
                "<b>📑 Отформатированный JSON:</b>",
                parse_mode="HTML"
            )
            await message.answer(
                f"<code>{escaped_json}</code>",
                parse_mode="HTML"
            )
        
    except json.JSONDecodeError as e:
        # Экранируем текст ошибки
        problem_part = json_text[max(0, e.pos-20):e.pos+20]
        escaped_problem = escape_xml_tags(problem_part)
        
        error_msg = (
            f"❌ <b>Ошибка в JSON:</b>\n"
            f"• Строка: {e.lineno}\n"
            f"• Колонка: {e.colno}\n"
            f"• Сообщение: {e.msg}\n\n"
            f"<b>Проблемный участок:</b>\n"
            f"<code>{escaped_problem}</code>"
        )
        await message.answer(
            error_msg,
            parse_mode="HTML"
        )
        raise

async def validate_xml(message: Message, xml_text: str):
    """Валидация XML"""
    try:
        # Пытаемся распарсить XML с помощью lxml (более строгая проверка)
        parser = etree.XMLParser(resolve_entities=False)
        tree = etree.parse(StringIO(xml_text), parser)
        root = tree.getroot()
        
        # Форматируем XML для красивого вывода
        formatted_xml = etree.tostring(root, encoding='unicode', pretty_print=True)
        
        # Получаем информацию о структуре
        # ВАЖНО: structure_info содержит строки вида "<tag>", а мы шлём сообщение с parse_mode="HTML".
        # Поэтому обязательно экранируем, иначе Telegram попытается распарсить это как HTML и упадёт
        # с ошибкой "can't parse entities: Unsupported start tag ...".
        structure_info = analyze_xml_structure(root)
        escaped_structure_info = escape_xml_tags(structure_info)
        
        # Также пробуем конвертировать в словарь для анализа
        try:
            xml_dict = xmltodict.parse(xml_text)
            dict_info = "\n✅ Можно конвертировать в словарь"
        except:
            dict_info = "\n⚠ Не удалось конвертировать в словарь"
        
        # Отправляем результат в нескольких сообщениях
        # 1. Сообщение о успешной валидации
        await message.answer(
            "✅ <b>XML валиден!</b>\n\n"
            f"<b>📊 Информация о структуре:</b>\n"
            f"<pre>{escaped_structure_info}{dict_info}</pre>",
            parse_mode="HTML"
        )
        
        # 2. Отправляем отформатированный XML как отдельное сообщение
        # Разбиваем XML на части если он слишком длинный
        max_length = 4000  # Telegram ограничение на длину сообщения
        
        if len(formatted_xml) > max_length:
            # Разбиваем на части
            parts = []
            current_part = ""
            
            for line in formatted_xml.split('\n'):
                if len(current_part) + len(line) + 1 > max_length:
                    parts.append(current_part)
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'
            
            if current_part:
                parts.append(current_part)
            
            await message.answer(
                "<b>📄 Отформатированный XML (часть 1):</b>",
                parse_mode="HTML"
            )
            
            for i, part in enumerate(parts):
                # Экранируем XML теги перед отправкой
                escaped_xml = escape_xml_tags(part)
                await message.answer(
                    f"<code>{escaped_xml}</code>",
                    parse_mode="HTML"
                )
                
                if i < len(parts) - 1:
                    await message.answer(
                        f"<b>📄 Отформатированный XML (часть {i+2}):</b>",
                        parse_mode="HTML"
                    )
        else:
            # Отправляем весь XML одним сообщением
            await message.answer(
                "<b>📄 Отформатированный XML:</b>",
                parse_mode="HTML"
            )
            # Экранируем XML теги перед отправкой
            escaped_xml = escape_xml_tags(formatted_xml)
            await message.answer(
                f"<code>{escaped_xml}</code>",
                parse_mode="HTML"
            )
        
    except etree.XMLSyntaxError as e:
        # Экранируем XML теги в ошибке
        problem_part = xml_text[max(0, e.position-50):e.position+50]
        escaped_problem = escape_xml_tags(problem_part)
        
        error_msg = (
            f"❌ <b>Ошибка в XML:</b>\n"
            f"• Строка: {e.lineno}\n"
            f"• Сообщение: {e.msg}\n\n"
            f"<b>Проблемный участок:</b>\n"
            f"<code>{escaped_problem}</code>"
        )
        await message.answer(
            error_msg,
            parse_mode="HTML"
        )
        raise
    except Exception as e:
        error_msg = (
            f"❌ <b>Ошибка в XML:</b>\n"
            f"• Сообщение: {str(e)}\n\n"
            f"<b>Проверь:</b>\n"
            f"• Корректность тегов\n"
            f"• Закрытие всех элементов\n"
            f"• Корректность атрибутов"
        )
        await message.answer(
            error_msg,
            parse_mode="HTML"
        )
        raise

async def validate_yaml(message: Message, yaml_text: str):
    """Валидация YAML"""
    try:
        # Пытаемся распарсить YAML
        parsed = yaml.safe_load(yaml_text)
        
        # Форматируем для красивого вывода
        formatted_yaml = yaml.dump(parsed, default_flow_style=False, allow_unicode=True)
        
        # Получаем информацию о структуре
        structure_info = analyze_yaml_structure(parsed)
        
        # Отправляем результат
        await message.answer(
            "✅ <b>YAML валиден!</b>\n\n"
            f"<b>📊 Информация о структуре:</b>\n"
            f"{structure_info}",
            parse_mode="HTML"
        )
        
        # Отправляем отформатированный YAML
        # Экранируем для безопасности
        escaped_yaml = escape_xml_tags(formatted_yaml)
        
        if len(escaped_yaml) > 4000:
            # Разбиваем на части
            parts = []
            current_part = ""
            
            for line in escaped_yaml.split('\n'):
                if len(current_part) + len(line) + 1 > 4000:
                    parts.append(current_part)
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'
            
            if current_part:
                parts.append(current_part)
            
            await message.answer(
                "<b>📋 Отформатированный YAML (часть 1):</b>",
                parse_mode="HTML"
            )
            
            for i, part in enumerate(parts):
                await message.answer(
                    f"<code>{part}</code>",
                    parse_mode="HTML"
                )
                
                if i < len(parts) - 1:
                    await message.answer(
                        f"<b>📋 Отформатированный YAML (часть {i+2}):</b>",
                        parse_mode="HTML"
                    )
        else:
            await message.answer(
                "<b>📋 Отформатированный YAML:</b>",
                parse_mode="HTML"
            )
            await message.answer(
                f"<code>{escaped_yaml}</code>",
                parse_mode="HTML"
            )
        
    except yaml.YAMLError as e:
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            # Экранируем проблемный участок
            problem_part = yaml_text[max(0, mark.index-50):mark.index+50]
            escaped_problem = escape_xml_tags(problem_part)
            
            error_msg = (
                f"❌ <b>Ошибка в YAML:</b>\n"
                f"• Строка: {mark.line + 1}\n"
                f"• Колонка: {mark.column + 1}\n"
                f"• Сообщение: {e.problem}\n\n"
                f"<b>Проблемный участок:</b>\n"
                f"<code>{escaped_problem}</code>"
            )
        else:
            error_msg = (
                f"❌ <b>Ошибка в YAML:</b>\n"
                f"• Сообщение: {str(e)}\n\n"
                f"<b>Проверь:</b>\n"
                f"• Отступы (должны быть пробелы, не табы)\n"
                f"• Синтаксис\n"
                f"• Структуру данных"
            )
        await message.answer(
            error_msg,
            parse_mode="HTML"
        )
        raise

def analyze_json_structure(data, indent=0):
    """Анализ структуры JSON"""
    if data is None:
        return "null"
    
    if isinstance(data, dict):
        result = "Объект {\n"
        for key, value in data.items():
            result += "  " * (indent + 1) + f"{key}: {analyze_json_structure(value, indent + 1)}\n"
        result += "  " * indent + "}"
        return result
    elif isinstance(data, list):
        if data:
            # Показываем тип первого элемента
            elem_type = type(data[0]).__name__
            result = f"Массив [{len(data)} элементов, тип: {elem_type}]"
            if len(data) <= 3:  # Показываем первые несколько элементов
                result += " [\n"
                for i, item in enumerate(data[:3]):
                    result += "  " * (indent + 1) + f"[{i}]: {analyze_json_structure(item, indent + 1)}\n"
                if len(data) > 3:
                    result += "  " * (indent + 1) + f"... еще {len(data) - 3} элементов\n"
                result += "  " * indent + "]"
        else:
            result = "Пустой массив []"
        return result
    elif isinstance(data, str):
        return f"Строка (длина: {len(data)})"
    elif isinstance(data, (int, float)):
        return f"Число ({data})"
    elif isinstance(data, bool):
        return f"Булево ({data})"
    else:
        return str(type(data).__name__)

def analyze_xml_structure(element, indent=0):
    """Анализ структуры XML"""
    result = f"Элемент: <{element.tag}>\n"
    
    # Атрибуты
    if element.attrib:
        result += "  " * indent + "Атрибуты:\n"
        for key, value in element.attrib.items():
            result += "  " * (indent + 1) + f"{key} = \"{value}\"\n"
    
    # Дочерние элементы
    children = list(element)
    if children:
        result += "  " * indent + f"Дочерние элементы ({len(children)}):\n"
        for child in children[:5]:  # Показываем первые 5 элементов
            result += "  " * (indent + 1) + f"<{child.tag}>\n"
            # Рекурсивно анализируем структуру
            child_structure = analyze_xml_structure(child, indent + 2)
            result += child_structure
        if len(children) > 5:
            result += "  " * (indent + 1) + f"... еще {len(children) - 5} элементов\n"
    
    # Текст
    if element.text and element.text.strip():
        text = element.text.strip()
        if len(text) > 50:
            text = text[:47] + "..."
        result += "  " * indent + f"Текст: \"{text}\"\n"
    
    return result

def analyze_yaml_structure(data, indent=0):
    """Анализ структуры YAML"""
    if data is None:
        return "null"
    
    if isinstance(data, dict):
        result = "Словарь {\n"
        for key, value in data.items():
            result += "  " * (indent + 1) + f"{key}: {analyze_yaml_structure(value, indent + 1)}\n"
        result += "  " * indent + "}"
        return result
    elif isinstance(data, list):
        if data:
            result = f"Список [{len(data)} элементов]\n"
            for i, item in enumerate(data[:3]):  # Показываем первые 3 элемента
                result += "  " * (indent + 1) + f"- {analyze_yaml_structure(item, indent + 1)}\n"
            if len(data) > 3:
                result += "  " * (indent + 1) + f"... еще {len(data) - 3} элементов\n"
        else:
            result = "Пустой список []"
        return result
    elif isinstance(data, str):
        return f"Строка (длина: {len(data)})"
    elif isinstance(data, (int, float)):
        return f"Число ({data})"
    elif isinstance(data, bool):
        return f"Булево ({data})"
    else:
        return str(type(data).__name__)

async def ask_for_repeat(message: Message, state: FSMContext):
    """Спрашиваем, хочет ли пользователь проверить еще данные"""
    repeat_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Проверить еще")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Хочешь проверить еще данные?",
        reply_markup=repeat_keyboard
    )
    await state.set_state(DataValidatorStates.waiting_for_repeat)

async def process_repeat_choice(message: Message, state: FSMContext):
    """Обрабатываем выбор пользователя после валидации"""
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return
        
    if message.text == "🔄 Проверить еще":
        await data_validator_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Используй кнопки")

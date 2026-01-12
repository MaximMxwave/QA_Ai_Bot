from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import html
from messages import MENU_MSG, get_main_menu, get_back_menu

logger = logging.getLogger(__name__)

class TestCaseTemplateStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_preconditions = State()
    waiting_for_steps = State()
    waiting_for_expected_result = State()
    waiting_for_priority = State()
    waiting_for_choice = State()

PRIORITIES = ['Критический', 'Высокий', 'Средний', 'Низкий']

async def test_case_template_command(message: Message, state: FSMContext):
    """Начало создания тест-кейса"""
    await state.set_state(TestCaseTemplateStates.waiting_for_title)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📋 <b>Создание тест-кейса</b>\n\n"
        "Введи название тест-кейса:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def process_title(message: Message, state: FSMContext):
    """Обработка названия тест-кейса"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи название тест-кейса")
        return
    
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    await state.update_data(title=message.text)
    await state.set_state(TestCaseTemplateStates.waiting_for_description)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📝 Введи описание тест-кейса:\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard
    )

async def process_description(message: Message, state: FSMContext):
    """Обработка описания тест-кейса"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи описание или нажми 'Пропустить'")
        return
    
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    description = "" if message.text == "Пропустить" else message.text
    await state.update_data(description=description)
    await state.set_state(TestCaseTemplateStates.waiting_for_preconditions)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "⚙️ Введи предусловия:\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard
    )

async def process_preconditions(message: Message, state: FSMContext):
    """Обработка предусловий"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи предусловия или нажми 'Пропустить'")
        return
    
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    preconditions = "" if message.text == "Пропустить" else message.text
    await state.update_data(preconditions=preconditions)
    await state.set_state(TestCaseTemplateStates.waiting_for_steps)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📌 Введи шаги тест-кейса:\n"
        "(каждый шаг с новой строки или через точку с запятой)\n\n"
        "Пример:\n"
        "1. Открыть приложение\n"
        "2. Ввести логин\n"
        "3. Ввести пароль\n"
        "4. Нажать 'Войти'",
        reply_markup=keyboard
    )

async def process_steps(message: Message, state: FSMContext):
    """Обработка шагов тест-кейса"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи шаги тест-кейса")
        return
    
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    # Форматируем шаги
    steps_text = message.text.strip()
    # Если шаги разделены точкой с запятой или новой строкой
    if ';' in steps_text:
        steps_list = [s.strip() for s in steps_text.split(';') if s.strip()]
    elif '\n' in steps_text:
        steps_list = [s.strip() for s in steps_text.split('\n') if s.strip()]
    else:
        steps_list = [steps_text] if steps_text else []
    
    # Убираем нумерацию, если она есть
    formatted_steps = []
    for step in steps_list:
        # Убираем начальные цифры и точки
        step = step.lstrip('0123456789. ').strip()
        if step:  # Добавляем только непустые шаги
            formatted_steps.append(step)
    
    if not formatted_steps:
        await message.answer("❌ Пожалуйста, введи хотя бы один шаг тест-кейса")
        return
    
    await state.update_data(steps=formatted_steps)
    await state.set_state(TestCaseTemplateStates.waiting_for_expected_result)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "✅ Введи ожидаемый результат:\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard
    )

async def process_expected_result(message: Message, state: FSMContext):
    """Обработка ожидаемого результата"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи ожидаемый результат или нажми 'Пропустить'")
        return
    
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    expected_result = "" if message.text == "Пропустить" else message.text
    await state.update_data(expected_result=expected_result)
    await state.set_state(TestCaseTemplateStates.waiting_for_priority)
    
    priority_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=priority) for priority in PRIORITIES[:2]],
            [KeyboardButton(text=priority) for priority in PRIORITIES[2:]],
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "🎯 Выбери приоритет тест-кейса:",
        reply_markup=priority_keyboard
    )

async def process_priority(message: Message, state: FSMContext):
    """Обработка приоритета и генерация шаблона"""
    if not message.text:
        await message.answer("❌ Пожалуйста, выбери приоритет или нажми 'Пропустить'")
        return
    
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    priority = "" if message.text == "Пропустить" else message.text
    if priority and priority not in PRIORITIES:
        await message.answer("⚠️ Выбери приоритет из предложенных вариантов")
        return
    
    await state.update_data(priority=priority)
    
    # Генерируем шаблон тест-кейса
    try:
        data = await state.get_data()
        template = generate_test_case_template(data)
        
        await message.answer(
            template,
            parse_mode="HTML"
        )
        
        await ask_for_new_template(message, state)
        
    except Exception as e:
        logger.error(f"Test case template generation error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при создании шаблона", reply_markup=get_main_menu())
        await state.clear()

def generate_test_case_template(data: dict) -> str:
    """Генерация тест-кейса в формате HTML"""
    title = html.escape(str(data.get('title', 'Не указано')))
    description = html.escape(str(data.get('description', '')))
    preconditions = html.escape(str(data.get('preconditions', '')))
    steps = data.get('steps', [])
    expected_result = html.escape(str(data.get('expected_result', '')))
    priority = html.escape(str(data.get('priority', 'Не указан')))
    
    template = f"<b>📋 ТЕСТ-КЕЙС</b>\n\n"
    template += f"<b>Название:</b> {title}\n\n"
    
    if description:
        template += f"<b>Описание:</b>\n{description}\n\n"
    
    if preconditions:
        template += f"<b>Предусловия:</b>\n{preconditions}\n\n"
    
    template += "<b>Шаги выполнения:</b>\n"
    if steps:
        for i, step in enumerate(steps, 1):
            escaped_step = html.escape(str(step))
            template += f"{i}. {escaped_step}\n"
    else:
        template += "Не указаны\n"
    template += "\n"
    
    if expected_result:
        template += f"<b>Ожидаемый результат:</b>\n{expected_result}\n\n"
    
    template += f"<b>Приоритет:</b> {priority}\n\n"
    template += "<b>Фактический результат:</b> <i>(заполняется при выполнении)</i>\n"
    template += "<b>Статус:</b> <i>(Не выполнен / Провален / Пропущен / Пройден)</i>"
    
    return template

async def ask_for_new_template(message: Message, state: FSMContext):
    """Предложение создать новый тест-кейс"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Создать ещё")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "Хочешь создать ещё один тест-кейс?",
        reply_markup=keyboard
    )
    await state.set_state(TestCaseTemplateStates.waiting_for_choice)

async def handle_choice(message: Message, state: FSMContext):
    """Обработка выбора пользователя"""
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return
    
    if message.text == "✨ Создать ещё":
        await test_case_template_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Пожалуйста, используй кнопки")


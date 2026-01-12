from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import json
import logging
from messages import MENU_MSG, get_main_menu, get_back_menu, WELCOME_MSG

logger = logging.getLogger(__name__)

class JsonValidatorStates(StatesGroup):
    waiting_for_json = State()
    waiting_for_repeat = State()

async def json_validator_command(message: Message, state: FSMContext):
    await state.set_state(JsonValidatorStates.waiting_for_json)
    await message.answer(
        "📑 Отправь JSON для проверки. Пример:\n"
        "<code>{\n  \"name\": \"Alex\",\n  \"age\": 28,\n  \"city\": \"London\"\n}</code>\n\n"
        "Я проверю:\n"
        "1. Синтаксис\n"
        "2. Формат\n"
        "3. Скобки",
        parse_mode="HTML",
        reply_markup=get_back_menu()
    )

async def process_json_validation(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текстовое сообщение с JSON", reply_markup=get_back_menu())
        return
        
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    json_text = message.text
    try:
        # Пытаемся распарсить JSON
        parsed = json.loads(json_text)
        
        # Форматируем для красивого вывода
        formatted_json = json.dumps(parsed, indent=2, ensure_ascii=False)
        
        await message.answer(
            "✅ <b>Всё отлично JSON валиден!</b>\n\n"
            "<b>📑 Отформатированный JSON:</b>\n"
            f"<code>{formatted_json}</code>",
            parse_mode="HTML"
        )
        
        # Предлагаем проверить еще один JSON
        await ask_for_repeat(message, state)
        
    except json.JSONDecodeError as e:
        error_msg = (
            f"❌ <b>Ошибка в JSON:</b>\n"
            f"• Строка: {e.lineno}\n"
            f"• Колонка: {e.colno}\n"
            f"• Сообщение: {e.msg}\n\n"
            f"<b>Проблемный участок:</b>\n"
            f"<code>{json_text[max(0, e.pos-20):e.pos+20]}</code>"
        )
        await message.answer(
            error_msg,
            parse_mode="HTML"
        )
        # Предлагаем исправить и проверить снова
        await ask_for_repeat(message, state)
        
    except Exception as e:
        logger.error(f"JSON validation error: {e}", exc_info=True)
        await message.answer(
            "❌ Неизвестная ошибка при обработке JSON",
            reply_markup=get_back_menu()
        )
        await state.clear()

async def ask_for_repeat(message: Message, state: FSMContext):
    """Спрашиваем, хочет ли пользователь проверить еще один JSON"""
    repeat_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Проверить еще JSON")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Хочешь проверить еще один JSON?",
        reply_markup=repeat_keyboard
    )
    await state.set_state(JsonValidatorStates.waiting_for_repeat)

async def process_repeat_choice(message: Message, state: FSMContext):
    """Обрабатываем выбор пользователя после валидации"""
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return
        
    if message.text == "Проверить еще JSON":
        await json_validator_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Используй кнопки")

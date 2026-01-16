from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import logging
from messages import MENU_MSG, get_main_menu, get_back_menu

logger = logging.getLogger(__name__)

class TimestampConverterStates(StatesGroup):
    waiting_for_input = State()
    waiting_for_convert_choice = State()

async def timestamp_converter_command(message: Message, state: FSMContext):
    await show_input_menu(message, state)

async def show_input_menu(message: Message, state: FSMContext):
    builder = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "🕐 <b>Конвертировать Timestamp</b>\n\n"
        "Отправь мне:\n"
        "• Timestamp (число) - для конвертации в дату\n"
        "• Дата в формате: DD.MM.YYYY или YYYY-MM-DD\n"
        "• Дата и время: DD.MM.YYYY HH:MM или YYYY-MM-DD HH:MM:SS",
        parse_mode="HTML",
        reply_markup=builder
    )
    await state.set_state(TimestampConverterStates.waiting_for_input)

async def process_timestamp_input(message: Message, state: FSMContext):
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    try:
        input_text = message.text.strip()
        
        # Попытка распознать timestamp (число)
        # Проверяем, является ли строка числом (только цифры, точка/запятая, знак минус)
        cleaned_for_check = input_text.replace(',', '.').lstrip('-')
        # Если после очистки остались только цифры и одна точка - это число
        if cleaned_for_check.replace('.', '').isdigit() and cleaned_for_check.count('.') <= 1:
            try:
                timestamp = float(input_text.replace(',', '.'))
                is_timestamp = True
            except ValueError:
                is_timestamp = False
        else:
            is_timestamp = False
        
        if is_timestamp:
            
            # Проверяем, это секунды или миллисекунды
            if timestamp > 1e10:  # Если больше 10 миллиардов, это миллисекунды
                timestamp_seconds = timestamp / 1000
            else:
                timestamp_seconds = timestamp
            
            # Конвертируем в datetime
            dt = datetime.fromtimestamp(timestamp_seconds)
            
            result = (
                "🕐 <b>Результат конвертации:</b>\n\n"
                f"> <b>Timestamp:</b> <code>{int(timestamp_seconds)}</code> (секунды)\n"
                f"> <b>Timestamp (мс):</b> <code>{int(timestamp_seconds * 1000)}</code> (миллисекунды)\n\n"
                f"> <b>Дата и время:</b>\n"
                f"> <code>{dt.strftime('%d.%m.%Y %H:%M:%S')}</code>\n"
                f"> <code>{dt.strftime('%Y-%m-%d %H:%M:%S')}</code>\n\n"
                f"> <b>Только дата:</b>\n"
                f"> <code>{dt.strftime('%d.%m.%Y')}</code>\n"
                f"> <code>{dt.strftime('%Y-%m-%d')}</code>"
            )
            
            await message.answer(result, parse_mode="HTML")
            await ask_for_convert_again(message, state)
            return
        
        # Попытка распознать дату
        dt = None
        date_formats = [
            '%d.%m.%Y %H:%M:%S',
            '%d.%m.%Y %H:%M',
            '%d.%m.%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(input_text, fmt)
                break
            except ValueError:
                continue
        
        if dt is None:
            await message.answer(
                "⚠ Не удалось распознать формат.\n\n"
                "Поддерживаемые форматы:\n"
                "• Timestamp: 1234567890 или 1234567890.123\n"
                "• Дата: DD.MM.YYYY или YYYY-MM-DD\n"
                "• Дата и время: DD.MM.YYYY HH:MM:SS"
            )
            return
        
        # Конвертируем дату в timestamp
        timestamp_seconds = dt.timestamp()
        timestamp_milliseconds = int(timestamp_seconds * 1000)
        
        result = (
            "🕐 <b>Результат конвертации:</b>\n\n"
            f"> <b>Дата и время:</b> <code>{dt.strftime('%d.%m.%Y %H:%M:%S')}</code>\n\n"
            f"> <b>Timestamp (секунды):</b> <code>{int(timestamp_seconds)}</code>\n"
            f"> <b>Timestamp (миллисекунды):</b> <code>{timestamp_milliseconds}</code>\n\n"
            f"> <b>Другие форматы:</b>\n"
            f"> <code>{dt.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
            f"> <code>{dt.strftime('%d.%m.%Y')}</code>"
        )
        
        await message.answer(result, parse_mode="HTML")
        await ask_for_convert_again(message, state)
        
    except ValueError as e:
        logger.error(f"Timestamp conversion error: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка при конвертации.\n\n"
            "Проверь формат ввода:\n"
            "• Timestamp: число (например, 1704067200)\n"
            "• Дата: DD.MM.YYYY или YYYY-MM-DD"
        )
    except Exception as e:
        logger.error(f"Timestamp converter error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при конвертации", reply_markup=get_main_menu())
        await state.clear()

async def ask_for_convert_again(message: Message, state: FSMContext):
    builder = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Конвертировать еще")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("Хочешь конвертировать еще?", reply_markup=builder)
    await state.set_state(TimestampConverterStates.waiting_for_convert_choice)

async def process_convert_choice(message: Message, state: FSMContext):
    if message.text == "✨ Конвертировать еще":
        await show_input_menu(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Используй кнопки")

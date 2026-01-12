from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from faker import Faker
import logging
from messages import MENU_MSG, get_main_menu, get_back_menu

logger = logging.getLogger(__name__)

# Инициализация Faker с локалью для русских данных
fake_ru = Faker('ru_RU')
fake_en = Faker()

class TestDataGeneratorStates(StatesGroup):
    waiting_for_count = State()
    waiting_for_regenerate_choice = State()

async def generate_test_data_command(message: Message, state: FSMContext):
    """Начало генерации тестовых данных"""
    await state.set_state(TestDataGeneratorStates.waiting_for_count)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "👥 <b>Создание тестовых данных пользователей</b>\n\n"
        "Введи количество пользователей для генерации (от 1 до 50):",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def process_count(message: Message, state: FSMContext):
    """Обработка количества пользователей"""
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    try:
        count = int(message.text)
        if count < 1 or count > 50:
            await message.answer("❌ Пожалуйста, введи число от 1 до 50")
            return
        
        await generate_and_show_users(message, state, count)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введи корректное число (от 1 до 50)")
    except Exception as e:
        logger.error(f"Test data generation error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при генерации данных", reply_markup=get_main_menu())
        await state.clear()

async def generate_and_show_users(message: Message, state: FSMContext, count: int):
    """Генерация и отображение тестовых данных пользователей"""
    try:
        users_data = []
        
        for i in range(count):
            # Генерация имени (русское)
            first_name = fake_ru.first_name()
            last_name = fake_ru.last_name()
            full_name = f"{first_name} {last_name}"
            
            # Генерация логина (уникальный логин на латинице)
            username = fake_en.user_name()[:12] + str(fake_en.random_int(min=100, max=999))
            
            # Генерация email
            email = fake_en.email()
            
            # Генерация пароля (сильный пароль)
            password = fake_en.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
            
            # Генерация адреса (русский адрес)
            address_line = fake_ru.street_address()
            city = fake_ru.city()
            postal_code = fake_ru.postcode()
            country = "Россия"
            full_address = f"{address_line}, {city}, {postal_code}, {country}"
            
            users_data.append({
                'name': full_name,
                'username': username,
                'email': email,
                'password': password,
                'address': full_address
            })
        
        # Формирование сообщения
        result_text = f"👥 <b>Сгенерировано пользователей: {count}</b>\n\n"
        result_text += "═" * 40 + "\n\n"
        
        for idx, user in enumerate(users_data, 1):
            result_text += f"<b>👤 Пользователь #{idx}</b>\n"
            result_text += f"├ Имя: <code>{user['name']}</code>\n"
            result_text += f"├ Логин: <code>{user['username']}</code>\n"
            result_text += f"├ Email: <code>{user['email']}</code>\n"
            result_text += f"├ Пароль: <code>{user['password']}</code>\n"
            result_text += f"└ Адрес: {user['address']}\n"
            
            if idx < len(users_data):
                result_text += "\n" + "─" * 40 + "\n\n"
        
        # Отправка сообщения (разбиваем на части, если слишком длинное)
        max_length = 4096
        if len(result_text) > max_length:
            # Разбиваем на несколько сообщений
            parts = []
            current_part = f"👥 <b>Сгенерировано пользователей: {count}</b>\n\n"
            
            for idx, user in enumerate(users_data, 1):
                user_text = f"<b>👤 Пользователь #{idx}</b>\n"
                user_text += f"├ Имя: <code>{user['name']}</code>\n"
                user_text += f"├ Логин: <code>{user['username']}</code>\n"
                user_text += f"├ Email: <code>{user['email']}</code>\n"
                user_text += f"├ Пароль: <code>{user['password']}</code>\n"
                user_text += f"└ Адрес: {user['address']}\n\n"
                
                if len(current_part) + len(user_text) > max_length:
                    parts.append(current_part)
                    current_part = user_text
                else:
                    current_part += user_text
            
            if current_part:
                parts.append(current_part)
            
            for part in parts:
                await message.answer(part, parse_mode="HTML")
        else:
            await message.answer(result_text, parse_mode="HTML")
        
        await ask_for_regenerate(message, state)
        
    except Exception as e:
        logger.error(f"Error generating users: {e}", exc_info=True)
        await message.answer("❌ Ошибка при генерации данных пользователей", reply_markup=get_main_menu())
        await state.clear()

async def ask_for_regenerate(message: Message, state: FSMContext):
    """Запрос на повторную генерацию"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Создать еще")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("Хочешь создать еще тестовые данные?", reply_markup=keyboard)
    await state.set_state(TestDataGeneratorStates.waiting_for_regenerate_choice)

async def process_regenerate_choice(message: Message, state: FSMContext):
    """Обработка выбора повторной генерации"""
    if message.text == "✨ Создать еще":
        await state.set_state(TestDataGeneratorStates.waiting_for_count)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Назад в меню")]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "👥 Введи количество пользователей для генерации (от 1 до 50):",
            reply_markup=keyboard
        )
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Используй кнопки для выбора")

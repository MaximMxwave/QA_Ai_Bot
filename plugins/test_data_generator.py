from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from faker import Faker
import logging
import json
import random
from datetime import datetime, timedelta
from messages import MENU_MSG, get_main_menu, get_back_menu

logger = logging.getLogger(__name__)

# Инициализация Faker с локалью для русских данных
fake_ru = Faker('ru_RU')
fake_en = Faker()

class TestDataGeneratorStates(StatesGroup):
    waiting_for_format = State()
    waiting_for_count = State()
    waiting_for_regenerate_choice = State()
    waiting_for_feature = State()
    waiting_for_payment_system = State()
    waiting_for_card_regenerate_choice = State()

# Платежные системы для генерации карт
PAYMENT_SYSTEMS = ['Visa', 'Mastercard', 'UnionPay', 'JCB', 'Mir']

async def generate_test_data_command(message: Message, state: FSMContext):
    """Начало работы с генератором тестовых данных"""
    await state.set_state(TestDataGeneratorStates.waiting_for_feature)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="💳 Банковская карта")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "👥 <b>Создать тестовые данные</b>\n\n"
        "Выбери, что нужно сгенерировать:\n"
        "• 👥 Пользователи\n"
        "• 💳 Банковская карта",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def process_feature_choice(message: Message, state: FSMContext):
    """Обработка выбора фичи генератора тестовых данных"""
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки", reply_markup=get_back_menu())
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    if message.text == "👥 Пользователи":
        await state.set_state(TestDataGeneratorStates.waiting_for_format)

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Текстовый формат")],
                [KeyboardButton(text="📊 JSON формат")],
                [KeyboardButton(text="Назад в меню")],
            ],
            resize_keyboard=True,
        )

        await message.answer(
            "👥 <b>Создание тестовых данных пользователей</b>\n\n"
            "Выбери формат вывода данных:",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    elif message.text == "💳 Банковская карта":
        # Показываем меню выбора платежной системы
        await show_payment_systems_menu(message, state)
    else:
        await message.answer("⚠ Пожалуйста, выбери вариант из списка")

async def process_format_choice(message: Message, state: FSMContext):
    """Обработка выбора формата"""
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    if message.text not in ["📝 Текстовый формат", "📊 JSON формат"]:
        await message.answer("⚠ Пожалуйста, выбери формат из списка")
        return
    
    # Сохраняем выбранный формат в состоянии
    await state.update_data(format=message.text)
    
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
        
        # Получаем выбранный формат из состояния
        data = await state.get_data()
        output_format = data.get('format', '📝 Текстовый формат')
        
        if output_format == "📊 JSON формат":
            await generate_and_show_users_json(message, state, count)
        else:
            await generate_and_show_users_text(message, state, count)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введи корректное число (от 1 до 50)")
    except Exception as e:
        logger.error(f"Test data generation error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при генерации данных", reply_markup=get_main_menu())
        await state.clear()

def generate_user_data():
    """Генерация данных одного пользователя"""
    # Генерация имени (русское)
    first_name = fake_ru.first_name()
    last_name = fake_ru.last_name()
    middle_name = fake_ru.middle_name()
    full_name = f"{last_name} {first_name} {middle_name}"
    
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
    
    # Генерация даты рождения (от 18 до 80 лет)
    end_date = datetime.now() - timedelta(days=18*365)
    start_date = datetime.now() - timedelta(days=80*365)
    birthdate = fake_en.date_between(start_date=start_date, end_date=end_date)
    
    # Генерация телефона (российский формат)
    phone = f"+7{fake_en.random_int(min=9000000000, max=9999999999)}"
    
    # Генерация пола (M/F)
    sex = random.choice(['M', 'F'])
    
    return {
        'name': full_name,
        'username': username,
        'mail': email,
        'password': password,
        'address': full_address,
        'birthdate': birthdate.strftime('%Y-%m-%d'),
        'phone': phone,
        'sex': sex
    }

async def generate_and_show_users_text(message: Message, state: FSMContext, count: int):
    """Генерация и отображение тестовых данных пользователей в текстовом формате"""
    try:
        users_data = []
        
        for i in range(count):
            user = generate_user_data()
            users_data.append(user)
        
        # Формирование сообщения
        result_text = f"👥 <b>Сгенерировано пользователей: {count}</b>\n\n"
        result_text += "═" * 50 + "\n\n"
        
        for idx, user in enumerate(users_data, 1):
            result_text += f"<b>👤 Пользователь #{idx}</b>\n"
            result_text += f"├ Имя: <code>{user['name']}</code>\n"
            result_text += f"├ Логин: <code>{user['username']}</code>\n"
            result_text += f"├ Email: <code>{user['mail']}</code>\n"
            result_text += f"├ Пароль: <code>{user['password']}</code>\n"
            result_text += f"├ Телефон: <code>{user['phone']}</code>\n"
            result_text += f"├ Дата рождения: <code>{user['birthdate']}</code>\n"
            result_text += f"├ Пол: <code>{user['sex']}</code>\n"
            result_text += f"└ Адрес: {user['address']}\n"
            
            if idx < len(users_data):
                result_text += "\n" + "─" * 50 + "\n\n"
        
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
                user_text += f"├ Email: <code>{user['mail']}</code>\n"
                user_text += f"├ Пароль: <code>{user['password']}</code>\n"
                user_text += f"├ Телефон: <code>{user['phone']}</code>\n"
                user_text += f"├ Дата рождения: <code>{user['birthdate']}</code>\n"
                user_text += f"├ Пол: <code>{user['sex']}</code>\n"
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
        logger.error(f"Error generating users text: {e}", exc_info=True)
        await message.answer("❌ Ошибка при генерации данных пользователей", reply_markup=get_main_menu())
        await state.clear()

async def generate_and_show_users_json(message: Message, state: FSMContext, count: int):
    """Генерация и отображение тестовых данных пользователей в JSON формате"""
    try:
        users_data = []
        
        for i in range(count):
            user = generate_user_data()
            users_data.append(user)
        
        # Формируем JSON
        json_data = json.dumps(users_data, ensure_ascii=False, indent=2)
        
        # Отправляем JSON
        await message.answer(
            f"👥 <b>Сгенерировано пользователей: {count}</b>\n"
            f"📊 <b>Формат: JSON</b>\n\n"
            "Данные готовы для использования в API тестах:",
            parse_mode="HTML"
        )
        
        # Отправляем JSON как отдельное сообщение
        await message.answer(f"<code>{json_data}</code>", parse_mode="HTML")
        
        await ask_for_regenerate(message, state)
        
    except Exception as e:
        logger.error(f"Error generating users JSON: {e}", exc_info=True)
        await message.answer("❌ Ошибка при генерации JSON данных", reply_markup=get_main_menu())
        await state.clear()

async def ask_for_regenerate(message: Message, state: FSMContext):
    """Запрос на повторную генерацию"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Создать еще"), KeyboardButton(text="⬅ Вернуться к выбору фичи")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True
    )
    await message.answer("Хочешь создать еще тестовые данные?", reply_markup=keyboard)
    await state.set_state(TestDataGeneratorStates.waiting_for_regenerate_choice)

async def process_regenerate_choice(message: Message, state: FSMContext):
    """Обработка выбора повторной генерации"""
    if message.text == "✨ Создать еще":
        # Повторно генерируем пользователей в том же режиме
        await state.set_state(TestDataGeneratorStates.waiting_for_count)
        await message.answer(
            "👥 Введи количество пользователей для генерации (от 1 до 50):",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Назад в меню")]],
                resize_keyboard=True,
            ),
        )
    elif message.text == "⬅ Вернуться к выбору фичи":
        await generate_test_data_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Используй кнопки для выбора")

# ========== ФУНКЦИИ ДЛЯ БАНКОВСКИХ КАРТ ==========

async def show_payment_systems_menu(message: Message, state: FSMContext):
    """Показать меню выбора платежной системы"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=system)] for system in PAYMENT_SYSTEMS
        ] + [
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("💳 Выбери платежную систему для карты:", reply_markup=keyboard)
    await state.set_state(TestDataGeneratorStates.waiting_for_payment_system)

async def process_payment_system(message: Message, state: FSMContext):
    """Обработка выбора платежной системы"""
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    if message.text not in PAYMENT_SYSTEMS:
        await message.answer("⚠ Выбери платежную систему из списка")
        return
    
    try:
        await generate_and_show_card(message, state, message.text)
    except Exception as e:
        logger.error(f"Payment data error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при генерации данных карты", reply_markup=get_main_menu())
        await state.clear()

def generate_card_number(system: str) -> str:
    """Генерация номера карты с проверкой по алгоритму Луна"""
    prefixes = {
        'Visa': ['4'],
        'Mastercard': ['51', '52', '53', '54', '55'],
        'UnionPay': ['62'],
        'JCB': ['35'],
        'Mir': ['2']
    }
    prefix = random.choice(prefixes.get(system, ['4']))  # Fallback на Visa
    number = prefix
    while len(number) < 15:
        number += str(random.randint(0, 9))
    
    # Алгоритм Луна
    total = 0
    for i, digit in enumerate(number):
        digit = int(digit)
        if i % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    
    check_digit = (10 - (total % 10)) % 10
    return number + str(check_digit)

async def generate_and_show_card(message: Message, state: FSMContext, system: str):
    """Генерация и отображение тестовой банковской карты"""
    card_number = generate_card_number(system)
    expiry_date = f"{random.randint(1, 12):02d}/{random.randint(23, 30)}"
    cvv = f"{random.randint(0, 999):03d}"
    
    await message.answer(
        "💳 <b>Тестовая банковская карта:</b>\n\n"
        f"> <b>Платежная система:</b> {system}\n"
        f"> <b>Номер карты:</b> <code>{card_number}</code>\n"
        f"> <b>Срок действия:</b> {expiry_date}\n"
        f"> <b>CVV/CVC:</b> <code>{cvv}</code>\n\n"
        "<i>⚠️ Используй только для тестирования!</i>",
        parse_mode="HTML"
    )
    
    await ask_for_card_regenerate(message, state)

async def ask_for_card_regenerate(message: Message, state: FSMContext):
    """Запрос на повторную генерацию карты"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Создать еще карту")],
            [KeyboardButton(text="⬅ Вернуться к выбору фичи")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("Хочешь создать еще одну карту или вернуться к выбору?", reply_markup=keyboard)
    await state.set_state(TestDataGeneratorStates.waiting_for_card_regenerate_choice)

async def process_card_regenerate_choice(message: Message, state: FSMContext):
    """Обработка выбора повторной генерации карты"""
    if message.text == "💳 Создать еще карту":
        # Возвращаем пользователя к выбору платежной системы
        await show_payment_systems_menu(message, state)
    elif message.text == "⬅ Вернуться к выбору фичи":
        await generate_test_data_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Используй кнопки для выбора")

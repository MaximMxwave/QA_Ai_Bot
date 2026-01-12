from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import html
from messages import MENU_MSG, get_main_menu

logger = logging.getLogger(__name__)


class BugReportStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_steps = State()
    waiting_for_actual_result = State()
    waiting_for_expected_result = State()
    waiting_for_environment = State()
    waiting_for_severity = State()
    waiting_for_logs = State()
    waiting_for_curl = State()
    waiting_for_docs = State()
    waiting_for_choice = State()


SEVERITIES = ["Blocker", "Critical", "Medium", "Minor", "Trivial"]


async def bug_report_command(message: Message, state: FSMContext):
    """Начало создания баг-репорта"""
    await state.set_state(BugReportStates.waiting_for_title)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🐞 <b>Создание баг-репорта</b>\n\n"
        "Введи краткое название бага:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def process_bug_title(message: Message, state: FSMContext):
    """Обработка названия бага"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи название бага")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    await state.update_data(title=message.text)
    await state.set_state(BugReportStates.waiting_for_description)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📝 Опиши баг подробнее (что наблюдается):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard
    )


async def process_bug_description(message: Message, state: FSMContext):
    """Обработка описания бага"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи описание или нажми 'Пропустить'")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    description = "" if message.text == "Пропустить" else message.text
    await state.update_data(description=description)
    await state.set_state(BugReportStates.waiting_for_steps)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📌 Введи шаги для воспроизведения бага:\n"
        "(каждый шаг с новой строки или через точку с запятой)\n\n"
        "Пример:\n"
        "1. Открыть страницу входа\n"
        "2. Ввести некорректный логин\n"
        "3. Нажать 'Войти'",
        reply_markup=keyboard
    )


async def process_bug_steps(message: Message, state: FSMContext):
    """Обработка шагов воспроизведения"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи шаги воспроизведения")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    steps_text = message.text.strip()
    if ';' in steps_text:
        steps_list = [s.strip() for s in steps_text.split(';') if s.strip()]
    elif '\n' in steps_text:
        steps_list = [s.strip() for s in steps_text.split('\n') if s.strip()]
    else:
        steps_list = [steps_text] if steps_text else []

    formatted_steps = []
    for step in steps_list:
        step = step.lstrip("0123456789. ").strip()
        if step:
            formatted_steps.append(step)

    if not formatted_steps:
        await message.answer("❌ Пожалуйста, введи хотя бы один шаг воспроизведения")
        return

    await state.update_data(steps=formatted_steps)
    await state.set_state(BugReportStates.waiting_for_actual_result)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "⚠️ Введи фактический результат (что происходит на самом деле):",
        reply_markup=keyboard
    )


async def process_bug_actual_result(message: Message, state: FSMContext):
    """Обработка фактического результата"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи фактический результат")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    await state.update_data(actual_result=message.text)
    await state.set_state(BugReportStates.waiting_for_expected_result)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "✅ Введи ожидаемый результат (как должно работать):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard
    )


async def process_bug_expected_result(message: Message, state: FSMContext):
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
    await state.set_state(BugReportStates.waiting_for_environment)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "💻 Укажи окружение (браузер, ОС, версия приложения и т.п.):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard
    )


async def process_bug_environment(message: Message, state: FSMContext):
    """Обработка окружения"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи окружение или нажми 'Пропустить'")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    environment = "" if message.text == "Пропустить" else message.text
    await state.update_data(environment=environment)
    await state.set_state(BugReportStates.waiting_for_severity)

    severity_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=sev) for sev in SEVERITIES[:2]],
            [KeyboardButton(text=sev) for sev in SEVERITIES[2:]],
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🎯 Выбери приоритет бага:",
        reply_markup=severity_keyboard
    )


async def process_bug_severity(message: Message, state: FSMContext):
    """Обработка приоритета"""
    if not message.text:
        await message.answer("❌ Пожалуйста, выбери приоритет или нажми 'Пропустить'")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    severity = "" if message.text == "Пропустить" else message.text
    if severity and severity not in SEVERITIES:
        await message.answer("⚠️ Выбери приоритет из предложенных вариантов")
        return

    await state.update_data(severity=severity)

    # Переходим к логам
    await state.set_state(BugReportStates.waiting_for_logs)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📜 Вставь логи (если есть):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard
    )


async def process_bug_logs(message: Message, state: FSMContext):
    """Обработка логов"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи логи или нажми 'Пропустить'")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    logs = "" if message.text == "Пропустить" else message.text
    await state.update_data(logs=logs)
    await state.set_state(BugReportStates.waiting_for_curl)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🔗 Вставь ручку (cURL) для запроса, если есть:\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard
    )


async def process_bug_curl(message: Message, state: FSMContext):
    """Обработка ручки (cURL)"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи cURL или нажми 'Пропустить'")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    curl = "" if message.text == "Пропустить" else message.text
    await state.update_data(curl=curl)
    await state.set_state(BugReportStates.waiting_for_docs)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📚 Вставь ссылку на документацию/требования (если есть):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard
    )


async def process_bug_docs(message: Message, state: FSMContext):
    """Обработка ссылки на документацию"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи документацию или нажми 'Пропустить'")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    docs = "" if message.text == "Пропустить" else message.text
    await state.update_data(docs=docs)

    try:
        data = await state.get_data()
        report = generate_bug_report(data)

        await message.answer(
            report,
            parse_mode="HTML"
        )

        await ask_for_new_bug_report(message, state)

    except Exception as e:
        logger.error(f"Bug report generation error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при создании баг-репорта", reply_markup=get_main_menu())
        await state.clear()


def generate_bug_report(data: dict) -> str:
    """Генерация баг-репорта в формате HTML"""
    title = html.escape(str(data.get("title", "Не указано")))
    description = html.escape(str(data.get("description", "")))
    steps = data.get("steps", [])
    actual_result = html.escape(str(data.get("actual_result", "")))
    expected_result = html.escape(str(data.get("expected_result", "")))
    environment = html.escape(str(data.get("environment", "")))
    severity = html.escape(str(data.get("severity", "Не указана")))
    logs = html.escape(str(data.get("logs", "")))
    curl = html.escape(str(data.get("curl", "")))
    docs = html.escape(str(data.get("docs", "")))

    report = "<b>🐞 БАГ-РЕПОРТ</b>\n\n"
    report += f"<b>Заголовок:</b> {title}\n\n"

    if description:
        report += f"<b>Описание:</b>\n{description}\n\n"

    report += "<b>Шаги для воспроизведения:</b>\n"
    if steps:
        for i, step in enumerate(steps, 1):
            escaped_step = html.escape(str(step))
            report += f"{i}. {escaped_step}\n"
    else:
        report += "Не указаны\n"
    report += "\n"

    if actual_result:
        report += f"<b>Фактический результат:</b>\n{actual_result}\n\n"

    if expected_result:
        report += f"<b>Ожидаемый результат:</b>\n{expected_result}\n\n"

    if environment:
        report += f"<b>Окружение:</b>\n{environment}\n\n"

    if logs:
        report += f"<b>Логи:</b>\n{logs}\n\n"

    if curl:
        report += f"<b>Ручка (cURL):</b>\n{curl}\n\n"

    if docs:
        report += f"<b>Документация:</b>\n{docs}\n\n"

    report += f"<b>Приоритет:</b> {severity}\n"

    return report


async def ask_for_new_bug_report(message: Message, state: FSMContext):
    """Предложение создать новый баг-репорт"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Создать ещё баг-репорт")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Хочешь создать ещё один баг-репорт?",
        reply_markup=keyboard
    )
    await state.set_state(BugReportStates.waiting_for_choice)


async def handle_choice(message: Message, state: FSMContext):
    """Обработка выбора пользователя после создания баг-репорта"""
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return

    if message.text == "✨ Создать ещё баг-репорт":
        await bug_report_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Пожалуйста, используй кнопки")



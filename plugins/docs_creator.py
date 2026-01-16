from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import html
from messages import MENU_MSG, get_main_menu, get_back_menu

logger = logging.getLogger(__name__)


class DocsStates(StatesGroup):
    # Выбор типа документа
    waiting_for_type = State()

    # Тест-кейс
    tc_waiting_for_title = State()
    tc_waiting_for_description = State()
    tc_waiting_for_preconditions = State()
    tc_waiting_for_steps = State()
    tc_waiting_for_expected_result = State()
    tc_waiting_for_priority = State()
    tc_waiting_for_choice = State()

    # Баг-репорт
    bug_waiting_for_title = State()
    bug_waiting_for_description = State()
    bug_waiting_for_steps = State()
    bug_waiting_for_actual_result = State()
    bug_waiting_for_expected_result = State()
    bug_waiting_for_environment = State()
    bug_waiting_for_severity = State()
    bug_waiting_for_logs = State()
    bug_waiting_for_curl = State()
    bug_waiting_for_docs = State()
    bug_waiting_for_choice = State()

    # Чек-лист
    cl_waiting_for_title = State()
    cl_waiting_for_items = State()
    cl_waiting_for_choice = State()


TEST_CASE_PRIORITIES = ['Критический', 'Высокий', 'Средний', 'Низкий']
BUG_SEVERITIES = ["Blocker", "Critical", "Medium", "Minor", "Trivial"]


async def docs_command(message: Message, state: FSMContext):
    """Начало работы с созданием документации"""
    await state.set_state(DocsStates.waiting_for_type)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Тест-кейс")],
            [KeyboardButton(text="✅ Чек-лист")],
            [KeyboardButton(text="🐞 Баг-репорт")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "📝 <b>Создать документацию</b>\n\n"
        "Выбери, что нужно создать:\n"
        "• 📋 Тест-кейс\n"
        "• ✅ Чек-лист\n"
        "• 🐞 Баг-репорт",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ===== Общие хелперы =====

async def _check_back_to_menu(message: Message, state: FSMContext) -> bool:
    """Общий хелпер: обработка перехода назад в меню."""
    if not message.text:
        await message.answer("❌ Пожалуйста, введи текст", reply_markup=get_back_menu())
        return True

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return True

    return False


async def process_docs_type(message: Message, state: FSMContext):
    """Обработка выбора типа документа"""
    if await _check_back_to_menu(message, state):
        return

    text = message.text

    if text == "📋 Тест-кейс":
        await _start_test_case_flow(message, state)
    elif text == "🐞 Баг-репорт":
        await _start_bug_report_flow(message, state)
    elif text == "✅ Чек-лист":
        await _start_checklist_flow(message, state)
    else:
        await message.answer("⚠ Пожалуйста, выбери вариант из списка")


# ===== ТЕСТ-КЕЙС =====

async def _start_test_case_flow(message: Message, state: FSMContext):
    await state.set_state(DocsStates.tc_waiting_for_title)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад в меню")]],
        resize_keyboard=True,
    )

    await message.answer(
        "📋 <b>Создание тест-кейса</b>\n\n"
        "Введи название тест-кейса:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def tc_process_title(message: Message, state: FSMContext):
    if await _check_back_to_menu(message, state):
        return

    await state.update_data(tc_title=message.text)
    await state.set_state(DocsStates.tc_waiting_for_description)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "📝 Введи описание тест-кейса:\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard,
    )


async def tc_process_description(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи описание или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    description = "" if message.text == "Пропустить" else message.text
    await state.update_data(tc_description=description)
    await state.set_state(DocsStates.tc_waiting_for_preconditions)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "⚙️ Введи предусловия:\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard,
    )


async def tc_process_preconditions(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи предусловия или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    preconditions = "" if message.text == "Пропустить" else message.text
    await state.update_data(tc_preconditions=preconditions)
    await state.set_state(DocsStates.tc_waiting_for_steps)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад в меню")]],
        resize_keyboard=True,
    )

    await message.answer(
        "📌 Введи шаги тест-кейса:\n"
        "(каждый шаг с новой строки или через точку с запятой)\n\n"
        "Пример:\n"
        "1. Открыть приложение\n"
        "2. Ввести логин\n"
        "3. Ввести пароль\n"
        "4. Нажать 'Войти'",
        reply_markup=keyboard,
    )


async def tc_process_steps(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи шаги тест-кейса")
        return

    if await _check_back_to_menu(message, state):
        return

    steps_text = message.text.strip()
    if ";" in steps_text:
        steps_list = [s.strip() for s in steps_text.split(";") if s.strip()]
    elif "\n" in steps_text:
        steps_list = [s.strip() for s in steps_text.split("\n") if s.strip()]
    else:
        steps_list = [steps_text] if steps_text else []

    formatted_steps = []
    for step in steps_list:
        step = step.lstrip("0123456789. ").strip()
        if step:
            formatted_steps.append(step)

    if not formatted_steps:
        await message.answer("❌ Пожалуйста, введи хотя бы один шаг тест-кейса")
        return

    await state.update_data(tc_steps=formatted_steps)
    await state.set_state(DocsStates.tc_waiting_for_expected_result)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "✅ Введи ожидаемый результат:\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard,
    )


async def tc_process_expected_result(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи ожидаемый результат или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    expected_result = "" if message.text == "Пропустить" else message.text
    await state.update_data(tc_expected_result=expected_result)
    await state.set_state(DocsStates.tc_waiting_for_priority)

    priority_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=p) for p in TEST_CASE_PRIORITIES[:2]],
            [KeyboardButton(text=p) for p in TEST_CASE_PRIORITIES[2:]],
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "🎯 Выбери приоритет тест-кейса:",
        reply_markup=priority_keyboard,
    )


async def tc_process_priority(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, выбери приоритет или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    priority = "" if message.text == "Пропустить" else message.text
    if priority and priority not in TEST_CASE_PRIORITIES:
        await message.answer("⚠️ Выбери приоритет из предложенных вариантов")
        return

    await state.update_data(tc_priority=priority)

    try:
        data = await state.get_data()
        template = generate_test_case_template(data)

        await message.answer(template, parse_mode="HTML")
        await ask_for_new_test_case(message, state)
    except Exception as e:
        logger.error(f"Test case template generation error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при создании шаблона", reply_markup=get_main_menu())
        await state.clear()


def generate_test_case_template(data: dict) -> str:
    """Генерация тест-кейса в формате HTML"""
    title = html.escape(str(data.get("tc_title", "Не указано")))
    description = html.escape(str(data.get("tc_description", "")))
    preconditions = html.escape(str(data.get("tc_preconditions", "")))
    steps = data.get("tc_steps", [])
    expected_result = html.escape(str(data.get("tc_expected_result", "")))
    priority = html.escape(str(data.get("tc_priority", "Не указан")))

    template = "<b>📋 ТЕСТ-КЕЙС</b>\n\n"
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


async def ask_for_new_test_case(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Создать ещё тест-кейс")],
            [KeyboardButton(text="📝 Вернуться к выбору документа")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "Хочешь создать ещё один тест-кейс или выбрать другой тип документа?",
        reply_markup=keyboard,
    )
    await state.set_state(DocsStates.tc_waiting_for_choice)


async def tc_handle_choice(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return

    if message.text == "✨ Создать ещё тест-кейс":
        await _start_test_case_flow(message, state)
    elif message.text == "📝 Вернуться к выбору документа":
        await docs_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Пожалуйста, используй кнопки")


# ===== БАГ-РЕПОРТ =====

async def _start_bug_report_flow(message: Message, state: FSMContext):
    await state.set_state(DocsStates.bug_waiting_for_title)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад в меню")]],
        resize_keyboard=True,
    )

    await message.answer(
        "🐞 <b>Создание баг-репорта</b>\n\n"
        "Введи краткое название бага:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def bug_process_title(message: Message, state: FSMContext):
    if await _check_back_to_menu(message, state):
        return

    await state.update_data(bug_title=message.text)
    await state.set_state(DocsStates.bug_waiting_for_description)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "📝 Опиши баг подробнее (что наблюдается):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard,
    )


async def bug_process_description(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи описание или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    description = "" if message.text == "Пропустить" else message.text
    await state.update_data(bug_description=description)
    await state.set_state(DocsStates.bug_waiting_for_steps)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад в меню")]],
        resize_keyboard=True,
    )

    await message.answer(
        "📌 Введи шаги для воспроизведения бага:\n"
        "(каждый шаг с новой строки или через точку с запятой)\n\n"
        "Пример:\n"
        "1. Открыть страницу входа\n"
        "2. Ввести некорректный логин\n"
        "3. Нажать 'Войти'",
        reply_markup=keyboard,
    )


async def bug_process_steps(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи шаги воспроизведения")
        return

    if await _check_back_to_menu(message, state):
        return

    steps_text = message.text.strip()
    if ";" in steps_text:
        steps_list = [s.strip() for s in steps_text.split(";") if s.strip()]
    elif "\n" in steps_text:
        steps_list = [s.strip() for s in steps_text.split("\n") if s.strip()]
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

    await state.update_data(bug_steps=formatted_steps)
    await state.set_state(DocsStates.bug_waiting_for_actual_result)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад в меню")]],
        resize_keyboard=True,
    )

    await message.answer(
        "⚠️ Введи фактический результат (что происходит на самом деле):",
        reply_markup=keyboard,
    )


async def bug_process_actual_result(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи фактический результат")
        return

    if await _check_back_to_menu(message, state):
        return

    await state.update_data(bug_actual_result=message.text)
    await state.set_state(DocsStates.bug_waiting_for_expected_result)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "✅ Введи ожидаемый результат (как должно работать):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard,
    )


async def bug_process_expected_result(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи ожидаемый результат или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    expected_result = "" if message.text == "Пропустить" else message.text
    await state.update_data(bug_expected_result=expected_result)
    await state.set_state(DocsStates.bug_waiting_for_environment)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "💻 Укажи окружение (браузер, ОС, версия приложения и т.п.):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard,
    )


async def bug_process_environment(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи окружение или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    environment = "" if message.text == "Пропустить" else message.text
    await state.update_data(bug_environment=environment)
    await state.set_state(DocsStates.bug_waiting_for_severity)

    severity_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=s) for s in BUG_SEVERITIES[:2]],
            [KeyboardButton(text=s) for s in BUG_SEVERITIES[2:]],
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "🎯 Выбери приоритет бага:",
        reply_markup=severity_keyboard,
    )


async def bug_process_severity(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, выбери приоритет или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    severity = "" if message.text == "Пропустить" else message.text
    if severity and severity not in BUG_SEVERITIES:
        await message.answer("⚠️ Выбери приоритет из предложенных вариантов")
        return

    await state.update_data(bug_severity=severity)
    await state.set_state(DocsStates.bug_waiting_for_logs)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "📜 Вставь логи (если есть):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard,
    )


async def bug_process_logs(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи логи или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    logs = "" if message.text == "Пропустить" else message.text
    await state.update_data(bug_logs=logs)
    await state.set_state(DocsStates.bug_waiting_for_curl)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "🔗 Вставь ручку (cURL) для запроса, если есть:\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard,
    )


async def bug_process_curl(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи cURL или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    curl = "" if message.text == "Пропустить" else message.text
    await state.update_data(bug_curl=curl)
    await state.set_state(DocsStates.bug_waiting_for_docs)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "📚 Вставь ссылку на документацию/требования (если есть):\n"
        "(или нажми 'Пропустить', чтобы оставить пустым)",
        reply_markup=keyboard,
    )


async def bug_process_docs(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи документацию или нажми 'Пропустить'")
        return

    if await _check_back_to_menu(message, state):
        return

    docs = "" if message.text == "Пропустить" else message.text
    await state.update_data(bug_docs=docs)

    try:
        data = await state.get_data()
        report = generate_bug_report(data)

        await message.answer(report, parse_mode="HTML")
        await ask_for_new_bug_report(message, state)
    except Exception as e:
        logger.error(f"Bug report generation error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при создании баг-репорта", reply_markup=get_main_menu())
        await state.clear()


def generate_bug_report(data: dict) -> str:
    """Генерация баг-репорта в формате HTML"""
    title = html.escape(str(data.get("bug_title", "Не указано")))
    description = html.escape(str(data.get("bug_description", "")))
    steps = data.get("bug_steps", [])
    actual_result = html.escape(str(data.get("bug_actual_result", "")))
    expected_result = html.escape(str(data.get("bug_expected_result", "")))
    environment = html.escape(str(data.get("bug_environment", "")))
    severity = html.escape(str(data.get("bug_severity", "Не указана")))
    logs = html.escape(str(data.get("bug_logs", "")))
    curl = html.escape(str(data.get("bug_curl", "")))
    docs = html.escape(str(data.get("bug_docs", "")))

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
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Создать ещё баг-репорт")],
            [KeyboardButton(text="📝 Вернуться к выбору документа")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "Хочешь создать ещё один баг-репорт или выбрать другой тип документа?",
        reply_markup=keyboard,
    )
    await state.set_state(DocsStates.bug_waiting_for_choice)


async def bug_handle_choice(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return

    if message.text == "✨ Создать ещё баг-репорт":
        await _start_bug_report_flow(message, state)
    elif message.text == "📝 Вернуться к выбору документа":
        await docs_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Пожалуйста, используй кнопки")


# ===== ЧЕК-ЛИСТ =====

async def _start_checklist_flow(message: Message, state: FSMContext):
    await state.set_state(DocsStates.cl_waiting_for_title)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад в меню")]],
        resize_keyboard=True,
    )

    await message.answer(
        "✅ <b>Создание чек-листа</b>\n\n"
        "Введи название чек-листа:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def cl_process_title(message: Message, state: FSMContext):
    if await _check_back_to_menu(message, state):
        return

    await state.update_data(cl_title=message.text)
    await state.set_state(DocsStates.cl_waiting_for_items)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад в меню")]],
        resize_keyboard=True,
    )

    await message.answer(
        "📌 Введи пункты чек-листа:\n"
        "• каждый пункт с новой строки или через точку с запятой\n\n"
        "Пример:\n"
        "1. Открыть страницу логина\n"
        "2. Проверить валидацию полей\n"
        "3. Проверить сообщение об ошибке",
        reply_markup=keyboard,
    )


async def cl_process_items(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи пункты чек-листа")
        return

    if await _check_back_to_menu(message, state):
        return

    items_text = message.text.strip()
    if ";" in items_text:
        items_list = [s.strip() for s in items_text.split(";") if s.strip()]
    elif "\n" in items_text:
        items_list = [s.strip() for s in items_text.split("\n") if s.strip()]
    else:
        items_list = [items_text] if items_text else []

    formatted_items = []
    for item in items_list:
        item = item.lstrip("0123456789. ").strip()
        if item:
            formatted_items.append(item)

    if not formatted_items:
        await message.answer("❌ Пожалуйста, введи хотя бы один пункт чек-листа")
        return

    await state.update_data(cl_items=formatted_items)

    try:
        data = await state.get_data()
        checklist = generate_checklist_template(data)

        await message.answer(checklist, parse_mode="HTML")
        await ask_for_new_checklist(message, state)
    except Exception as e:
        logger.error(f"Checklist generation error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при создании чек-листа", reply_markup=get_main_menu())
        await state.clear()


def generate_checklist_template(data: dict) -> str:
    """Генерация чек-листа в формате HTML"""
    title = html.escape(str(data.get("cl_title", "Не указан")))
    items = data.get("cl_items", [])

    template = "<b>✅ ЧЕК-ЛИСТ</b>\n\n"
    template += f"<b>Название:</b> {title}\n\n"
    template += "<b>Пункты проверки:</b>\n"

    if items:
        for i, item in enumerate(items, 1):
            escaped_item = html.escape(str(item))
            template += f"[ ] {i}. {escaped_item}\n"
    else:
        template += "Не указаны\n"

    return template


async def ask_for_new_checklist(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Создать ещё чек-лист")],
            [KeyboardButton(text="📝 Вернуться к выбору документа")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "Хочешь создать ещё один чек-лист или выбрать другой тип документа?",
        reply_markup=keyboard,
    )
    await state.set_state(DocsStates.cl_waiting_for_choice)


async def cl_handle_choice(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return

    if message.text == "✨ Создать ещё чек-лист":
        await _start_checklist_flow(message, state)
    elif message.text == "📝 Вернуться к выбору документа":
        await docs_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Пожалуйста, используй кнопки")


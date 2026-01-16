from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from messages import MENU_MSG, get_main_menu, get_back_menu

logger = logging.getLogger(__name__)


class SqlGeneratorStates(StatesGroup):
    waiting_for_type = State()
    waiting_for_table_name = State()
    waiting_for_columns = State()
    waiting_for_where = State()
    waiting_for_limit = State()
    waiting_for_choice = State()


SQL_TYPES = ["SELECT", "INSERT", "UPDATE", "DELETE"]


async def sql_generator_command(message: Message, state: FSMContext):
    """Начало работы с генератором SQL"""
    await state.set_state(SqlGeneratorStates.waiting_for_type)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="SELECT"), KeyboardButton(text="INSERT")],
            [KeyboardButton(text="UPDATE"), KeyboardButton(text="DELETE")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "🗃 <b>Сгенерировать SQL</b>\n\n"
        "Выбери тип запроса:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def process_sql_type(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, выбери тип запроса", reply_markup=get_back_menu())
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    if message.text not in SQL_TYPES:
        await message.answer("⚠ Пожалуйста, выбери тип запроса из списка")
        return

    await state.update_data(sql_type=message.text)
    await state.set_state(SqlGeneratorStates.waiting_for_table_name)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад в меню")]],
        resize_keyboard=True,
    )

    await message.answer(
        "📄 Введи название таблицы (например, users):",
        reply_markup=keyboard,
    )


async def process_table_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи название таблицы")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    await state.update_data(table=message.text.strip())

    data = await state.get_data()
    sql_type = data.get("sql_type", "SELECT")

    # Для SELECT и DELETE спрашиваем колонки/WHERE, для INSERT/UPDATE — колонки и значения
    await state.set_state(SqlGeneratorStates.waiting_for_columns)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="*")], [KeyboardButton(text="Назад в меню")]],
        resize_keyboard=True,
    )

    if sql_type == "SELECT":
        desc = (
            "📌 Введи список колонок через запятую\n"
            "Пример: id, name, email\n\n"
            "Или отправь * чтобы выбрать все колонки"
        )
    elif sql_type == "INSERT":
        desc = (
            "📌 Введи список колонок через запятую\n"
            "Пример: name, email, password"
        )
    elif sql_type == "UPDATE":
        desc = (
            "📌 Введи список колонок и значений\n"
            "Формат: column=value, column2=value2\n"
            "Пример: name='Alex', is_active=1"
        )
    else:  # DELETE
        desc = "📌 Колонки можно пропустить, сразу перейдём к WHERE-условию.\nОтправь * чтобы пропустить."

    await message.answer(desc, reply_markup=keyboard)


async def process_columns(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи колонки или *")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    cols = message.text.strip()
    await state.update_data(columns=cols)

    data = await state.get_data()
    sql_type = data.get("sql_type", "SELECT")

    # WHERE и LIMIT нужны только для SELECT/UPDATE/DELETE
    if sql_type in ("SELECT", "UPDATE", "DELETE"):
        await state.set_state(SqlGeneratorStates.waiting_for_where)

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Без условия")],
                [KeyboardButton(text="Назад в меню")],
            ],
            resize_keyboard=True,
        )

        await message.answer(
            "🔎 Введи WHERE-условие (без слова WHERE)\n"
            "Пример: id = 1 AND is_active = 1\n\n"
            "Или нажми 'Без условия'",
            reply_markup=keyboard,
        )
    else:
        # INSERT: сразу генерируем SQL
        await generate_and_show_sql(message, state)


async def process_where(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи условие или выбери 'Без условия'")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    if message.text == "Без условия":
        where_clause = ""
    else:
        where_clause = message.text.strip()

    await state.update_data(where=where_clause)

    data = await state.get_data()
    sql_type = data.get("sql_type", "SELECT")

    if sql_type == "SELECT":
        await state.set_state(SqlGeneratorStates.waiting_for_limit)

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Без LIMIT")],
                [KeyboardButton(text="10"), KeyboardButton(text="100")],
                [KeyboardButton(text="Назад в меню")],
            ],
            resize_keyboard=True,
        )

        await message.answer(
            "📏 Введи LIMIT (кол-во записей) или выбери вариант",
            reply_markup=keyboard,
        )
    else:
        await generate_and_show_sql(message, state)


async def process_limit(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введи LIMIT или выбери 'Без LIMIT'")
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return

    if message.text == "Без LIMIT":
        limit_clause = ""
    else:
        limit_clause = message.text.strip()

    await state.update_data(limit=limit_clause)

    await generate_and_show_sql(message, state)


async def generate_and_show_sql(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        sql_type = data.get("sql_type", "SELECT")
        table = data.get("table", "table_name")
        columns = data.get("columns", "*")
        where = data.get("where", "")
        limit = data.get("limit", "")

        sql = ""

        if sql_type == "SELECT":
            cols = "*" if columns.strip() == "*" else columns
            sql = f"SELECT {cols} FROM {table}"
            if where:
                sql += f" WHERE {where}"
            if limit:
                sql += f" LIMIT {limit}"
        elif sql_type == "INSERT":
            cols = columns
            sql = (
                f"INSERT INTO {table} ({cols})\n"
                f"VALUES (-- значения подставь здесь);"
            )
        elif sql_type == "UPDATE":
            set_part = columns
            sql = f"UPDATE {table} SET {set_part}"
            if where:
                sql += f" WHERE {where}"
        elif sql_type == "DELETE":
            sql = f"DELETE FROM {table}"
            if where:
                sql += f" WHERE {where}"
        else:
            sql = "-- Неподдерживаемый тип запроса"

        await message.answer(
            "🗃 <b>Сгенерированный SQL:</b>\n\n"
            f"<code>{sql}</code>",
            parse_mode="HTML",
        )

        await ask_for_new_sql(message, state)

    except Exception as e:
        logger.error(f"SQL generation error: {e}", exc_info=True)
        await message.answer("❌ Ошибка при генерации SQL", reply_markup=get_main_menu())
        await state.clear()


async def ask_for_new_sql(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Сгенерировать ещё SQL")],
            [KeyboardButton(text="Назад в меню")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "Хочешь сгенерировать ещё один SQL-запрос?",
        reply_markup=keyboard,
    )
    await state.set_state(SqlGeneratorStates.waiting_for_choice)


async def process_sql_choice(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return

    if message.text == "✨ Сгенерировать ещё SQL":
        await sql_generator_command(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Пожалуйста, используй кнопки")


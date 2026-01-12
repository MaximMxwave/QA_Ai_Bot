from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from allpairspy import AllPairs
import logging
from itertools import product
from messages import MENU_MSG, get_main_menu, get_back_menu

logger = logging.getLogger(__name__)

class PairwiseStates(StatesGroup):
    waiting_for_parameters = State()
    waiting_for_action = State()

async def pairwise_command(message: Message, state: FSMContext):
    await state.set_state(PairwiseStates.waiting_for_parameters)
    await message.answer(
        "🧪 Введи параметры для Pairwise тестирования в формате:\n"
        "<code>параметр1: значение1, значение2; параметр2: значение1, значение2</code>\n\n"
        "Пример:\n"
        "<code>os: mac, win; size: 1000, 1200; browser: chrome, firefox</code>\n\n"
        "Для возврата в меню нажми 'Назад в меню'",
        parse_mode="HTML",
        reply_markup=get_back_menu()
    )

async def process_pairwise_parameters(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текстовое сообщение", reply_markup=get_back_menu())
        return
        
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    try:
        parameters = {}
        input_text = message.text.strip()
        param_blocks = [block.strip() for block in input_text.split(';') if block.strip()]
        
        for block in param_blocks:
            if ':' not in block:
                await message.answer(
                    "❌ Ошибка формата. Используй 'параметр: значение1, значение2'",
                    reply_markup=get_back_menu()
                )
                return
                
            param_name, values_str = block.split(':', 1)
            param_name = param_name.strip()
            values = [v.strip() for v in values_str.split(',') if v.strip()]
            
            if not param_name or not values:
                await message.answer(
                    "❌ Ошибка: параметр и значения не могут быть пустыми",
                    reply_markup=get_back_menu()
                )
                return
                
            parameters[param_name] = values
        
        if len(parameters) < 2:
            await message.answer(
                "❌ Нужно минимум 2 параметра для pairwise тестирования",
                reply_markup=get_back_menu()
            )
            return
        
        pairwise_combinations = list(AllPairs(parameters.values()))
        # Вычисляем все комбинации один раз и сохраняем для дальнейшего использования
        all_combinations = list(product(*parameters.values()))
        all_combinations_count = len(all_combinations)
        
        await state.update_data(
            parameters=parameters,
            pairwise_combinations=pairwise_combinations,
            all_combinations=all_combinations,
            all_combinations_count=all_combinations_count
        )
        
        report = (
            f"🧪 <b>Pairwise тестирование</b>\n\n"
            f"<b>Параметры ({len(parameters)}):</b>\n" +
            "\n".join(f"• {param}: {', '.join(values)}" for param, values in parameters.items()) +
            f"\n\n<b>Оптимальное количество тестов:</b> {len(pairwise_combinations)} из {all_combinations_count}\n\n"
            f"<b>🧩 Оптимальные тесты:</b>\n" +
            "\n".join(
                f"{i}. " + ", ".join(f"{param}: {value}" for param, value in zip(parameters.keys(), combo))
                for i, combo in enumerate(pairwise_combinations, 1)
            )
        )
        
        await message.answer(report, parse_mode="HTML")
        
        action_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Показать полный список"), KeyboardButton(text="🧩 Показать оптимальные тесты")],
                [KeyboardButton(text="Проверить другие параметры")],
                [KeyboardButton(text="Назад в меню")]
            ],
            resize_keyboard=True
        )
        
        await message.answer("Выбери действие:", reply_markup=action_keyboard)
        await state.set_state(PairwiseStates.waiting_for_action)
        
    except Exception as e:
        logger.error(f"Pairwise error: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка при обработке параметров. Проверьте формат ввода.",
            reply_markup=get_back_menu()
        )
        await state.clear()

async def process_pairwise_action(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, используй предложенные кнопки")
        return
        
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    data = await state.get_data()
    parameters = data['parameters']
    pairwise_combinations = data['pairwise_combinations']
    all_combinations = data.get('all_combinations')
    all_combinations_count = data['all_combinations_count']
    
    # Если полные комбинации не сохранены, вычисляем их
    if all_combinations is None:
        all_combinations = list(product(*parameters.values()))
        await state.update_data(all_combinations=all_combinations)
    
    if message.text == "Проверить другие параметры":
        await pairwise_command(message, state)
        return
    
    elif message.text == "📋 Показать полный список":
        
        report = (
            f"📋 <b>Полный список комбинаций ({len(all_combinations)}):</b>\n\n" +
            "\n".join(
                f"{i}. " + ", ".join(f"{param}: {value}" for param, value in zip(parameters.keys(), combo))
                for i, combo in enumerate(all_combinations, 1)
            )
        )
        
        # Разбиваем длинное сообщение на части, учитывая лимит Telegram (4096 символов)
        max_length = 4000
        if len(report) > max_length:
            # Разбиваем по строкам, чтобы не разрывать HTML
            lines = report.split('\n')
            current_chunk = ""
            for line in lines:
                if len(current_chunk) + len(line) + 1 > max_length:
                    if current_chunk:
                        await message.answer(current_chunk, parse_mode="HTML")
                    current_chunk = line + '\n'
                else:
                    current_chunk += line + '\n'
            if current_chunk:
                await message.answer(current_chunk, parse_mode="HTML")
        else:
            await message.answer(report, parse_mode="HTML")
        
    elif message.text == "🧩 Показать оптимальные тесты":
        report = (
            f"🧩 <b>Оптимальные тесты ({len(pairwise_combinations)} из {all_combinations_count}):</b>\n\n" +
            "\n".join(
                f"{i}. " + ", ".join(f"{param}: {value}" for param, value in zip(parameters.keys(), combo))
                for i, combo in enumerate(pairwise_combinations, 1)
            )
        )
        # Разбиваем длинное сообщение на части
        max_length = 4000
        if len(report) > max_length:
            lines = report.split('\n')
            current_chunk = ""
            for line in lines:
                if len(current_chunk) + len(line) + 1 > max_length:
                    if current_chunk:
                        await message.answer(current_chunk, parse_mode="HTML")
                    current_chunk = line + '\n'
                else:
                    current_chunk += line + '\n'
            if current_chunk:
                await message.answer(current_chunk, parse_mode="HTML")
        else:
            await message.answer(report, parse_mode="HTML")
    
    else:
        await message.answer("Используй предложенные кнопки")
        return
    
    # Только если нужно продолжить, покажем меню
    if message.text in ["📋 Показать полный список", "🧩 Показать оптимальные тесты"]:
        action_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Показать полный список"), KeyboardButton(text="🧩 Показать оптимальные тесты")],
                [KeyboardButton(text="Проверить другие параметры")],
                [KeyboardButton(text="Назад в меню")]
            ],
            resize_keyboard=True
        )
        await message.answer("Выбери действие:", reply_markup=action_keyboard)

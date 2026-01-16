from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
import asyncio
import json
import time
import logging
import html
import re
from urllib.parse import urlparse
from messages import MENU_MSG, get_main_menu, get_back_menu

logger = logging.getLogger(__name__)

class ApiValidatorStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_validate_choice = State()

def escape_html_for_telegram(text: str) -> str:
    """Экранирует HTML-теги и специальные символы для безопасной отправки в Telegram"""
    if not text:
        return text
    # Экранируем специальные символы HTML
    text = html.escape(text)
    # Дополнительно экранируем символы, которые могут вызвать проблемы в Telegram
    # Но оставляем уже экранированные теги как есть
    return text

HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']

async def api_validator_command(message: Message, state: FSMContext):
    await show_url_input_menu(message, state)

async def show_url_input_menu(message: Message, state: FSMContext):
    builder = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "🔍 <b>Валидатор API</b>\n\n"
        "Отправь мне URL для проверки:\n"
        "• <code>https://jsonplaceholder.typicode.com/posts/1</code>\n"
        "• <code>https://api.github.com/users/octocat</code>\n\n"
        "Также можно указать метод:\n"
        "• <code>POST https://api.example.com/users</code>\n"
        "• <code>GET https://api.example.com/data</code>\n\n"
        "Поддерживаемые методы: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS\n\n"
        "💡 <i>Указывай конкретные endpoints, а не корневые URL</i>",
        parse_mode="HTML",
        reply_markup=builder
    )
    await state.set_state(ApiValidatorStates.waiting_for_url)

async def process_api_validation(message: Message, state: FSMContext):
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
        return
    
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь URL для проверки", reply_markup=get_back_menu())
        return
    
    try:
        input_text = message.text.strip()
        logger.info(f"Processing API validation request: {input_text}")
        
        # Парсим метод и URL
        parts = input_text.split(maxsplit=1)
        if len(parts) == 2 and parts[0].upper() in HTTP_METHODS:
            method = parts[0].upper()
            url = parts[1]
        else:
            method = 'GET'
            url = input_text
        
        # Валидация и нормализация URL
        parsed_url = urlparse(url)
        
        # Если нет схемы, добавляем https://
        if not parsed_url.scheme:
            url = f"https://{url}"
            parsed_url = urlparse(url)
            logger.info(f"Added https:// scheme to URL: {url}")
        
        # Проверяем, что есть домен
        if not parsed_url.netloc:
            await message.answer(
                "❌ <b>Некорректный URL</b>\n\n"
                "Примеры правильных URL:\n"
                "• <code>https://api.example.com/users</code>\n"
                "• <code>http://localhost:3000/api/data</code>\n"
                "• <code>api.example.com</code> (автоматически добавится https://)",
                parse_mode="HTML"
            )
            return
        
        # Используем нормализованный URL
        logger.info(f"Final URL after validation: {url}, method: {method}")
        
        # Делаем запрос
        await message.answer("⏳ Выполняю запрос...")
        
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method, url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response_time = round((time.time() - start_time) * 1000, 2)  # в миллисекундах
                    
                    # Пытаемся сначала прочитать как JSON, если не получится - читаем как текст
                    is_json = False
                    json_data = None
                    formatted_json = None
                    response_text = None
                    
                    # Проверяем Content-Type для определения формата
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    # Пытаемся прочитать как JSON
                    try:
                        # Читаем байты, чтобы можно было попробовать и JSON и текст
                        # Ограничиваем размер ответа до 5MB для безопасности
                        max_size = 5 * 1024 * 1024  # 5MB
                        raw_data = await response.read()
                        
                        if len(raw_data) > max_size:
                            response_text = f"[Ответ слишком большой: {len(raw_data)} байт (максимум {max_size} байт)]"
                            logger.warning(f"Response too large: {len(raw_data)} bytes for URL {url}")
                        else:
                            # Пытаемся распарсить как JSON
                            try:
                                decoded_text = raw_data.decode('utf-8')
                                json_data = json.loads(decoded_text)
                                is_json = True
                                formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
                                response_text = decoded_text
                            except (json.JSONDecodeError, UnicodeDecodeError) as json_err:
                                # Если не JSON, читаем как текст
                                try:
                                    response_text = raw_data.decode('utf-8')
                                except UnicodeDecodeError:
                                    response_text = f"[Бинарные данные, размер: {len(raw_data)} байт]"
                    except Exception as e:
                        logger.error(f"Error reading response body for URL {url}: {e}", exc_info=True)
                        response_text = f"[Ошибка при чтении тела ответа: {str(e)}]"
                    
                    # Формируем результат
                    status_emoji = "✅" if 200 <= response.status < 300 else "⚠️" if 300 <= response.status < 400 else "❌"
                    status_text = "Успешно" if 200 <= response.status < 300 else "Перенаправление" if 300 <= response.status < 400 else "Ошибка"
                    
                    result = (
                        f"{status_emoji} <b>Результат проверки API:</b>\n\n"
                        f"> <b>URL:</b> <code>{url}</code>\n"
                        f"> <b>Метод:</b> <code>{method}</code>\n"
                        f"> <b>Статус:</b> <code>{response.status}</code> {status_text}\n"
                        f"> <b>Время ответа:</b> {response_time} мс\n\n"
                    )
                    
                    # Добавляем информацию о заголовках
                    content_type_header = response.headers.get('Content-Type', 'Не указан')
                    result += f"> <b>Content-Type:</b> <code>{content_type_header}</code>\n"
                    
                    if is_json:
                        result += f"> <b>Формат:</b> JSON ✅\n\n"
                        result += f"<b>📑 Тело ответа (JSON):</b>\n"
                        # Экранируем HTML-теги в JSON (на случай если в данных есть HTML)
                        escaped_json = escape_html_for_telegram(formatted_json)
                        # Ограничиваем длину JSON для отображения
                        if len(escaped_json) > 2000:
                            result += f"<code>{escaped_json[:2000]}...</code>\n"
                            result += f"\n<i>(Показаны первые 2000 символов из {len(escaped_json)})</i>"
                        else:
                            result += f"<code>{escaped_json}</code>"
                    else:
                        result += f"> <b>Формат:</b> Не JSON\n\n"
                        if response_text and len(response_text.strip()) > 0:
                            result += f"<b>📄 Тело ответа:</b>\n"
                            # Экранируем HTML-теги в тексте ответа
                            escaped_text = escape_html_for_telegram(response_text)
                            if len(escaped_text) > 1000:
                                result += f"<code>{escaped_text[:1000]}...</code>\n"
                                result += f"\n<i>(Показаны первые 1000 символов из {len(escaped_text)})</i>"
                            else:
                                result += f"<code>{escaped_text}</code>"
                        else:
                            result += f"<b>📄 Тело ответа:</b> <i>Пусто</i>"
                    
                    # Добавляем важные заголовки
                    important_headers = ['Server', 'Date', 'Content-Length', 'Cache-Control', 'X-RateLimit-Limit']
                    headers_info = []
                    for header in important_headers:
                        if header in response.headers:
                            headers_info.append(f"• <b>{header}:</b> <code>{response.headers[header]}</code>")
                    
                    if headers_info:
                        result += f"\n\n<b>📋 Важные заголовки:</b>\n" + "\n".join(headers_info)
                    
                    logger.info(f"Successfully processed API request for {url}: status={response.status}, response_time={response_time}ms, is_json={is_json}")
                    
                    # Пытаемся отправить с HTML-парсингом, если не получается - отправляем без парсинга
                    try:
                        await message.answer(result, parse_mode="HTML")
                    except Exception as telegram_error:
                        logger.error(f"Telegram parse error: {telegram_error}", exc_info=True)
                        # Если ошибка парсинга HTML, отправляем без форматирования
                        # Убираем HTML-теги из результата
                        plain_result = re.sub(r'<[^>]+>', '', result)
                        plain_result = html.unescape(plain_result)
                        await message.answer(
                            f"⚠️ <b>Результат проверки API (без форматирования):</b>\n\n"
                            f"{plain_result[:4000]}",
                            parse_mode="HTML"
                        )
                    
                    await ask_for_validate_again(message, state)
                    
            except (aiohttp.ServerTimeoutError, asyncio.TimeoutError) as e:
                logger.error(f"Timeout error for URL {url}: {e}", exc_info=True)
                await message.answer(
                    "⏱ <b>Таймаут запроса</b>\n\n"
                    "Сервер не ответил в течение 30 секунд.\n\n"
                    f"<b>Ошибка:</b> {str(e)}",
                    parse_mode="HTML"
                )
                await ask_for_validate_again(message, state)
                
            except aiohttp.ClientConnectorError as e:
                logger.error(f"Connection error for URL {url}: {e}", exc_info=True)
                error_details = str(e)
                
                # Проверяем, является ли это DNS ошибкой
                dns_hint = ""
                if "Name or service not known" in error_details or "nodename nor servname provided" in error_details:
                    dns_hint = (
                        "\n\n<b>💡 Подсказка:</b>\n"
                        "Проверь правильность домена. Попробуй:\n"
                        "• Убедиться, что домен написан правильно\n"
                        "• Попробовать добавить 'www.' перед доменом\n"
                        "• Проверить, что домен существует"
                    )
                
                error_msg = (
                    "❌ <b>Ошибка подключения:</b>\n\n"
                    f"• <b>Сообщение:</b> <code>{html.escape(error_details)}</code>\n\n"
                    f"<b>Возможные причины:</b>\n"
                    "• Сервер недоступен\n"
                    "• Неверный URL или домен\n"
                    "• Проблемы с DNS\n"
                    "• Блокировка файрволом"
                    f"{dns_hint}"
                )
                await message.answer(error_msg, parse_mode="HTML")
                await ask_for_validate_again(message, state)
                
            except aiohttp.ClientError as e:
                logger.error(f"Client error for URL {url}: {e}", exc_info=True)
                error_msg = (
                    "❌ <b>Ошибка при выполнении запроса:</b>\n\n"
                    f"• <b>Тип ошибки:</b> {type(e).__name__}\n"
                    f"• <b>Сообщение:</b> {str(e)}\n\n"
                    f"<b>Возможные причины:</b>\n"
                    "• Неверный URL\n"
                    "• Сервер недоступен\n"
                    "• Проблемы с сетью\n"
                    "• SSL/TLS ошибки"
                )
                await message.answer(error_msg, parse_mode="HTML")
                await ask_for_validate_again(message, state)
                
    except Exception as e:
        logger.error(f"API validation error for input '{input_text}': {e}", exc_info=True)
        error_msg = str(e)
        
        # Проверяем, является ли это ошибкой парсинга Telegram
        if "can't parse entities" in error_msg or "Unsupported start tag" in error_msg:
            await message.answer(
                "❌ <b>Ошибка форматирования ответа</b>\n\n"
                "Ответ от API содержит HTML-теги, которые не могут быть обработаны.\n"
                "Попробуй указать конкретный endpoint API (например, /posts/1 вместо корневого URL).",
                parse_mode="HTML",
                reply_markup=get_back_menu()
            )
        else:
            await message.answer(
                f"❌ <b>Неизвестная ошибка при проверке API</b>\n\n"
                f"<b>Детали:</b> <code>{html.escape(error_msg)}</code>\n\n"
                "Проверь правильность URL и попробуй снова.",
                parse_mode="HTML",
                reply_markup=get_back_menu()
            )
        await ask_for_validate_again(message, state)

async def ask_for_validate_again(message: Message, state: FSMContext):
    builder = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Проверить еще")],
            [KeyboardButton(text="Назад в меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("Хочешь проверить еще один API?", reply_markup=builder)
    await state.set_state(ApiValidatorStates.waiting_for_validate_choice)

async def process_validate_choice(message: Message, state: FSMContext):
    if message.text == "✨ Проверить еще":
        await show_url_input_menu(message, state)
    elif message.text == "Назад в меню":
        await state.clear()
        await message.answer(MENU_MSG, reply_markup=get_main_menu())
    else:
        await message.answer("Используй кнопки")

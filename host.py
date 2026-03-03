import os
import logging
import subprocess
import time
import re
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация через переменные окружения (Bothost их поддерживает)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8543292422:AAEf66fuoePuO8VYW2kxJv3tHIlg7i_4Mqk")
JAR_FILE = "atlassian-agent.jar"
CHECK_FILE_NAME = "check"
SEPARATOR = "(Don't copy this line!!!): "

# Email и ServerID тоже можно вынести в переменные окружения
EMAIL = os.environ.get("EMAIL", "asmirnov2@renins.com")
SERVER_ID = os.environ.get("SERVER_ID", "BL0D-VDDA-1108-VLMH")

def escape_markdown(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def extract_activation_code(check_content: str) -> str:
    if not check_content:
        return ""
    
    if SEPARATOR in check_content:
        code_part = check_content.split(SEPARATOR, 1)[1]
        code_part = code_part.strip()
        cleaned_code = code_part.replace(" ", "").replace("\t", "").replace("\r", "").replace("\n", "")
        
        import string
        valid_chars = string.ascii_letters + string.digits + "+/="
        cleaned_code = ''.join([c for c in cleaned_code if c in valid_chars])
        
        if cleaned_code:
            return cleaned_code
    
    all_content_clean = check_content.replace(" ", "").replace("\t", "").replace("\r", "").replace("\n", "")
    base64_pattern = r'[A-Za-z0-9+/=]{100,}'
    matches = re.findall(base64_pattern, all_content_clean)
    
    if matches:
        return max(matches, key=len)
    
    return ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "👋 Привет\\! Я бот для активации плагинов\\.\n\n🚀 Отправь ключ плагина для активации\\!"
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN_V2)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "ℹ️ *Помощь по использованию бота\\:*\n\n"
        "1\\. Отправьте ключ плагина\n"
        "2\\. Бот выполнит Java активатор с вашим ключом\n"
        "3\\. Отправит вам код активации\n\n"
        "*Команды\\:*\n"
        "/start \\- Начать\n"
        "/help \\- Справка\n"
        "/status \\- Проверить Java и файлы"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN_V2)

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_text = "*📊 Статус\\:*\n\n"
    
    # Проверяем Java
    try:
        java_version = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if java_version.returncode == 0:
            status_text += "✅ *Java:* установлена\n"
        else:
            status_text += "❌ *Java:* НЕ установлена\n"
    except:
        status_text += "❌ *Java:* НЕ найдена\n"
    
    # Проверяем jar
    jar_path = Path(JAR_FILE)
    if jar_path.exists():
        status_text += f"✅ *JAR файл:* найден ({jar_path.stat().st_size} байт)\n"
    else:
        status_text += f"❌ *JAR файл:* {JAR_FILE} не найден\\!\n"
    
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN_V2)

def run_java_activation(plugin_key: str):
    jar_path = Path(JAR_FILE)
    check_file_path = Path(CHECK_FILE_NAME)
    
    if not jar_path.exists():
        return False, "", f"JAR файл не найден: {jar_path}"
    
    try:
        if check_file_path.exists():
            check_file_path.unlink()
        
        cmd = [
            'java', '-jar', str(jar_path),
            '-m', EMAIL,
            '-d',
            '-o', 'Putin',
            '-p', plugin_key,
            '-s', SERVER_ID
        ]
        
        logger.info(f"Запуск Java: {' '.join(cmd)}")
        
        with open(check_file_path, 'w') as outfile:
            result = subprocess.run(cmd, stdout=outfile, stderr=subprocess.PIPE, timeout=30)
        
        time.sleep(1)
        
        if check_file_path.exists():
            with open(check_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                check_content = f.read()
            
            activation_code = extract_activation_code(check_content)
            
            if activation_code:
                return True, activation_code, ""
            else:
                preview = check_content[:500]
                return False, "", f"Код не найден. Содержимое файла:\n{preview}"
        else:
            return False, "", "Файл check не создан"
            
    except subprocess.TimeoutExpired:
        return False, "", "Таймаут при выполнении Java"
    except Exception as e:
        return False, "", f"Ошибка: {str(e)}"

async def handle_plugin_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plugin_key = update.message.text.strip()
    
    if not plugin_key:
        await update.message.reply_text("❌ Отправьте ключ плагина")
        return
    
    processing_msg = await update.message.reply_text(
        f"⏳ *Обработка ключа:* `{escape_markdown(plugin_key)}`\n"
        f"🔄 Запуск Java активатора\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    
    try:
        success, activation_code, error = run_java_activation(plugin_key)
        
        if success and activation_code:
            code_length = len(activation_code)
            
            result_text = (
                f"✅ *Активация успешна\\!*\n\n"
                f"🔑 *Ключ:* `{escape_markdown(plugin_key)}`\n"
                f"🔓 *КОД АКТИВАЦИИ:*\n"
                f"```\n{activation_code}\n```\n"
                f"📏 *Длина:* {code_length} символов"
            )
            
            await processing_msg.edit_text(result_text, parse_mode=ParseMode.MARKDOWN_V2)
            
        else:
            error_text = (
                f"❌ *Ошибка активации*\n\n"
                f"🔑 *Ключ:* `{escape_markdown(plugin_key)}`\n"
                f"📋 *Ошибка:*\n```\n{escape_markdown(error[:1000])}\n```"
            )
            await processing_msg.edit_text(error_text, parse_mode=ParseMode.MARKDOWN_V2)
            
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ *Критическая ошибка:*\n`{escape_markdown(str(e)[:200])}`",
            parse_mode=ParseMode.MARKDOWN_V2
        )

def main():
    print("🚀 Бот запускается на платформе Bothost...")
    
    # Проверяем Java
    try:
        subprocess.run(['java', '-version'], capture_output=True, check=True)
        print("✅ Java доступна")
    except:
        print("❌ Java не найдена! Бот не сможет работать.")
    
    jar_path = Path(JAR_FILE)
    if jar_path.exists():
        print(f"✅ JAR файл найден: {JAR_FILE}")
    else:
        print(f"⚠️ ВНИМАНИЕ: {JAR_FILE} отсутствует!")
    
    # Важно: Bothost автоматически добавит переменные окружения
    print(f"✅ Токен бота: {'загружен' if BOT_TOKEN else 'ОТСУТСТВУЕТ!'}")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", check_status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plugin_request))
    
    print("✅ Бот готов к работе!")
    application.run_polling()

if __name__ == '__main__':
    main()
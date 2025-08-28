import os, subprocess, tempfile, random
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_TOKENS = os.getenv("GEMINI_TOKENS", "").split(",")
user_requests = {}

def pick_token():
    return random.choice([t.strip() for t in GEMINI_TOKENS if t.strip()])

def process_with_gemini(prompt, input_path, output_path):
    token = pick_token()
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = token

    cmd = ["gemini", "ask", f"{prompt} + tài liệu trong file", "--file", input_path]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)

    # luôn ghi stdout vào file output
    if result.stdout.strip():
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
    elif result.stderr.strip():
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("Error:\n" + result.stderr)
    return output_path

async def ai_command(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Dùng: /ai <yêu cầu>\nVD: /ai sửa code này")
        return
    prompt = " ".join(context.args)
    user_requests[update.message.from_user.id] = prompt
    await update.message.reply_text(f"Đã ghi nhận yêu cầu: {prompt}\nGửi file (.txt, .js, .py)")

async def handle_file(update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    doc = update.message.document
    filename = doc.file_name.lower()

    if not (filename.endswith(".txt") or filename.endswith(".js") or filename.endswith(".py")):
        await update.message.reply_text("Chỉ hỗ trợ file .txt, .js, .py")
        return

    if uid not in user_requests:
        await update.message.reply_text("Hãy dùng /ai <yêu cầu> trước khi gửi file.")
        return

    prompt = user_requests.pop(uid)
    file = await doc.get_file()

    with tempfile.NamedTemporaryFile(delete=False) as tmp_in:
        await file.download_to_drive(custom_path=tmp_in.name)
        input_path = tmp_in.name

    base, ext = os.path.splitext(filename)
    output_filename = f"{base}_ai{ext}"
    output_path = tempfile.NamedTemporaryFile(delete=False).name

    await update.message.reply_text(f"⏳ Đang xử lý: {prompt}")

    output_file = process_with_gemini(prompt, input_path, output_path)

    with open(output_file, "rb") as f:
        await update.message.reply_document(f, filename=output_filename)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.run_polling()

if __name__ == "__main__":
    main()

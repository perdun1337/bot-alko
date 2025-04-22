from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import logging

logging.basicConfig(level=logging.INFO)

# Этапы диалогов
(HARAKTERISTIKA_VOLUME, HARAKTERISTIKA_GRADUS, HARAKTERISTIKA_TIME,
 SMES_KOLVO, SMES_GRADUS, SMES_VOLUME,
 OTNOSHENIE_STRONG, OTNOSHENIE_WEAK, OTNOSHENIE_TARGET) = range(9)


# Сюда временно сохраняются данные пользователя
user_data_store = {}

# Главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ХАРАКТЕРИСТИКА", callback_data='harakteristika')],
        [InlineKeyboardButton("СМЕСЬ", callback_data='smes')],
        [InlineKeyboardButton("ОТНОШЕНИЕ", callback_data='otnoshenie')],
        [InlineKeyboardButton("КОКТЕЙЛИ", callback_data='kokteyli')]
    ]
    await update.message.reply_text(
        "Выберите опцию:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



# Обработка нажатия кнопок
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'harakteristika':
        await query.message.reply_text("Введите объем напитка (в литрах):", reply_markup=ReplyKeyboardRemove())
        return HARAKTERISTIKA_VOLUME

    elif choice == 'smes':
        keyboard = [[InlineKeyboardButton(str(i), callback_data=f"smes_{i}")] for i in range(2, 9)]
        await query.message.reply_text("Выберите количество напитков:", reply_markup=InlineKeyboardMarkup(keyboard))
        return SMES_KOLVO

    elif choice == 'otnoshenie':
        await query.message.reply_text("Введите градус крепкого напитка:")
        return OTNOSHENIE_STRONG

    elif choice == 'kokteyli':
        await query.message.reply_text("t.me/AlcosofiaCocktailsBot")

# ХАРАКТЕРИСТИКА
async def harakteristika_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['volume'] = float(update.message.text)
    await update.message.reply_text("Введите градус напитка:")
    return HARAKTERISTIKA_GRADUS

async def harakteristika_gradus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['gradus'] = float(update.message.text)
    await update.message.reply_text("Введите время (в часах):")
    return HARAKTERISTIKA_TIME

async def harakteristika_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time = float(update.message.text)
    volume = context.user_data['volume']
    gradus = context.user_data['gradus']
    result = (volume * gradus) / time
    await update.message.reply_text(f"Въеб: {round(result, 2)} Ананасовых")
    return ConversationHandler.END

# СМЕСЬ
async def smes_kolvo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kolvo = int(query.data.split("_")[1])
    context.user_data['smes_kolvo'] = kolvo
    context.user_data['smes_index'] = 1
    context.user_data['smes_list'] = []
    await query.message.reply_text(f"Введите градус 1 напитка:")
    return SMES_GRADUS

async def smes_gradus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gradus = float(update.message.text)
    context.user_data['current_gradus'] = gradus
    await update.message.reply_text(f"Введите объем {context.user_data['smes_index']} напитка (в литрах):")
    return SMES_VOLUME

async def smes_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    volume = float(update.message.text)
    gradus = context.user_data['current_gradus']
    context.user_data['smes_list'].append((gradus, volume))
    context.user_data['smes_index'] += 1

    if context.user_data['smes_index'] <= context.user_data['smes_kolvo']:
        await update.message.reply_text(f"Введите градус {context.user_data['smes_index']} напитка:")
        return SMES_GRADUS
    else:
        total_volume = sum(v for _, v in context.user_data['smes_list'])
        total_alcohol = sum(g * v for g, v in context.user_data['smes_list'])
        avg_gradus = total_alcohol / total_volume
        await update.message.reply_text(f"Общий объем: {round(total_volume, 2)} л\nСредний градус: {round(avg_gradus, 2)}°")
        return ConversationHandler.END

# ОТНОШЕНИЕ
async def otnoshenie_strong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['strong'] = float(update.message.text)
    await update.message.reply_text("Введите градус слабого напитка:")
    return OTNOSHENIE_WEAK

async def otnoshenie_weak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['weak'] = float(update.message.text)
    await update.message.reply_text("Какой градус хотите получить?")
    return OTNOSHENIE_TARGET

async def otnoshenie_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = float(update.message.text)
    strong = context.user_data['strong']
    weak = context.user_data['weak']

    if strong == weak:
        await update.message.reply_text("Невозможно рассчитать — оба напитка имеют одинаковую крепость.")
    else:
        ratio = (strong - target) / (target - weak)
        await update.message.reply_text(
            f"На 1 часть {strong}-градусного напитка нужно примерно {round(ratio, 2)} частей {weak}-градусного напитка"
        )
    return ConversationHandler.END

# Сброс
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token("7733462257:AAHlnyaYA-hm9MSi5_x_D1n_IAaPY_fWkks").build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_buttons)
        ],
        states={
            HARAKTERISTIKA_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, harakteristika_volume)],
            HARAKTERISTIKA_GRADUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, harakteristika_gradus)],
            HARAKTERISTIKA_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, harakteristika_time)],

            SMES_KOLVO: [CallbackQueryHandler(smes_kolvo, pattern="^smes_")],
            SMES_GRADUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, smes_gradus)],
            SMES_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, smes_volume)],

            OTNOSHENIE_STRONG: [MessageHandler(filters.TEXT & ~filters.COMMAND, otnoshenie_strong)],
            OTNOSHENIE_WEAK: [MessageHandler(filters.TEXT & ~filters.COMMAND, otnoshenie_weak)],
            OTNOSHENIE_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, otnoshenie_target)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))


    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()

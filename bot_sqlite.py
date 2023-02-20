import time
import logging
import sqlite3
import os
from questions_demo import Questions

from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.environ.get('TOKEN')
quest = Questions()


class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect('traps.db')
        self.cur = self.conn.cursor()

        self.cur.execute("""CREATE TABLE IF NOT EXISTS bot_users(
                                                 chat_id int PRIMARY KEY,
                                                 is_passed int NOT NULL,
                                                 is_passing int NOT NULL,
                                                 question_index int NOT NULL,
                                                 answers varchar(100) NOT NULL);""")
        self.conn.commit()

        self.cur.execute("""CREATE TABLE IF NOT EXISTS questions(
                                                  id int PRIMARY KEY,
                                                  question varchar(200) NOT NULL)""")
        self.questions = self.get_questions()
        self.questions_count = len(list(self.questions))
        if self.questions_count == 0:
            self.insert_many_questions(quest.questions)
            self.questions = self.get_questions()

        self.questions_count = len(list(self.questions))

    def insert_many_questions(self, rows):
        self.cur.executemany("""INSERT INTO questions VALUES(?, ?);""", rows)
        self.conn.commit()

    def get_user(self, chat_id):
        query = f"""SELECT chat_id, is_passed, is_passing, question_index, answers 
                    FROM bot_users WHERE chat_id = {chat_id};"""
        self.cur.execute(query)
        user = self.cur.fetchone()

        if user is not None:
            return user

        user = (chat_id, False, False, 0, "")

        self.cur.execute("""INSERT INTO bot_users VALUES(?, ?, ?, ?, ?);""", user)
        self.conn.commit()

        return user

    def set_user(self, chat_id, is_passed=None, is_passing=None, question_index=None, answers=None):
        if is_passed is None:
            is_passed = 'is_passed'
        if is_passing is None:
            is_passing = 'is_passing'
        if question_index is None:
            question_index = 'question_index'
        if answers is None:
            answers = 'answers'
        print(f"""UPDATE bot_users 
                             SET is_passed={is_passed}, 
                                 is_passing={is_passing},
                                 question_index={question_index},
                                 answers={answers}
                             WHERE chat_id={chat_id};""")
        self.cur.execute(f"""UPDATE bot_users 
                             SET is_passed={is_passed}, 
                                 is_passing={is_passing},
                                 question_index={question_index},
                                 answers={answers}
                             WHERE chat_id={chat_id};""")
        self.conn.commit()

    def get_question(self, index):
        return self.questions[index][1]

    def get_questions(self):
        query = "SELECT id, question FROM questions;"
        self.cur.execute(query)
        result = self.cur.fetchall()
        return result


db = DataBase()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
menu_markup = types.InlineKeyboardMarkup()
menu_markup.add(types.InlineKeyboardButton(text="Начать тест", callback_data='new'))
menu_markup.add(types.InlineKeyboardButton(text="Продолжить тест", callback_data='continue'))
menu_markup.add(types.InlineKeyboardButton(text="Пройти тест заново", callback_data='restart'))
menu_markup.add(types.InlineKeyboardButton(text="Мои результаты", callback_data='results'))
menu_markup.add(types.InlineKeyboardButton(text="Справка", callback_data='info'))

enter_text = "Предлагаем вам пройти тест на Эмоциональные Ловушки.\n\n" +\
             "Ловушка — это закономерность в поведении, которая возникает в детстве и закрепляется на " +\
             "всю жизнь. Ловушки появляются из-за того, что с нами сделали родственники или другие " +\
             "дети. Кто-то нас бросал, критиковал, чрезмерно опекал, жестоко обошелся с нами, отверг " +\
             "или проигнорировал нас — то есть каким-то образом причинил нам вред.\n\n" +\
             "Даже покинув дом своего детства, мы продолжаем воспроизводить ситуации, в которых с " +\
             "нами дурно обращаются, игнорируют, отчитывают или помыкают нами; из-за этого нам не " +\
             "удается добиться самых желанных целей. Ловушки управляют нашими мыслями, чувствами, " +\
             "действиями и отношениями с окружающими людьми. Из-за них мы испытываем гнев, грусть и " +\
             "тревогу. Даже когда кажется, что у нас есть все: высокий социальный статус, брак, " +\
             "уважение близких, успех, — нам часто не удается насладиться жизнью или поверить в " +\
             "свои достижения. \n\n" +\
             "Итак, выберите одну из опций:"

start_text = "Как проходить тест:\n" +\
             "Поставьте каждому из следующих утверждений оценку от в зависимости от того, насколько оно " +\
             "правдиво для вас.\n\n" +\
             "Каждый из вопросов имеет два варианта: как оно было в детстве и как дела обстоят сейчас. Если в " +\
             "разные моменты детства вы ответили бы по-разному, выберите значение, которое больше подходит для " +\
             "возраста до двенадцати лет.\n\n" +\
             "Затем оцените, насколько они верны для вас сейчас, во взрослом " +\
             "возрасте. Если в разные периоды вашей жизни ответ был бы разным, поставьте оценку в соответствии " +\
             "со своими чувствами в последние полгода."

about_text = "Привет! На связи Наталия Власевская, психолог, гештальт-терапевт. Я пишу про психологию, родительство " +\
             "и то, как найти контакт со своим Внутренним Ребенком простыми словами. А еще про переезд, отношения и " +\
             "мамские будни. Подписывайтесь на меня в соцестях, тут интересно."

info_text = start_text + "\n\n" +\
            "Этот тест составлен по книге Джефри Янга 'Прочь из замкнутого круга'. Если вы наберете много баллов в " +\
            "какой-то из ловушек, то рекомендуем вам ознакомиться и с книгой.\n\n" + about_text


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'{user_id} {user_full_name} {time.asctime()}')
    await bot.send_message(message.chat.id,
                           f"Привет, {user_full_name}!\n\n" + enter_text,
                           reply_markup=menu_markup)


@dp.message_handler(commands=['info'])
async def start_handler(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Telegram", url="https://t.me/golos_dadre"))
    markup.add(types.InlineKeyboardButton(text="Instagram psydadre", url="https://www.instagram.com/psydadre/"))
    markup.add(types.InlineKeyboardButton(text="VK", url="https://vk.com/dadre"))
    markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
    await bot.send_message(message.chat.id,
                           info_text,
                           reply_markup=markup)


@dp.callback_query_handler(lambda query: query.data.startswith("info"))
async def get_info(query: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Telegram", url="https://t.me/golos_dadre"))
    markup.add(types.InlineKeyboardButton(text="Instagram", url="https://www.instagram.com/psydadre/"))
    markup.add(types.InlineKeyboardButton(text="VK", url="https://vk.com/dadre"))
    markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
    await bot.edit_message_text(info_text,
                                query.message.chat.id, query.message.message_id,
                                reply_markup=markup)


@dp.callback_query_handler(lambda query: query.data.startswith("back_to_menu"))
async def back_to_menu(query: types.CallbackQuery):
    await bot.edit_message_text(f"Привет, {query['from']['first_name']} {query['from']['last_name']}!\n\n" + enter_text,
                                query.message.chat.id,
                                query.message.message_id,
                                reply_markup=menu_markup)


@dp.callback_query_handler(lambda query: query.data.startswith("new"))
async def start_new_test(query: types.CallbackQuery):
    user = db.get_user(query.message.chat.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
    if user[1] == 1:
        await bot.edit_message_text("Вы уже прошли тест. " +
                                    "Нажмите 'Пройти тест заново' для сброса результатов и повторного прохождения.",
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=markup)
        return

    if user[2] == 1:
        await bot.edit_message_text("Нажмите 'Продолжить' для возобновления прохождения теста, " +
                                    "либо 'Пройти тест заново' для сброса результатов",
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=markup)
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Перейти к вопросам", callback_data='start_questions'))
    markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
    db.set_user(chat_id=query.message.chat.id, is_passed=0, is_passing=1, question_index=0)
    await bot.edit_message_text(start_text,
                                query.message.chat.id,
                                query.message.message_id,
                                reply_markup=markup)


@dp.callback_query_handler(lambda query: query.data.startswith("start_questions"))
async def start_questions(query: types.CallbackQuery):
    user = db.get_user(query.message.chat.id)
    post = get_question_message(user)

    if post is not None:
        await bot.edit_message_text(post["text"],
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=post["keyboard"])


@dp.callback_query_handler(lambda query: query.data.startswith("continue"))
async def continue_test(query: types.CallbackQuery):
    user = db.get_user(query.message.chat.id)

    if user[1] == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
        await bot.edit_message_text("Вы уже завершили прохождение теста. " +
                                    "Для просмотра результатов нажмите 'Мои результаты'. "
                                    "Для повторного прохождения теста нажмите 'Начать тест заново'.",
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=markup)
        return

    if not user[1] == 1 and not user[2] == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
        await bot.edit_message_text("Вы ещё не проходили тест для того чтобы его продолжить. " +
                                    "Для прохождения теста, нажмите 'Начать тест'",
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=markup)
        return

    post = get_question_message(user)
    if post is not None:
        await bot.edit_message_text(post["text"],
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=post["keyboard"])


@dp.callback_query_handler(lambda query: query.data.startswith("restart"))
async def restart_test(query: types.CallbackQuery):
    user = db.get_user(query.message.chat.id)

    if not user[1] == 1 and not user[2] == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Начать тест", callback_data='new'))
        markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
        await bot.edit_message_text("Вы ещё не проходили тест для того чтобы начать его заново. Желаете начать тест?",
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=markup)
        return

    if not user[1] == 1 and user[2] == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Начать тест заново", callback_data='confirm_restart'))
        markup.add(types.InlineKeyboardButton(text="Продолжить тест", callback_data='continue'))
        markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
        await bot.edit_message_text("Вы уже проходите тест. Желаете начать тест заново?",
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=markup)
        return

    db.set_user(chat_id=query.message.chat.id, is_passed=0, is_passing=1, question_index=0, answers="''")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Перейти к вопросам", callback_data='start_questions'))
    markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
    await bot.edit_message_text(start_text,
                                query.message.chat.id,
                                query.message.message_id,
                                reply_markup=markup)


@dp.callback_query_handler(lambda query: query.data.startswith("confirm_restart"))
async def confirm_restart(query: types.CallbackQuery):
    db.set_user(chat_id=query.message.chat.id, is_passed=0, is_passing=1, question_index=0, answers="''")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Перейти к вопросам", callback_data='start_questions'))
    markup.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
    await bot.edit_message_text(start_text,
                                query.message.chat.id,
                                query.message.message_id,
                                reply_markup=markup)


@dp.callback_query_handler(lambda query: query.data.startswith("answer"))
async def set_answer(query: types.CallbackQuery):
    user = db.get_user(query.message.chat.id)

    if user[1] == 1 or not user[2] == 1:
        return

    separator = ''
    if len(user[4]) != 0:
        separator = ','
    answers = user[4] + separator + query.data.split("answer_")[1]
    db.set_user(chat_id=query.message.chat.id, answers="'"+answers+"'", question_index=int(user[3])+1)

    post = get_question_message(user)
    if post is not None:
        await bot.edit_message_text(post["text"],
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=post["keyboard"])


def get_question_message(user):
    user = db.get_user(user[0])
    keyboard = types.InlineKeyboardMarkup()

    if int(user[3]) == db.questions_count:
        text = f"Вы ответили на все вопросы."
        keyboard.add(types.InlineKeyboardButton(text="Мои результаты", callback_data='results'))

        db.set_user(chat_id=user[0], is_passed=1, is_passing=0)

        return {
            "text": text,
            "keyboard": keyboard
        }

    question = db.get_question(int(user[3]))
    if question is None:
        return

    keyboard.add(types.InlineKeyboardButton(text="Совершенно не обо мне", callback_data='answer_1'))
    keyboard.add(types.InlineKeyboardButton(text="В основном неверно", callback_data='answer_2'))
    keyboard.add(types.InlineKeyboardButton(text="Скорее верно, чем неверно", callback_data='answer_3'))
    keyboard.add(types.InlineKeyboardButton(text="Верно в небольшой степени", callback_data='answer_4'))
    keyboard.add(types.InlineKeyboardButton(text="В основном верно", callback_data='answer_5'))
    keyboard.add(types.InlineKeyboardButton(text="Идеально описывает меня", callback_data='answer_6'))
    text = f"Вопрос №{int(user[3]) + 1}\n\n{question}"

    return {"text": text, "keyboard": keyboard}


@dp.callback_query_handler(lambda query: query.data.startswith("results"))
async def get_results(query: types.CallbackQuery):
    user = db.get_user(query.message.chat.id)

    if not user[1] == 1:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
        await bot.edit_message_text(f"Для просмотра результатов, требуется пройти тест.",
                                    query.message.chat.id,
                                    query.message.message_id,
                                    reply_markup=keyboard)
        return

    traps_list = ["Отверженность__                     ",
                  "Недоверие и жестокое\n      обращение                              ",
                  "Уязвимость                              ",
                  "Зависимость                           ",
                  "Эмоциональная\n     депривация                             ",
                  "Изгнание из общества         ",
                  "Неполноценность                 ",
                  "Несостоятельность              ",
                  "Покорность                             ",
                  "Завышенные стандарты     ",
                  "Избранность                           "]
    rows = ["Ваши результаты: \n\n",
            "❗️*Ловушки*                                  *Максимум*\n"]
    answers = list(map(int, user[4].split(',')))
    index_modify = 0
    keyboard = types.InlineKeyboardMarkup()
    for index, trap in enumerate(traps_list):
        result = "     "
        if answers[index + index_modify] > 3 \
                or answers[index + 1 + index_modify] > 3 \
                or answers[index + 2 + index_modify] > 3 \
                or answers[index + 3 + index_modify] > 3:
            result = "❗️"
            if index == 0:
                keyboard.add(types.InlineKeyboardButton(text="Отверженность", callback_data='trap_1'))
            elif index == 1:
                keyboard.add(types.InlineKeyboardButton(text="Недоверие и жестокое обращение", callback_data='trap_2'))
            elif index == 2:
                keyboard.add(types.InlineKeyboardButton(text="Уязвимость", callback_data='trap_3'))
            elif index == 3:
                keyboard.add(types.InlineKeyboardButton(text="Зависимость", callback_data='trap_4'))
            elif index == 4:
                keyboard.add(types.InlineKeyboardButton(text="Эмоциональная депривация", callback_data='trap_5'))
            elif index == 5:
                keyboard.add(types.InlineKeyboardButton(text="Изгнание из общества", callback_data='trap_6'))
            elif index == 6:
                keyboard.add(types.InlineKeyboardButton(text="Неполноценность", callback_data='trap_7'))
            elif index == 7:
                keyboard.add(types.InlineKeyboardButton(text="Несостоятельность", callback_data='trap_8'))
            elif index == 8:
                keyboard.add(types.InlineKeyboardButton(text="Покорность", callback_data='trap_9'))
            elif index == 9:
                keyboard.add(types.InlineKeyboardButton(text="Завышенные стандарты", callback_data='trap_10'))
            elif index == 10:
                keyboard.add(types.InlineKeyboardButton(text="Избранность", callback_data='trap_11'))
        mark_max = max(answers[index + index_modify],
                       answers[index + 1 + index_modify],
                       answers[index + 2 + index_modify],
                       answers[index + 3 + index_modify])
        rows.append(result + trap + str(mark_max) + "\n")

        index_modify += 3

    text_result = ""
    for row in rows:
        text_result += row

    text_result += "\n" + "================================\n\n"+about_text +\
                   "\n\n[Telegram](https://t.me/golos_dadre) \t" +\
                   "[Instagram](https://www.instagram.com/psydadre/) \t[VK](https://vk.com/dadre)" +\
                   "\n\n================================"

    keyboard.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_menu'))
    if len(rows) > 0:
        text_result += "\n\n*Чтобы почитать подробнее про каждую ловушку, нажмите:*"

    await bot.edit_message_text(text_result,
                                query.message.chat.id,
                                query.message.message_id,
                                reply_markup=keyboard,
                                parse_mode="Markdown",
                                disable_web_page_preview=True)


@dp.callback_query_handler(lambda query: query.data.startswith("trap_"))
async def get_results(query: types.CallbackQuery):
    text_result = ""
    keyboard = types.InlineKeyboardMarkup()
    if query.data == 'trap_1':
        text_result = "*Ловушка Отверженности* — это ощущение, что люди, которых вы любите, бросят вас и вы " +\
                      "навсегда останетесь в эмоциональной изоляции. Близкие умрут, навсегда уйдут из дома или " +\
                      "предпочтут когото другого, — вас так или иначе оставят одного. Из-за этого убеждения вы " +\
                      "цепляетесь за близких людей, но таким образом только отталкиваете их от себя. Даже недолгая " +\
                      "разлука сильно расстраивает или злит вас."
    if query.data == 'trap_2':
        text_result = "*Ловушка Недоверия и  жестокого обращения* — это ожидание, что люди обидят вас или " +\
                      "каким-то образом навредят вам; изменят, обманут, будут манипулировать, унижать, бить или " +\
                      "каким-то образом использовать вас. Попав в нее, вы защищаетесь, спрятавшись за стеной " +\
                      "недоверия. Вы никого не подпускаете близко. Вы подозрительно относитесь к намерениям людей " +\
                      "и склонны предполагать худшее. Вы ждете, что люди, которых вы любите, предадут вас. Вы либо " +\
                      "совсем избегаете отношений и не слишком открываетесь другим, либо вступаете в отношения с " +\
                      "людьми, которые плохо к вам относятся, а потом злитесь на них и желаете им отомстить. \n\n" +\
                      "C вашей способностью существовать независимо от других связаны еще две ловушки: " +\
                      "*Зависимость* и *Уязвимость*."
        keyboard.add(types.InlineKeyboardButton(text="Зависимость", callback_data='trap_4'))
        keyboard.add(types.InlineKeyboardButton(text="Уязвимость", callback_data='trap_3'))
    if query.data == 'trap_3':
        text_result = "С *Уязвимостью* вы живете в страхе, что вот-вот случится катастрофа — природная, " +\
                      "криминальная, медицинская или финансовая. Вы попали в эту ловушку, потому что в детстве " +\
                      "вас научили, что мир — это опасное место. Вероятно, родители чрезмерно опекали вас из страха " +\
                      "за ваше благополучие. Ваши страхи огромны и нереалистичны, но вы позволяете им " +\
                      "контролировать вашу жизнь и очень много энергии тратите на безопасность. Вы можете бояться " +\
                      "болезни, панической атаки, СПИДа или безумия. Вы переживаете, что обеднеете и будете просить " +\
                      "подаяния на улицах. Ваша уязвимость может быть связана и с другими фобиями, например " +\
                      "страхом полетов, уличных грабителей или землетрясений. \n\n" +\
                      "Две другие ловушки связаны с силой эмоциональной привязанности к другим: *Эмоциональная* " +\
                      "*депривация* и *Изгнание из общества*."
    if query.data == 'trap_4':
        text_result = "Попав в *ловушку Зависимости*, вы чувствуете, что неспособны справиться с повседневной " +\
                      "жизнью без посторонней помощи. Вы полагаетесь на других, как на костыли, и вам нужна " +\
                      "постоянная поддержка. В детстве вы пытались отстоять свою независимость, а вас заставили " +\
                      "почувствовать себя беспомощным. Теперь вы ищете сильных людей, на которых можно положиться и " +\
                      "отдать свою жизнь в их руки. На работе вы избегаете самостоятельных заданий. Нечего и " +\
                      "говорить, что из-за этого вы проигрываете."
        keyboard.add(types.InlineKeyboardButton(text="Эмоциональная депривация", callback_data='trap_5'))
        keyboard.add(types.InlineKeyboardButton(text="Изгнание из общества", callback_data='trap_6'))
    if query.data == 'trap_5':
        text_result = "*Эмоциональная депривация* — это вера в то, что другие люди никогда не смогут удовлетворить " +\
                      "вашу потребность в любви. Вам кажется, что никто о вас не заботится и вас не понимает. Вас " +\
                      "тянет к холодным и равнодушным людям, или вы сами холодны и равнодушны, а это приводит " +\
                      "к неудовлетворенности в отношениях. Вы чувствуете себя обманутым; то злитесь, то страдаете " +\
                      "от боли и одиночества. По иронии судьбы, ваша злость только сильнее отталкивает людей, " +\
                      "продлевая вашу депривацию. \n\n" +\
                      "    Когда пациенты с эмоциональной депривацией приходят на терапевтические сессии, их тоска " +\
                      "как будто остается с нами после их ухода. Это ощущение опустошенности и эмоциональной " +\
                      "оторванности. Это люди, которые не знают, что такое любовь."
    if query.data == 'trap_6':
        text_result = "*Изгнание из общества* — ловушка ваших отношений с друзьями и социальными группами. Вам " +\
                      "кажется, что вы изолированы от остального мира, вы чувствуете себя иным. Если вы попали в " +\
                      "эту ловушку, то в детстве вас, вероятно, отвергали сверстники. У вас не было друзей, или " +\
                      "некая необычная черта заставляла вас чувствовать себя непохожим на других. Во взрослом " +\
                      "возрасте вы, скорее всего, поддерживаете свою ловушку, избегая социальных контактов. Вы не " +\
                      "общаетесь в компаниях и не заводите друзей. \n" +\
                      "    Вы могли чувствовать себя отверженным, потому что другим детям в вас что-то не нравилось " +\
                      "и вы чувствовали себя нежелательным элементом общества. Во взрослом возрасте вы можете " +\
                      "ощущать, что вы уродливы, несексуальны, у вас низкий статус, вы обладаете слабыми навыками " +\
                      "общения, скучны или как-то иначе неполноценны. Общаясь, вы воспроизводите свою детскую " +\
                      "отверженность — чувствуете себя и поступаете так, будто вы хуже других. \n" +\
                      "    Ловушка Изгнания из общества не всегда очевидна. Многие люди довольно комфортно " +\
                      "чувствуют себя с ней и вполне успешны в общении. Их ловушка может не проявляться в личных " +\
                      "отношениях. Иногда мы удивляемся, обнаружив, как тревожно и одиноко им на вечеринках, в " +\
                      "классах, на встречах или на работе. Они испытывают беспокойство, ищут и не могут найти " +\
                      "себе места. \n\n" +\
                      "Две ловушки, которые касаются вашей самооценки, — *Неполноценность* и *Несостоятельность*."
        keyboard.add(types.InlineKeyboardButton(text="Неполноценность", callback_data='trap_7'))
        keyboard.add(types.InlineKeyboardButton(text="Несостоятельность", callback_data='trap_8'))
    if query.data == 'trap_7':
        text_result = "С *Неполноценностью* вы чувствуете, что на глубинном уровне у вас есть изъяны и недостатки. " +\
                      "Вы уверены, что если кто-то приблизится к вам, он уже не сможет вас полюбить — ваша " +\
                      "ущербность вылезет наружу. В детстве вы не чувствовали, что в семье вас уважают. Вместо " +\
                      "этого вас критиковали. Вы винили себя — и чувствовали, что недостойны любви. Во взрослом " +\
                      "возрасте вам сложно поверить, что близкие ценят вас; вы ждете, что они вас оттолкнут."
    if query.data == 'trap_8':
        text_result = "*Несостоятельность* — это уверенность в том, что вы ничего не достигли по сравнению со " +\
                      "сверстниками: ни в школе, ни на работе, ни в спорте. В детстве ваши успехи принижали. Вам " +\
                      "было сложно учиться или не хватало усидчивости, чтобы освоить такие важные навыки, как, " +\
                      "например, чтение. Другие дети всегда были лучше вас. Вас называли «тупым», «бездарным» или " +\
                      "«ленивым». Во взрослом возрасте вы поддерживаете свою ловушку, преувеличивая свои неудачи и " +\
                      "ведя себя так, что они продолжаются. \n\n" +\
                      "Две ловушки связаны с самовыражением — возможностью говорить о своих желаниях и добиваться " +\
                      "удовлетворения своих насущных потребностей: *Покорность* и *Завышенные стандарты*."
        keyboard.add(types.InlineKeyboardButton(text="Покорность", callback_data='trap_9'))
        keyboard.add(types.InlineKeyboardButton(text="Завышенные стандарты", callback_data='trap_10'))
    if query.data == 'trap_9':
        text_result = "С *Покорностью* вы жертвуете собственными нуждами и желаниями ради удовлетворения " +\
                      "потребностей других людей или их удовольствия. Вы позволяете кому-то контролировать вас. " +\
                      "Вы делаете это либо из чувства вины за то, что раните других, когда выбираете себя, или из " +\
                      "страха, что вас накажут или бросят, если вы не подчинитесь. В детстве близкий человек, " +\
                      "вероятно родитель, подчинил вас себе. Во взрослом возрасте вы постоянно завязываете " +\
                      "отношения с доминирующими, контролирующими людьми, которым подчиняетесь, или с " +\
                      "несостоятельными людьми, неспособными дать вам ничего взамен"
    if query.data == 'trap_10':
        text_result = "С *Завышенными стандартами* вы очень высоко задираете планку и изо всех сил стараетесь не " +\
                      "разочароваться в себе. Вы делаете особый акцент на статусе, деньгах, достижениях, " +\
                      "внешности, порядке или признании. Для вас они важнее счастья, радости, удовольствия от " +\
                      "выполненного дела и полноценных отношений. Вероятно, вы проецируете свои завышенные " +\
                      "стандарты на других людей и осуждаете их. В детстве от вас ждали самых лучших результатов, " +\
                      "учили, что все остальное — провал. Вы усвоили, что все ваши поступки недостаточно хороши."
    if query.data == 'trap_11':
        text_result = "Последняя ловушка, *Избранность*, ассоциируется со способностью воспринимать адекватные " +\
                      "жизненные ограничения. Люди с этой ловушкой чувствуют себя особенными. Они уверены, что " +\
                      "имеют право делать, говорить или получать все, что захотят, причем без промедления. Они " +\
                      "отвергают то, что требует времени и терпения, и цену, которую приходится платить за их " +\
                      "прихоти другим людям. Им не хватает самодисциплины. \n" +\
                      "    Многих таких людей баловали в детстве. Их не учили контролировать себя или " +\
                      "придерживаться определенных рамок. Они выросли, но продолжают сердиться, если не получают " +\
                      "желаемого."
    keyboard.add(types.InlineKeyboardButton(text="Вернуться к результатам", callback_data='results'))
    await bot.edit_message_text(text_result,
                                query.message.chat.id,
                                query.message.message_id,
                                reply_markup=keyboard,
                                parse_mode="Markdown")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

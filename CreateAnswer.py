import random

import logging
from logging import handlers

logging_handler = logging.handlers.RotatingFileHandler(
    filename='logs/system.log',
    encoding='utf8',
    mode='a'
)

logging.basicConfig(format='%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO,
                    handlers=[logging_handler])


class CreateAnswer:
    def __init__(self, ege_data, similar_tasks):
        self.ege_data = ege_data
        self.similar_tasks = similar_tasks

    def ans_template(self, users_dict, user_id, text_question):
        question_num = str(users_dict[user_id].active_problem)
        s = self.ege_data[question_num]['problem_solution']
        s += 'Правильный ответ: '
        s += ', '.join(self.ege_data[question_num]['answer'])
        if text_question != 'нет ответа':
            s += '\n' + 'Ваш ответ: ' + text_question + '\n'
            if question_num not in users_dict[user_id].list_of_solved_problems:
                users_dict[user_id].put_new_solved_problem(question_num)
            s += 'Ваш ответ оказался правильным' + '\n'
            s += f'Вы решили задачу с {users_dict[user_id].attempt_cnt} попытки'

        return {'message': [s], 'photo': [self.ege_data[question_num]['problem_image_solution']]}

    def is_ready_problem(self, user, task):
        if str(task) not in user.list_of_solved_problems and \
                str(task) not in user.list_of_not_solved_problems:
            return True
        return False

    def get_stats(self, users_list, user_id):
        s = ""
        try:
            s = s + "- Вы ответили правильно на: " + str(
                round(len(users_list[user_id].list_of_solved_problems) /
                      (len(users_list[user_id].list_of_solved_problems) +
                       len(users_list[user_id].list_of_not_solved_problems)) * 100)) + "% задач\n"
        except:
            s += "- Вы ещё не решили ни одной задачи\n"
        try:
            s = s + "- В среднем вы тратите " + str(round(users_list[user_id].attempts_succesess /
                                                          len(users_list[user_id].list_of_solved_problems),
                                                          2)) + " попыток на задачу"
        except:
            s += "- У вас ещё нет правильно решенных задач\n"

        return {'message': [s], 'photo': []}

    def choice_rand_question(self, users_dict, user_id):
        while True:
            num = random.choice([*self.ege_data.keys()])
            if self.is_ready_problem(users_dict[user_id], str(num)):
                break

        rnd = random.random()
        if rnd < 0.6 and len(users_dict[user_id].list_of_not_solved_problems):
            unsolved_q = random.choice(users_dict[user_id].list_of_not_solved_problems)
            similar_tasks = self.similar_tasks[unsolved_q]
            similar_tasks_not_solved = []
            for task in similar_tasks:
                if self.is_ready_problem(users_dict[user_id], str(task)):
                    similar_tasks_not_solved.append(str(task))
            if len(similar_tasks_not_solved) != 0:
                zam_num = random.choice(similar_tasks_not_solved)
                if str(zam_num) in [*self.ege_data.keys()]:
                    num = zam_num

        logging.info(f"Solving task {num} by {user_id}")
        print(f"Solving task {num} by {user_id}")
        users_dict[user_id].active_problem = str(num)
        users_dict[user_id].attempt_cnt = '1'

        return {'message': ['Задача по предмету: ' + self.ege_data[str(num)]['subject_name'],
                            self.ege_data[str(num)]['problem_text']],
                'photo': [self.ege_data[str(num)]['problem_image_text']]}

    def choice_similar_task(self, users_dict, user_id):
        if users_dict[user_id].past_problem == '-1':
            return {'message': ['Вы еще не решили ни одной задачи :('], 'photo': []}
        else:
            for problem_id in self.similar_tasks[users_dict[user_id].past_problem]:
                if str(problem_id) not in [*self.ege_data.keys()]:
                    continue
                if self.is_ready_problem(users_dict[user_id], str(problem_id)):
                    users_dict[user_id].active_problem = str(problem_id)
                    users_dict[user_id].attempt_cnt = '1'
                    return {'message': ['Задача по предмету: ' + self.ege_data[str(problem_id)]['subject_name'],
                                        self.ege_data[str(problem_id)]['problem_text']],
                            'photo': [self.ege_data[str(problem_id)]['problem_image_text']]}
            return {'message': ['Мы не смогли найти похожую задачу'], 'photo': []}

    def get_answer(self, users_dict, user_id, question_num):
        if question_num != '-1':
            messages = self.ans_template(users_dict, user_id, 'нет ответа')
            messages['message'].append('Вы не смогли решить задачу')
            logging.info('#not#' + str(user_id) + ':' + str(users_dict[user_id].active_problem))
            print('#not#', str(user_id), ':', str(users_dict[user_id].active_problem))
            users_dict[user_id].list_of_not_solved_problems.append(
                users_dict[user_id].active_problem)
            users_dict[user_id].past_problem = users_dict[user_id].active_problem
            users_dict[user_id].active_problem = '-1'
            users_dict[user_id].attempt_cnt = '1'

            return messages
        else:
            return {'message': ['Вы сейчас не решаете задачу'], 'photo': []}

    def check_answer(self, users_dict, user_id, text_question, question_num):
        if users_dict[user_id].active_problem == '-1':
            logging.info(f"Incorrect command {text_question} by {user_id}")
            print(f"Incorrect command {text_question} by {user_id}")
            return {'message': ["Неправильный формат ввода"], 'photo': []}
        else:
            flag = False
            for line in self.ege_data[question_num]['answer']:
                if type(line) == str:
                    if text_question.lower() == line.lower():
                        flag = True
                else:
                    if text_question == line:
                        flag = True
            if flag:
                messages = self.ans_template(users_dict, user_id, text_question)
                users_dict[user_id].past_problem = users_dict[user_id].active_problem
                users_dict[user_id].active_problem = '-1'
                users_dict[user_id].attempt_cnt = '1'
                return messages
            users_dict[user_id].attempt_cnt = str(int(users_dict[user_id].attempt_cnt) + 1)
            if users_dict[user_id].attempt_cnt == '3':
                messages = self.ans_template(users_dict, user_id, 'нет ответа')
                messages['message'].insert(0, 'Вы не смогли решить задачу')

                logging.info('##' + str(user_id) + ':' + str(users_dict[user_id].active_problem))
                print('##', str(user_id), ':', str(users_dict[user_id].active_problem))

                users_dict[user_id].list_of_not_solved_problems.append(
                    users_dict[user_id].active_problem)
                users_dict[user_id].past_problem = users_dict[user_id].active_problem
                users_dict[user_id].active_problem = '-1'
                users_dict[user_id].attempt_cnt = '1'
                return messages
            else:
                return {'message': ['Неправильный ответ'], 'photo': []}

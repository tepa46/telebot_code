import json


class UserDataManager(object):
    def __init__(self, user_name='', list_of_solved_problems=[], list_of_not_solved_problems=[], active_problem='-1',
                 past_problem='-1', attempt_cnt='1', attempts_succesess=0):
        self.user_name = user_name
        self.list_of_solved_problems = list_of_solved_problems.copy()
        self.list_of_not_solved_problems = list_of_not_solved_problems.copy()
        self.active_problem = active_problem
        self.past_problem = past_problem
        self.attempt_cnt = attempt_cnt
        self.attempts_succesess = attempts_succesess

    def put_new_solved_problem(self, problem_id):
        self.attempts_succesess += int(self.attempt_cnt)
        self.list_of_solved_problems.append(problem_id)

    def put_new_not_solved_problem(self, problem_id):
        self.list_of_not_solved_problems.append(problem_id)


def load_user_data_manager():
    try:
        open('users_list.json', 'r', encoding='utf8')
    except FileNotFoundError:
        with open('users_list.json', 'w', encoding='utf8') as f:
            print('{}', file=f)

    with open('users_list.json', 'r', encoding='utf8') as input_file:
        d = json.load(input_file)
    for user in d:
        d[user] = UserDataManager(d[user][0], d[user][1], d[user][2], d[user][3], d[user][4], d[user][5], d[user][6])
    return d


def put_new_users(tg_users_dict):
    d = dict()
    for user in tg_users_dict:
        if user[:2] != 'tg':
            continue
        d[user] = [tg_users_dict[user].user_name, tg_users_dict[user].list_of_solved_problems,
                   tg_users_dict[user].list_of_not_solved_problems,
                   tg_users_dict[user].active_problem, tg_users_dict[user].past_problem,
                   tg_users_dict[user].attempt_cnt,
                   tg_users_dict[user].attempts_succesess]
    with open('users_list.json', 'w', encoding='utf8') as output_file:
        json.dump(d, output_file)

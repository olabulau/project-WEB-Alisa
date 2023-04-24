from flask import Flask, request, jsonify
import logging
import random
from food import type_animal
from name import animals

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False,
            'guessed_animal': []
        }

        return
    first_name = get_first_name(req)
    if sessionStorage[user_id]['first_name'] is None:
        if first_name is None:
            res['response']['text'] = 'Не раслышала имя. Повтори!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_animals'] = []
            res['response']['text'] = 'Приятно познакомиться, ' + first_name.title() + '. Я Алиса. ' \
                                                                                       'Отгадаешь животного' \
                                                                                       ' по части фото?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True

                },
                {
                    'title': 'Нет',
                    'hide': True

                }
            ]

    else:

        if not sessionStorage[user_id]['game_started']:
            if 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['guessed_animals']) == 50:
                    res['response']['text'] = 'Ты отгадал всех животных!'
                    res['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req)

            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True

            else:
                res['response']['text'] = 'Не понял ответа! Так да или нет?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }
                ]
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        animal = list(animals.keys())[random.randint(0, 49)]
        while animal in sessionStorage[user_id]['guessed_animals']:
            animal = list(animals.keys())[random.randint(0, 2)]

        sessionStorage[user_id]['animal'] = animal

        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за животное?'
        res['response']['card']['image_id'] = animals[animal][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'

    else:
        animal = sessionStorage[user_id]['animal']
        if animal in sessionStorage[user_id]['guessed_animals']:
            if req['request']['original_utterance'].lower() in type_animal[animal]:
                res['response']['text'] = 'Правильно! Сыграем еще?'
                res['response']['buttons'] = [
                    {
                        "title": "Да",
                        "hide": True
                    },
                    {
                        "title": "Нет",
                        "hide": True
                    }
                ]
                sessionStorage[user_id]['game_started'] = False
                return
            else:
                res['response']['text'] = 'Это неправильное питание для животного: %s. Попробуй еще.' \
                                          % (animal.title())
                return

        if req['request']['original_utterance'].lower() == animal:

            res['response']['text'] = 'Правильно! А чем это животное питается?'
            sessionStorage[user_id]['guessed_animals'].append(animal)
            return

        else:

            res['response']['text'] = 'Неправильно'
            if attempt == 4:
                res['response']['text'] = 'Вы пытались. Это ' + animal.title() + '. Сыграем еще?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_animals'].append(animal)
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе другая часть животного'
                res['response']['card']['image_id'] = animals[animal][attempt - 1]

    sessionStorage[user_id]['attempt'] += 1


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            if 'first_name' in entity['value'].keys():
                return entity['value']['first_name']
            else:
                return None
    return None


if __name__ == '__main__':
    app.run()

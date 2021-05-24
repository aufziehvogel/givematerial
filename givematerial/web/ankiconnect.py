import collections
import requests
import sys

from givematerial.learningstatus import AnkiStatus


if __name__ == '__main__':
    user_id = sys.argv[1]
    deck_name = sys.argv[2]
    host = 'localhost'
    port = 5000
    status_reader = AnkiStatus(deck_name)

    update_msg = collections.defaultdict(list)
    for known_word in status_reader.get_known_learnables():
        update_msg['known'].append(known_word)
    for learning_word in status_reader.get_learning_learnables():
        update_msg['learning'].append(learning_word)

    update_msg['token'] = user_id
    r = requests.post(f'http://{host}:{port}/learning-status', json=update_msg)
    print(r.json())

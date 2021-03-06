#!/usr/bin/env python3

import argparse
import requests

from givematerial.learningstatus import AnkiStatus, FileBasedStatus


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Upload local status to web site')
    parser.add_argument(
        '--server-host', '-s', dest='host', default='localhost')
    parser.add_argument(
        '--server-port', '-p', dest='port', default='5000')
    parser.add_argument(
        '--username', '-u', dest='username', required=True)

    subparsers = parser.add_subparsers(dest='subparser_name')

    anki_parser = subparsers.add_parser('anki')
    anki_parser.add_argument('--deck', '-d', dest='deckname', required=True)
    file_parser = subparsers.add_parser('file')
    file_parser.add_argument('--file', '-f', dest='filepath', required=True)

    args = parser.parse_args()

    if args.subparser_name == 'anki':
        status_reader = AnkiStatus(args.deckname)
    elif args.subparser_name == 'file':
        status_reader = FileBasedStatus(args.filepath, None)
    else:
        raise NotImplementedError('Unknown command')

    update_msg = {'known': [], 'learning': []}
    for known_word in status_reader.get_known_learnables():
        update_msg['known'].append(known_word)
    for learning_word in status_reader.get_learning_learnables():
        update_msg['learning'].append(learning_word)

    update_msg['token'] = args.username
    remote_url = f'http://{args.host}:{args.port}/learning-status'
    r = requests.post(remote_url, json=update_msg)
    print(r.json())

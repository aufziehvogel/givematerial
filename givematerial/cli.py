import argparse

from givematerial import recommendation


def main():
    parser = argparse.ArgumentParser(description='Get text recommendations')
    parser.add_argument('--language', '-l', dest='language', required=True)
    args = parser.parse_args()

    for _, ts in recommendation.calc_recommendations(args.language):
        print(
            f'== {ts.artist} - {ts.title} (learning {ts.learning}, total {ts.total}, unknown {len(ts.unknown)}) ==')
        print()
        print(' '.join(ts.unknown))
        print()
        print(ts.text)
        print()
        print()


def manage_read():
    parser = argparse.ArgumentParser(description='Manage read markers')
    parser.add_argument('--language', '-l', dest='language', required=True)
    parser.add_argument('learning', nargs='*')
    args = parser.parse_args()

    with open(f'data/{args.language}/learning', 'at') as f:
        for word in args.learning:
            f.write(f'{word}\n')

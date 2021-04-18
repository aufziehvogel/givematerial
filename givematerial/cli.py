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
        print(', '.join(ts.unknown))
        print()
        print(ts.text)
        print()
        print()

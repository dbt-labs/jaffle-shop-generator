from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument("years")

args = parser.parse_args()

years = args.years

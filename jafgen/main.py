import argparse

from jafgen.simulation import Simulation


def main():
    parser = argparse.ArgumentParser(
        prog="jafgen",
        description="Generate a jaffle shop simulation across a given number of years",
        epilog="Enjoy your jaffles!",
    )

    parser.add_argument(
        "--years",
        choices=range(1, 11),
        nargs="?",
        default=2,
        type=int,
        help="Enter an integer between 1 and 10 to control the length of the simultation",
    )

    parser.add_argument(
        "--prefix",
        type=str,
        nargs="?",
        default="raw",
        help="String that will be prefixed with an underscore before file names",
    )

    args = parser.parse_args()

    sim = Simulation(args.years, args.prefix)
    sim.run_simulation()
    sim.save_results()

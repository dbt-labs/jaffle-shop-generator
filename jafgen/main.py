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
        type=int,
        help="Enter an integer between 1 and 10 to control the length of the simultation",
    )

    args = parser.parse_args()

    sim = Simulation(args.years)
    sim.run_simulation()
    sim.save_results()

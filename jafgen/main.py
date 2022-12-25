# import argparse

from jafgen.simulation import Simulation

# parser = argparse.ArgumentParser(
#     prog="jafgen",
#     description="Generate a jaffle shop simulation across a given number of years",
#     epilog="Enjoy your jaffles!",
# )


def main():
    sim = Simulation(2)
    sim.run_simulation()
    sim.save_results()

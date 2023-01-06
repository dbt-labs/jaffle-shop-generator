# test if jagen is run for 1 year that it has 365 days
from jafgen.simulation import Simulation


def test_year_length():
    sim = Simulation(2)
    assert sim.sim_days == 730

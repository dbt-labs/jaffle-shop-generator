from jafgen.simulation import Simulation


def test_year_length():
    sim = Simulation(2, "raw")
    assert sim.sim_days == 730

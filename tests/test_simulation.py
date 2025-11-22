from pathlib import Path
from jafgen.simulation import Simulation
import csv

class TestSimulation:
    def test_simulation_run(self, tmp_path: Path):
        # Create a simulation that runs for 1 year and 1 day
        simulation = Simulation(years=1, days=1, prefix="test")

        # Run the simulation
        simulation.run_simulation()

        # Check that the simulation has produced some data
        assert len(simulation.orders) > 0
        assert len(simulation.customers) > 0
        
        # Save the results
        simulation.save_results()

        # Check that the output files have been created
        output_path = Path("./jaffle-data")
        assert (output_path / "test_customers.csv").exists()
        assert (output_path / "test_orders.csv").exists()
        assert (output_path / "test_items.csv").exists()
        assert (output_path / "test_stores.csv").exists()
        assert (output_path / "test_supplies.csv").exists()
        assert (output_path / "test_products.csv").exists()
        assert (output_path / "test_tweets.csv").exists()

        # Check that the output files have the expected content
        with open(output_path / "test_customers.csv", "r") as f:
            reader = csv.reader(f)
            # Check that there is at least one customer
            assert len(list(reader)) > 1

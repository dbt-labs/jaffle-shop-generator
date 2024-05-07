import datetime as dt
from typing import Annotated

import typer

from jafgen.simulation import Simulation
from jafgen.time import Day

app = typer.Typer()


@app.command()
def run(
    years: Annotated[
        int, typer.Argument(help="Number of years to simulate. Default is 1.")
    ] = 1,
    pre: Annotated[
        str,
        typer.Option(help="Optional prefix for the output file names."),
    ] = "raw",
    export_from: Annotated[
        dt.datetime,
        typer.Option(help="Export data from this date onwards.")
    ] = Day.EPOCH
) -> None:
    """Run jafgen in CLI mode."""
    sim = Simulation(years * 365, pre)
    sim.run_simulation()
    sim.save_results(path="./jaffle-data/", start_from=export_from)

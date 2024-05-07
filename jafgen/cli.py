import datetime as dt
from pathlib import Path
from typing import Annotated, Optional

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
    cache_file: Annotated[
        Optional[Path],
        typer.Option(
            help="The state cache file to use, if provided. "
            "Otherwise will run simulation from EPOCH.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    export_from: Annotated[
        dt.datetime, typer.Option(help="Export data from this date onwards.")
    ] = Day.EPOCH,
) -> None:
    """Run jafgen in CLI mode."""
    sim_end = Day.EPOCH + dt.timedelta(days=365 * years)
    sim = Simulation(
        sim_end=sim_end,
        cache_file=cache_file,
    )
    sim.run_simulation()
    sim.save_results(path="./jaffle-data/", prefix=pre, save_from=export_from)

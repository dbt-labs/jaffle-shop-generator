from typing import Annotated

import typer

from jafgen.simulation import Simulation

app = typer.Typer()


@app.command()
def run(
    # We set default to 0 here to make sure users don't get confused if they only put in days.
    # If they don't set anything we have years default = 1 later to keep the same functionality. 
    years: Annotated[
         int, typer.Argument(help="Number of years to simulate. Default is 1.")
    ] = 0,
    days: Annotated[
        int, typer.Option(help="Number of years to simulate. Default is 1.")
    ] = 0,
    pre: Annotated[
        str,
        typer.Option(help="Optional prefix for the output file names."),
    ] = "raw",
) -> None:
    
    # To keep the default value for backwards compatibility.
    if years == 0 and days == 0:
        years = 1

    sim = Simulation(years, days, pre)
    sim.run_simulation()
    sim.save_results()

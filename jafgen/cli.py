from typing import Annotated
import typer

from jafgen.simulation import Simulation

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
):
    sim = Simulation(years, pre)
    sim.run_simulation()
    sim.save_results()

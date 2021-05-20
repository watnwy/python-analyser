import asyncio
import logging
from pathlib import Path

import typer

from analyser.packages import poetry

app = typer.Typer()

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class CLIHandler(logging.Handler):
    COLORS = {
        logging.DEBUG: "blue",
        logging.INFO: "green",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "red",
    }

    __slots__ = "no_color"

    def __init__(self, no_color: bool):
        self.no_color = no_color
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        typer.secho(
            self.format(record),
            fg=self.COLORS.get(record.levelno) if not self.no_color else None,
        )


def logging_setup(debug: bool, no_color: bool):
    ch = CLIHandler(no_color=no_color)

    if debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)

    logger.addHandler(ch)


@app.command()
def analyse(
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Only print out the result",
        show_default=False,
        is_flag=True,
    ),
    no_color: bool = typer.Option(
        False,
        "--no_color",
        "-n",
        help="Do not color the logs",
        show_default=False,
        is_flag=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Also display the debugging logs",
        show_default=False,
        is_flag=True,
    ),
    path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
):
    """
    Run an analyse and return the found objects
    """
    if not quiet:
        logging_setup(debug, no_color)
    logger.info(f"Analysing {path}")
    objects = asyncio.run(poetry.objects_from_packages(str(path)))
    column_width = max(len(object.name) for object in objects)
    for object in sorted(objects, key=lambda object: object.name):
        typer.echo(f"{object.name:{column_width}} - {object.version}")


app()

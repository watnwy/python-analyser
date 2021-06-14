import asyncio
import logging
from pathlib import Path

import typer

from analyser import run_analyses

app = typer.Typer()

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class CLIHandler(logging.Handler):
    COLORS = {
        logging.DEBUG: "blue",
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


class CLIAnalysisHandler(CLIHandler):
    ANALYSIS_COLORS = ["bright_green", "bright_blue", "bright_magenta", "bright_cyan"]

    __slots__ = "no_color"

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.WARNING:
            return super().emit(record)
        typer.secho(
            self.format(record),
            fg=self.ANALYSIS_COLORS[
                int(record.__dict__.get("analyser_id", 0)) % len(self.COLORS)
            ]
            if not self.no_color
            else None,
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

    analysis_logger = logging.getLogger("watnwy.analysis")
    analysis_logger.propagate = False
    analyser_handler = CLIAnalysisHandler(no_color=no_color)
    if debug:
        analyser_handler.setLevel(logging.DEBUG)
    else:
        analyser_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(analyser_id)s > %(message)s"
    )
    analyser_handler.setFormatter(formatter)

    analysis_logger.addHandler(analyser_handler)


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

    objects = asyncio.run(run_analyses(str(path)))

    if objects:
        column_width = max(len(object.name) for object in objects)
    else:
        column_width = 10
    for object in sorted(objects, key=lambda object: object.name):
        typer.echo(
            f"{object.name:{column_width}} - {object.versions} "
            f"(With versions provider: {len(object.versions_providers) > 0})"
        )


app()

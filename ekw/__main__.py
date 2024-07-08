from rich import print
import typing

import typer

from ekw.process import ScraperProcess
from ekw.utils.logging import setup_logging
from ekw.utils.sum import find_crc

app = typer.Typer()


@app.command()
def start(
    region: typing.Annotated[
        str,
        typer.Argument(
            ...,
            help="Kod regionu, np. KR1A",
        ),
    ],
    start: typing.Annotated[
        int,
        typer.Option(
            ...,
            help="Numer pierwszej księgi do pobrania",
        ),
    ] = 0,
    end: typing.Annotated[
        int,
        typer.Option(
            ...,
            help="Numer ostatniej księgi do pobrania",
        ),
    ] = 9999,
):
    setup_logging()

    for i in range(start, end + 1):
        ekw = f"{region}/{str(i).zfill(8)}"
        ekw_sum = find_crc(ekw)

        print(f"Pobieram [b][blue]{ekw}/{ekw_sum}[/blue][/b]...")
        scraper = ScraperProcess(f"{ekw}/{ekw_sum}")
        scraper.start()


if __name__ == "__main__":
    app()

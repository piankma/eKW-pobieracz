import dataclasses
import logging
import pathlib
from enum import StrEnum

import orjson

log = logging.getLogger("ekw")


class BrowserEnum(StrEnum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"


@dataclasses.dataclass(slots=True)
class Config:
    CONFIG_PATH = pathlib.Path("config.json")
    browser: BrowserEnum = BrowserEnum.CHROME
    log_file: pathlib.Path = "ekw.log"
    db_file: pathlib.Path = "ekw.db"
    out_dir: pathlib.Path = "output"
    save_pdf: bool = True
    save_png: bool = False
    save_txt: bool = False

    def save(self):
        data = dataclasses.asdict(self)
        json = orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
        self.CONFIG_PATH.write_bytes(json)
        log.info(f"Zapisano konfigurację do {self.CONFIG_PATH.absolute()}")

    @classmethod
    def load(cls):
        if not cls.CONFIG_PATH.exists():
            log.info("Zapisuję domyślną konfigurację")
            cls().save()

        log.info(f"Ładowanie konfiguracji z pliku {cls.CONFIG_PATH.absolute()}")

        # load settings from the file
        cfg = orjson.loads(cls.CONFIG_PATH.read_bytes())
        data = cls(
            browser=BrowserEnum(cfg["browser"]),
            log_file=pathlib.Path(cfg["log_file"]),
            db_file=pathlib.Path(cfg["db_file"]),
            out_dir=pathlib.Path(cfg["out_dir"]),
            save_pdf=cfg["save_pdf"],
            save_png=cfg["save_png"],
        )

        for folder in (data.out_dir,):
            if not folder.exists():
                folder.mkdir(parents=True, exist_ok=True)
                log.info(f"Utworzono folder {folder.absolute()}")

        return data


@dataclasses.dataclass(slots=True, frozen=True)
class Constants:
    CONST_PATH = pathlib.Path("etc/constants.json")
    regions: list[str, str]

    @classmethod
    def load(cls):
        if not cls.CONST_PATH.exists():
            raise FileNotFoundError(f"File not found: {cls.CONST_PATH}")

        log.info(f"Ładowanie stałych z pliku {cls.CONST_PATH.absolute()}")
        # load constants from the file
        cfg = orjson.loads(cls.CONST_PATH.read_bytes())
        return cls(
            regions=cfg["regions"],
        )

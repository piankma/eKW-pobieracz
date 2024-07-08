import base64
import logging
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import InvalidArgumentException, NoSuchElementException

from ekw.utils.config import Config, BrowserEnum

config = Config()
log = logging.getLogger("ekw")


class ScraperProcess:
    _BROWSER_DRIVER = None

    def __init__(self, ekw: str):
        self.ekw = ekw
        self.ekw_reg, self.ekw_num, self.ekw_crc = self.ekw.split("/")
        self.data = {}

    @property
    def _browser_chrome(self):
        opts = webdriver.ChromeOptions()
        return webdriver.Chrome(options=opts)

    @property
    def browser(self) -> webdriver.Chrome | webdriver.Firefox | webdriver.Edge:
        """
        Configure the browser driver based on the configuration.

        Returns:
            WebDriver: The configured browser driver.
        """
        if not self._BROWSER_DRIVER:
            if config.browser == BrowserEnum.CHROME:
                self._BROWSER_DRIVER = self._browser_chrome
            else:
                raise NotImplementedError("Tylko Chrome jest wspierany (na razie)")

        return self._BROWSER_DRIVER

    def save(self, filename: str):
        dir = (Path(config.out_dir) / self.ekw_reg / self.ekw_num).absolute()
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
            log.debug(f"Tworzę folder {dir}...")

        if config.save_pdf:
            self._save_to_pdf(f"{dir / filename}.pdf")

        if config.save_png:
            self._save_to_png(f"{dir / filename}.png")

        if config.save_txt:
            self._save_to_txt(f"{dir / filename}.txt")

    def _save_to_pdf(self, filename: str):
        print_opts = PrintOptions()
        print_opts.page = "A4"
        print_opts.orientation = "landscape"
        print_opts.shrink_to_fit = True
        data = self.browser.print_page(print_opts)
        with open(filename, "wb") as f:
            data = base64.b64decode(data)
            f.write(data)

    def _save_to_png(self, filename: str):
        self.browser.save_full_page_screenshot(filename)

    def _save_to_txt(self, filename: str):
        with open(f"{filename}.txt", "w", encoding="utf-8") as f:
            f.write(self.browser.find_element(By.XPATH, "//body").text)

    def _append_csv(self):
        with open("output.csv", "a", encoding="utf-8") as f:
            loc = self.data.get("loc", ["", ""])

            data = ""
            data += self.data.get("numer_ksiegi", "")
            data += ";"
            data += self.data.get("typ_ksiegi", "")
            for i in loc:
                data += f";{i}"
            if len(loc) != 6:
                data += ";" * (6 - len(loc))

            if wl := self.data.get("wlasciciel", ""):
                data += wl.replace("\n", ";")

            f.write(data + "\n")

    def find_wait(self, value: str, by: By = By.CSS_SELECTOR, wait_seconds: int = 60):
        """Returns the element found by the given method and value after waiting for it to be present."""
        wdw = WebDriverWait(self.browser, wait_seconds)
        method = expected_conditions.presence_of_element_located
        return wdw.until(method((by, value)))  # noqa

    def _proc_prepare(self):
        self.browser.get(
            "https://przegladarka-ekw.ms.gov.pl/eukw_prz/KsiegiWieczyste/wyszukiwanieKW"
        )

        if self.browser.page_source.find("The requested URL was rejected") > 0:
            log.error("Odrzucono żądanie, nakryli cię! Chwila przerwy...")
            time.sleep(3 * 60)  # 3min
            self._proc_prepare()
            return

        log.debug("  Wklejam dane do formularza")
        self.find_wait("#kodWydzialuInput").send_keys(self.ekw_reg)
        self.find_wait("#numerKsiegiWieczystej").send_keys(self.ekw_num)
        self.find_wait("#cyfraKontrolna").send_keys(self.ekw_crc)
        self.find_wait("#wyszukaj").click()

        if "nie została odnaleziona" in self.find_wait("div.section").text:
            log.warning(f"Nie znaleziono księgi {self.ekw}")
            raise FileNotFoundError(f"Nie znaleziono księgi {self.ekw}")

        self.data["numer_ksiegi"] = self.find_wait(
            "#content-wrapper > div > div:nth-child(4) > div:nth-child(1) > div.content-column-50 > div"
        ).text
        self.data["typ_ksiegi"] = self.find_wait(
            "#content-wrapper > div > div:nth-child(4) > div:nth-child(2) > div.content-column-50 > div"
        ).text

        try:
            self.data["loc"] = self.browser.find_element(
                By.CSS_SELECTOR,
                "#content-wrapper > div > div:nth-child(4) > div:nth-child(6) > div.content-column-50 > div > p",
            ).text
            self.data["loc"] = self.data["loc"].strip().split(",")
        except (InvalidArgumentException, NoSuchElementException):
            self.data["loc"] = ["", ""]

        try:
            self.data["wlasciciel"] = self.browser.find_element(
                By.CSS_SELECTOR,
                "#content-wrapper > div > div:nth-child(4) > div:nth-child(7) > div.content-column-50 > div",
            ).text.strip()
        except (InvalidArgumentException, NoSuchElementException):
            self.data["wlasciciel"] = ""

        self._append_csv()

        self.find_wait("#przyciskWydrukZwykly").click()

    def _proc_section_1(self):
        self.find_wait('input[value="Dział I-O"]').click()
        log.debug("  Pobieram dział I-O")
        self.save("dzial_I-O")

    def _proc_section_1sp(self):
        self.find_wait('input[value="Dział I-Sp"]').click()
        log.debug("  Pobieram dział I-Sp")
        self.save("dzial_I-Sp")

    def _proc_section_2(self):
        self.find_wait('input[value="Dział II"]').click()
        log.debug("  Pobieram dział II")
        self.save("dzial_II")

    def _proc_section_3(self):
        self.find_wait('input[value="Dział III"]').click()
        log.debug("  Pobieram dział III")
        self.save("dzial_III")

    def _proc_section_4(self):
        self.find_wait('input[value="Dział IV"]').click()
        log.debug("  Pobieram dział IV")
        self.save("dzial_IV")

    def start(self):
        try:
            self._proc_prepare()
        except FileNotFoundError:
            return  # skip the rest of the process, the book was not found

        self._proc_section_1()
        self._proc_section_1sp()
        self._proc_section_2()
        self._proc_section_3()
        self._proc_section_4()

        self.browser.quit()


# if __name__ == "__main__":
#     setup_logging()
#
#     sp = ScraperProcess("OS1O/00000019/7")
#     sp.start()

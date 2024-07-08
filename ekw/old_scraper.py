import base64
import concurrent.futures
import logging
import multiprocessing
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from ekw.utils.config import Config, BrowserEnum
from ekw.utils.sum import find_crc

log = logging.getLogger("ekw")


class Scraper:
    def __init__(self):
        self._cfg = Config().load()

        if self._cfg.browser == BrowserEnum.CHROME:
            opts = webdriver.ChromeOptions()
            self.driver = webdriver.Chrome(options=opts)
        else:
            raise NotImplementedError("Tylko Chrome jest wspierany (na razie)")

    def find(self, by, value):
        wdw = WebDriverWait(self.driver, 60)
        method = expected_conditions.presence_of_element_located
        return wdw.until(method((by, value)))

    def _save_to_pdf(self, filename: str):
        print_opts = PrintOptions()
        print_opts.page = "A4"
        print_opts.orientation = "landscape"
        print_opts.shrink_to_fit = True
        data = self.driver.print_page(print_opts)
        with open(filename, "wb") as f:
            data = base64.b64decode(data)
            f.write(data)

    def _ekw_path(self, ekw_id: str) -> str:
        """
        Returns the path to the EKW file storage.
        """
        ekw_reg, ekw_num, ekw_crc = ekw_id.split("/")
        path = self._cfg.out_dir / ekw_reg / f"{ekw_num}-{ekw_crc}/"
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            log.info(f"Tworzę folder {path}...")

        return str(path)

    def _save_files(self, ekw_id, filename):
        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "/Dział I-Sp.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(
                self._ekw_path(ekw_id) + "/Dział I-Sp.png"
            )

    def start(self, ekw_id: str):
        log.info(f"Rozpoczynam pobieranie {ekw_id}...")

        ekw_reg, ekw_num, ekw_sum = ekw_id.split("/")

        self.driver.get(
            "https://przegladarka-ekw.ms.gov.pl/eukw_prz/KsiegiWieczyste/wyszukiwanieKW"
        )

        if self.driver.page_source.find("The requested URL was rejected") > 0:
            log.error(f"Nie można pobrać księgi {ekw_id}, przerwa na papieroska...")
            time.sleep(3 * 60)  # 3min
            return

        log.debug("  Wklejam dane do formularza...")
        self.find(By.CSS_SELECTOR, "#kodWydzialuInput").send_keys(ekw_reg)
        self.find(By.CSS_SELECTOR, "#numerKsiegiWieczystej").send_keys(ekw_num)
        self.find(By.CSS_SELECTOR, "#cyfraKontrolna").send_keys(ekw_sum)
        self.find(By.CSS_SELECTOR, "#wyszukaj").click()

        if "nie została odnaleziona" in self.find(By.CSS_SELECTOR, "div.section").text:
            log.warning(f"Nie znaleziono księgi {ekw_id}")
            return

        log.debug("  Klikam przycisk 'Wydruk zwykły'...")
        self.find(By.CSS_SELECTOR, "#przyciskWydrukZwykly").click()
        self._scrap_section_1(ekw_id)
        self._scrap_section_1sp(ekw_id)
        self._scrap_section_2(ekw_id)
        self._scrap_section_3(ekw_id)
        self._scrap_section_4(ekw_id)

    def _scrap_section_1(self, ekw_id: str) -> dict:
        # scrap section 1
        self.find(By.CSS_SELECTOR, 'input[value="Dział I-O"]').click()
        log.debug("  Pobieram dział I-O...")

        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "/Dział I-O.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(
                self._ekw_path(ekw_id) + "/Dział I-O.png"
            )

    def _scrap_section_1sp(self, ekw_id: str) -> dict:
        # scrap section 1sp
        self.find(By.CSS_SELECTOR, 'input[value="Dział I-Sp"]').click()
        log.debug("  Pobieram dział I-Sp...")

    def _scrap_section_2(self, ekw_id: str):
        # scrap section 2
        self.find(By.CSS_SELECTOR, 'input[value="Dział II"]').click()
        log.debug("  Pobieram dział II...")

        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "/Dział II.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(self._ekw_path(ekw_id) + "/Dział II.png")

    def _scrap_section_3(self, ekw_id: str):
        # scrap section 3
        self.find(By.CSS_SELECTOR, 'input[value="Dział III"]').click()
        log.debug("  Pobieram dział III...")

        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "/Dział III.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(
                self._ekw_path(ekw_id) + "/Dział III.png"
            )

    def _scrap_section_4(self, ekw_id: str):
        # scrap section 4
        self.find(By.CSS_SELECTOR, 'input[value="Dział IV"]').click()
        log.debug("  Pobieram dział IV...")

        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "/Dział IV.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(self._ekw_path(ekw_id) + "/Dział IV.png")


def _start(i):
    s = Scraper()
    crc = find_crc("OS1O/" + str(i).zfill(8))
    s.start(f"OS1O/{str(i).zfill(8)}/{crc}")


if __name__ == "__main__":
    from ekw.utils.logging import setup_logging

    setup_logging()

    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        # executor.map(_start, range(99999999))
        for j in range(0, 99999999):
            executor.submit(_start, j)

    # s.start("KR1P/00286974/1")
    # s.start("OS1M/00005748/9")

import base64
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from ekw.utils.settings import Settings, BrowserEnum
from ekw.utils.sum import find_crc

log = logging.getLogger("ekw")


class Scraper:
    def __init__(self):
        self._cfg = Settings().load()

        if self._cfg.browser == BrowserEnum.CHROME:
            opts = webdriver.ChromeOptions()
            opts.headless = True
            opts.version_main = 126
            opts.set_window_rect = (1920, 1080)
            opts.add_argument("--headless=new")
            self.driver = webdriver.Chrome(options=opts)
        else:
            raise NotImplementedError("Tylko Chrome jest wspierany (na razie)")

        wdw = WebDriverWait(self.driver, 60)
        method = expected_conditions.presence_of_element_located
        self.find = lambda by, selector: wdw.until(method((by, selector)))

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
        path = self._cfg.out_dir / ekw_id.split("/")[0] / f"{ekw_id[1]}-{ekw_id[2]}/"
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            log.info(f"Tworzę folder {path}...")

        return str(path)

    def start(self, ekw_id: str):
        log.info(f"Rozpoczynam pobieranie {ekw_id}...")

        ekw_reg, ekw_num, ekw_sum = ekw_id.split("/")

        self.driver.get(
            "https://przegladarka-ekw.ms.gov.pl/eukw_prz/KsiegiWieczyste/wyszukiwanieKW"
        )
        self.find(By.CSS_SELECTOR, "#kodWydzialuInput").send_keys(ekw_reg)
        self.find(By.CSS_SELECTOR, "#numerKsiegiWieczystej").send_keys(ekw_num)
        self.find(By.CSS_SELECTOR, "#cyfraKontrolna").send_keys(ekw_sum)
        self.find(By.CSS_SELECTOR, "#wyszukaj").click()

        if "nie została odnaleziona" in self.find(By.CSS_SELECTOR, "div.section").text:
            log.warning(f"Nie znaleziono księgi {ekw_id}")
            return

        self.find(By.CSS_SELECTOR, "#przyciskWydrukZwykly").click()
        self._scrap_section_1(ekw_id)
        self._scrap_section_1sp(ekw_id)
        self._scrap_section_2(ekw_id)
        self._scrap_section_3(ekw_id)
        self._scrap_section_4(ekw_id)

    def _scrap_section_1(self, ekw_id: str) -> dict:
        # scrap section 1
        self.find(By.CSS_SELECTOR, 'input[value="Dział I-O"]').click()

        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "Dział I-O.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(self._ekw_path(ekw_id) + "Dział I-O.png")

    def _scrap_section_1sp(self, ekw_id: str) -> dict:
        # scrap section 1sp
        self.find(By.CSS_SELECTOR, 'input[value="Dział I-Sp"]').click()

        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "Dział I-Sp.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(
                self._ekw_path(ekw_id) + "Dział I-Sp.png"
            )

    def _scrap_section_2(self, ekw_id: str):
        # scrap section 2
        self.find(By.CSS_SELECTOR, 'input[value="Dział II"]').click()

        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "Dział II.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(self._ekw_path(ekw_id) + "Dział II.png")

    def _scrap_section_3(self, ekw_id: str):
        # scrap section 3
        self.find(By.CSS_SELECTOR, 'input[value="Dział III"]').click()

        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "Dział III.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(self._ekw_path(ekw_id) + "Dział III.png")

    def _scrap_section_4(self, ekw_id: str):
        # scrap section 4
        self.find(By.CSS_SELECTOR, 'input[value="Dział IV"]').click()

        if self._cfg.save_pdf:
            self._save_to_pdf(self._ekw_path(ekw_id) + "Dział IV.pdf")

        if self._cfg.save_png:
            self.driver.get_screenshot_as_file(self._ekw_path(ekw_id) + "Dział IV.png")


if __name__ == "__main__":
    from ekw.utils.logging import setup_logging

    setup_logging()

    s = Scraper()
    for i in range(99999999):
        crc = find_crc("OS1O/" + str(i).zfill(8))
        s.start(f"OS1O/{str(i).zfill(8)}/{crc}")

    # s = Scraper()
    # s.start("KR1P/00286974/1")
    # # s.start("OS1M/00005748/9")

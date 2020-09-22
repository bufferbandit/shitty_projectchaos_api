#!/usr/bin/python3
import inspect
import os
import sys
import requests
import tempfile
import threading
import zipfile
from collections import OrderedDict
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from terminaltables import AsciiTable, SingleTable
from threading import Lock
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By




class CHAOS:

    def __init__(self, piped=False):
        self.base_url = "https://chaos.projectdiscovery.io/"
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        #sleep(3)
        self.table_list = []
        self.all_urls = []
        self.threads = []
        self.lock = Lock()
        self.piped = piped

    def run(self):
        if self.piped:
            for element in self.driver.find_elements_by_tag_name("input"):
                zip_url = element.get_attribute("value")
                if zip_url.startswith("http"):
                    threading.Thread(
                        target=self.process_zip_file, args=(zip_url,)).start()
        else:
            self.add_to_table()
            print(SingleTable(c.table_list).table)

    def process_row(self, row):
        sleep(0.5)
        self.lock.acquire()
        self.table_list.append([
            colmn.text for colmn in row.find_elements_by_class_name("ReactVirtualized__Table__rowColumn") if colmn.text]
            + [row.find_element_by_tag_name("input").get_attribute("value")])
        self.lock.release()
        #zip_url = self.table_list[-1][4]
        # threading.Thread(target=self.process_zip_file,args=(zip_url,)).start()
        return

    def process_zip_file(self, url):
        zip_path = self.download_zip(url)
        self.extract_zip(zip_path)

    def extract_zip(self, zip_path):
        zip_file = zipfile.ZipFile(zip_path)
        for zipped_file_name in zip_file.namelist():
            zipped_file = zip_file.read(zipped_file_name)
            zip_lines = zipped_file.decode("utf-8")  # .split("\n")
            #for zip_line in zip_lines:print(zip_line)
            #self.all_urls += all_urls
            print(zip_lines)
        os.remove(zip_path)

    def download_zip(self, url):
        r = requests.get(url, stream=True)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            for chunk in r.iter_content(1024):
                if chunk:
                    temp_file.write(chunk)
            temp_file.close()
            return temp_file.name

    def add_to_table(self):
        table = self.driver.find_element_by_class_name(
            "ReactVirtualized__Grid__innerScrollContainer")
        self.table_list.append(["Program Name", "Offers Reward",
                                "No. Subdomains", "Last Updated", "Url"])
        for row in table.find_elements_by_class_name("ReactVirtualized__Table__row"):
            # self.process_row(row)
            t = threading.Thread(target=self.process_row, args=(row,))
            self.threads.append(t)
            t.start()
        for thread in self.threads:
            thread.join()

    def search(self, searchtherm, timeout=0.075):
        search_field = self.driver.find_element_by_id("search_input")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "search_input")))
        for l in searchtherm:
            search_field.send_keys(l)
            sleep(timeout)

    def scroll_down(self):
        actions = ActionChains(self.driver)
        last_program = self.table_list[-1][0]
        self.add_to_table()
        table = self.driver.find_element_by_class_name("scan_jobs_table")
        table.click()
        actions.send_keys(Keys.PAGE_DOWN).perform()

    def filter(self, all=False, new_programs=False, new_subdomains=False, hackerone=False, bugcrowd=False, with_rewards=False, no_rewards=False):
        values = inspect.getargvalues(inspect.currentframe())[3]
        selecteds = [key.replace("_", " ")
                     for key in values.keys() if values[key]]
        for element in self.driver.find_elements_by_class_name("filter_bar_item___1M9rw"):
            if element.text in selecteds:
                element.click()


if __name__ == "__main__":
    c = CHAOS(piped=True)
    c.search(sys.argv[1])
    c.run()
    c.driver.quit()

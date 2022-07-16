from selenium import webdriver

from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By


from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.support.wait import WebDriverWait
from browsermobproxy import Server
import getpass


class chrome_driver(object):
    def __init__(self):
        # options = Options()
        #
        # self.driver = webdriver.Firefox(options=options)

        if getpass.getuser()=='zhazekun':
            server_loc = r'W:\My Documents\Oculus\browsermob-proxy-2.1.4-bin\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat'
        else:
            server_loc = r'browsermob-proxy-2.1.4\bin\browsermob-proxy.bat'
        self.server = Server(
            server_loc,\
            options={'port':8286})
        self.server.start()
        self.proxy = self.server.create_proxy()
        chrome_options = Options()
        chrome_options.add_argument('disable-infobars')
        chrome_options.add_argument('--ignore-ssl-errors=yes')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--proxy-server={0}'.format(self.proxy.proxy))
        chrome_options.binary_location = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
        chrome_path = os.environ['USERPROFILE'] + r'\AppData\Local\Google\Chrome\User Data'
        chrome_options.add_argument("user-data-dir=" + chrome_path)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 300)
    def get_url(self, url):
        try:
            self.driver.get(url)
            while 'midway' in self.driver.current_url:
                time.sleep(20)
        except:
            self.get_url(url)

    def clickable_click(self, xpath):
        self.wait.until(
            EC.element_to_be_clickable((
                By.XPATH, xpath
            ))).click()

    def wait_until_located(self, xpath):
        item = self.wait.until(
            EC.presence_of_element_located((
                By.XPATH, xpath
            ))
        )
        return item

    def close(self):
        self.driver.quit()
        self.proxy.close()
        self.server.stop()

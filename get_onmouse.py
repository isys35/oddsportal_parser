from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options

url = 'https://www.oddsportal.com/soccer/africa/africa-cup-of-nations-2008/cameroon-egypt-I1u1cV7k/'
options = Options()
options.headless = False

browser = webdriver.Firefox(options=options)
browser.get(url)
initial_odd_data = browser.find_element_by_css_selector('td.right.odds.up')
hov = ActionChains(browser).move_to_element(initial_odd_data)
hov.perform()
requiredHtml = browser.page_source
soup = BeautifulSoup(requiredHtml, 'html.parser')
help_box = soup.select('span.help')
print(help_box)



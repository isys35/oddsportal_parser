import requests
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sqlite3

options = Options()
options.headless = True
soccer_url = 'https://www.oddsportal.com/results/#soccer'
bookmaker_url = 'https://www.oddsportal.com/bookmakers/'
import time
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'
}
db = 'oddsportal.db'

def main():
    r = requests.get(soccer_url, headers=headers)
    html = BS(r.content, 'html.parser')
    body = html.select('table.table-main.sport')
    print(body)
    matches = body[0].select('td')
    for match in matches:
        if len(match.select('a'))>0:
            href_liga = match.select('a')[0]['href']
            if href_liga.split('/')[1] == 'soccer':
                liga_request = requests.get('https://www.oddsportal.com' +href_liga, headers=headers)
                soup_liga = BS(liga_request.content, 'html.parser')




def parsing_bookmaker():
    r = requests.get(bookmaker_url, headers=headers)
    html = BS(r.content, 'html.parser')
    bookmakers = html.select('a.no-ext') #
    for bookmaker in bookmakers:
        if bookmaker.text:
            add_bookmaker_in_db(bookmaker.text)

def add_bookmaker_in_db(name: str):
    con = sqlite3.connect('oddsportal.db')
    cur = con.cursor()
    query = 'SELECT * FROM bookmaker'
    cur.execute(query)
    data_name = [name[1] for name in cur.fetchall()]
    print(data_name)
    if name in data_name:
        print('[INFO] %s букмекер уже есть в базе' %name)
    else:
        cur.execute('INSERT INTO bookmaker (name) VALUES(?)', [name])
        con.commit()
        print('[INFO] Букмекер %s добавлен в базу' % name)
    cur.close()
    con.close()

main()


#     # for country in countrys:
#     #     if str(country['style']) == 'display: table-row;':
#     #         print(country['class'])
#     # print(len(countrys))
#     time.sleep(5)
#     browser.close()
#main()
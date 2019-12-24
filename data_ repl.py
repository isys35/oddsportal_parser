import requests
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sqlite3
from selenium.webdriver.common.action_chains import ActionChains

options = Options()
options.headless = False
soccer_url = 'https://www.oddsportal.com/results/#soccer'
bookmaker_url = 'https://www.oddsportal.com/bookmakers/'
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'
}
db = 'oddsportal.db'

def main():
    browser = webdriver.Firefox(options=options)
    r = requests.get(soccer_url, headers=headers)
    html = BS(r.content, 'html.parser')
    body = html.select('table.table-main.sport')
    ligs = body[0].select('td')
    for lig in ligs:
        if len(lig.select('a'))>0:
            href_liga = lig.select('a')[0]['href']
            if href_liga.split('/')[1] == 'soccer':
                liga_request_allyears = requests.get('https://www.oddsportal.com' + href_liga, headers=headers)
                soup_liga = BS(liga_request_allyears.content, 'html.parser')
                years_menu = soup_liga.select('.main-menu2.main-menu-gray')
                years_pages = years_menu[0].select('a')
                browser.get('https://www.oddsportal.com' + years_pages[0]['href'])
                content_browser = browser.page_source
                soup_liga = BS(content_browser, 'html.parser')
                breadcrump = soup_liga.select('#breadcrumb')
                breadcrump_a = breadcrump[0].select('a')
                liga = breadcrump_a[3].text
                for page in years_pages:
                    print(page['href'])
                    browser.get('https://www.oddsportal.com' + page['href'])
                    content_browser = browser.page_source
                    soup_liga = BS(content_browser, 'html.parser')
                    if len(soup_liga.select('#pagination')) == 0:
                        matches = soup_liga.select('td.name.table-participant')
                    else:
                        matches = soup_liga.select('td.name.table-participant')
                        max_page = soup_liga.select('#pagination')[0].select('a')[-1]['x-page']
                        p = 2
                        while p != int(max_page):
                            browser.get('https://www.oddsportal.com' + page['href'] + '#/page/%s/' % str(p))
                            content_browser = browser.page_source
                            soup_liga = BS(content_browser, 'html.parser')
                            matches += soup_liga.select('td.name.table-participant')
                            p += 1
                    for match in matches:
                        match_url ='https://www.oddsportal.com' + match.select('a')[0]['href']
                        print(match_url)
                        browser.get(match_url)
                        content_match = browser.page_source
                        soup_liga = BS(content_match, 'html.parser')
                        col_content = soup_liga.select('#col-content')
                        name = col_content[0].select('h1')[0].text
                        print(name)
                        date = col_content[0].select('p.date')[0].text
                        print(date)
                        try:
                            result = col_content[0].select('p.result')[0].text
                        except IndexError:
                            result = 'Canceled'
                        print(result)
                        breadcrump = soup_liga.select('#breadcrumb')
                        breadcrump_a = breadcrump[0].select('a')
                        sport = breadcrump_a[1].text
                        country = breadcrump_a[2].text
                        print(liga)
                        print(sport)
                        print(country)
                        data_parsing = [name, match_url, date, result, sport, country, liga]
                        if not add_game_in_db(data_parsing):
                            continue
                        table_odds = soup_liga.select('table.table-main.detail-odds')
                        bets = table_odds[0].select('tr.lo')
                        bets_dict = {}

                        right_odds = table_odds[0].select('td.right.odds')
                        right_odds_browser = browser.find_elements_by_css_selector('td.right.odds')

                        for bet in bets:
                            bookmaker = bet.select('a.name')[0].text
                            print(bookmaker)
                            right_odds_bet = bet.select('td.right.odds')
                            odds_list = []
                            for odd in right_odds_bet:
                                try:
                                    if odd.select('div')[0]['onmouseout'] == "delayHideTip()":
                                        index = right_odds.index(odd)
                                        hov = ActionChains(browser).move_to_element(right_odds_browser[index])
                                        hov.perform()
                                        content_bet = browser.page_source
                                        soup = BS(content_bet, 'html.parser')
                                        help_box = soup.select('span.help')[0].text
                                        open_odds = help_box.split(' ')[-1]
                                        odds_list.append(open_odds)
                                        print(open_odds)
                                except KeyError:
                                    open_odds = odd.select('div')[0].text
                                    odds_list.append(open_odds)
                                    print(open_odds)
                            bets_dict[bookmaker] = odds_list
                        print(bets_dict)
                        add_bet_in_db(bets_dict,data_parsing)
    browser.quit()





def parsing_bookmaker():
    r = requests.get(bookmaker_url, headers=headers)
    html = BS(r.content, 'html.parser')
    bookmakers = html.select('a.no-ext') #
    for bookmaker in bookmakers:
        if bookmaker.text:
            add_bookmaker_in_db(bookmaker.text)


def add_game_in_db(data_parsing: list):
    con = sqlite3.connect('oddsportal.db')
    cur = con.cursor()
    query = 'SELECT name,url,date,result,sport,country,liga FROM game'
    cur.execute(query)
    data_game = [[el for el in name] for name in cur.fetchall()]
    if data_parsing in data_game:
        print('[INFO] %s игра уже есть в базе' % data_parsing[0])
        cur.close()
        con.close()
        return False
    else:
        cur.execute('INSERT INTO game (name,url,date,result,sport,country,liga) '
                    'VALUES(?,?,?,?,?,?,?)', data_parsing)
        con.commit()
        print('[INFO] игра %s добавлен в базу' % data_parsing[0])
        cur.close()
        con.close()
        return True

def add_bet_in_db(bets_dict:dict,data_parsing: list):
    con = sqlite3.connect('oddsportal.db')
    cur = con.cursor()
    query = 'SELECT id,name,url,date,result,sport,country,liga FROM game'
    cur.execute(query)
    data_game_dict = {}
    for game in cur.fetchall():
        data_game_dict[game[0]] = [el for el in game[1:]]
    key_game = None
    for key, item in data_game_dict.items():
        if item == data_parsing:
            key_game = key
            break
    for key, item in bets_dict.items():
        add_bookmaker_in_db(key)
        key_bookmaker = None
        query = 'SELECT * FROM bookmaker'
        cur.execute(query)
        data_bookmakers = [[el for el in bookmaker] for bookmaker in cur.fetchall()]
        for bookmaker in data_bookmakers:
            if bookmaker[1] == key:
                key_bookmaker = bookmaker[0]
                break
        data_out = [key_bookmaker, item[0], item[1], item[2], key_game]
        cur.execute('INSERT INTO bet (bookmaker_id,p1,x,p2,game_id) VALUES(?,?,?,?,?)', data_out)
        con.commit()
        print('[INFO] Ставка добавлена в базу')
    cur.close()
    con.close()


def add_bookmaker_in_db(name: str):
    con = sqlite3.connect('oddsportal.db')
    cur = con.cursor()
    query = 'SELECT * FROM bookmaker'
    cur.execute(query)
    data_name = [name[1] for name in cur.fetchall()]
    if name in data_name:
        print('[INFO] %s букмекер уже есть в базе' % name)
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
import requests
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sqlite3
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import time

class Parser:

    def start(self):
        options = Options()
        options.headless = False
        soccer_url = 'https://www.oddsportal.com/results/#soccer'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'
        }
        browser = webdriver.Firefox(options=options)
        browser.set_window_size(1000, 1000)
        r = requests.get(soccer_url, headers=headers)
        html = BS(r.content, 'html.parser')
        body = html.select('table.table-main.sport')
        ligs = body[0].select('td')
        for lig in ligs:
            if len(lig.select('a')) > 0:
                href_liga = lig.select('a')[0]['href']
                if href_liga.split('/')[1] == 'soccer':
                    liga_request_allyears = requests.get('https://www.oddsportal.com' + href_liga, headers=headers)
                    soup_liga = BS(liga_request_allyears.content, 'html.parser')
                    years_menu = soup_liga.select('.main-menu2.main-menu-gray')
                    if years_menu:
                        years_pages = years_menu[0].select('a')
                        browser.get('https://www.oddsportal.com' + years_pages[0]['href'])
                        content_browser = browser.page_source
                        soup_liga = BS(content_browser, 'html.parser')
                        breadcrump = soup_liga.select('#breadcrumb')
                        breadcrump_a = breadcrump[0].select('a')
                        sport = breadcrump_a[1].text
                        country = breadcrump_a[2].text
                        liga = breadcrump_a[3].text
                        print('Страна '+country)
                        print('Чемпионат '+liga)
                        for page in years_pages:
                            year_page = 'https://www.oddsportal.com' + page['href']
                            print(year_page)
                            browser.get(year_page)
                            page_pagination = BS(browser.page_source, 'html.parser')
                            pagination = page_pagination.select('#pagination')
                            try:
                                if len(pagination) == 0:
                                    self.get_liga_data_in_year(year_page, browser, sport, country, liga)
                                else:
                                    print('Страница 1')
                                    self.get_liga_data_in_year(year_page, browser, sport, country, liga)
                                    max_page = pagination[0].select('a')[-1]['x-page']
                                    p = 2
                                    while p != int(max_page):
                                        print('Страница '+str(p))
                                        year_page_add = 'https://www.oddsportal.com' + page[
                                            'href'] + '#/page/%s/' % str(p)
                                        self.get_liga_data_in_year(year_page_add, browser, sport, country, liga)
                                        p += 1
                            except TimeoutException:
                                print('[EROR] TimeoutException')
        browser.quit()

    def check_game_in_db(self, url: str):
        con = sqlite3.connect('oddsportal2.db')
        cur = con.cursor()
        query = 'SELECT url FROM game'
        cur.execute(query)
        data_game = [game[0] for game in cur.fetchall()]
        if url in data_game:
            print('[INFO] %s игра уже есть в базе' % str(url))
            cur.close()
            con.close()
            return True
        else:
            cur.close()
            con.close()
            return False

    def get_match_data(self, url: str, browser):
        browser.get(url)
        content_match = browser.page_source
        soup_liga = BS(content_match, 'html.parser')
        col_content = soup_liga.select('#col-content')
        try:
            result = col_content[0].select('p.result')[0].text
        except IndexError:
            result = 'Canceled'
        table_odds = soup_liga.select('table.table-main.detail-odds')
        if len(table_odds) > 0:
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
                            try:
                                help_box = soup.select('span.help')[0].text
                                open_odds = help_box.split(' ')[-1]
                            except IndexError:
                                open_odds = odd.select('div')[0].text
                            odds_list.append(open_odds)
                            print(open_odds)
                    except KeyError:
                        open_odds = odd.select('div')[0].text
                        odds_list.append(open_odds)
                        print(open_odds)
                bets_dict[bookmaker] = odds_list
            return [result, bets_dict]
        else:
            bets_dict = {}
            return [result, bets_dict]

    def get_liga_data_in_year(self, url, browser, sport, country, liga):
        print(url)
        date = None
        browser.get(url)
        time.sleep(2)
        content_browser = browser.page_source
        soup_liga = BS(content_browser, 'html.parser')
        table_matchs = soup_liga.select('#tournamentTable')[0]
        trs = table_matchs.select('tr')
        for tr in trs:
            try:
                if tr['class'] == ['center', 'nob-border']:
                    date = tr.select('span')[0].text
                elif 'deactivate' in tr['class']:
                    if len(tr.select('span.live-odds-ico-prev')) == 0:
                        timematch = tr.select('td.table-time')[0].text
                        match_url = 'https://www.oddsportal.com' + tr.select('a')[0]['href']
                        game_name = tr.select('a')[0].text
                        print(game_name)
                        command1 = game_name.split(' - ')[0]
                        command2 = game_name.split(' - ')[1]
                        # check_list = [command1, command2, match_url, date, timematch, sport, country, liga]
                        if self.check_game_in_db(match_url):
                            continue
                        else:
                            match_data = self.get_match_data(match_url, browser)
                            out_match = [command1,
                                         command2,
                                         match_url,
                                         date,
                                         timematch,
                                         match_data[0],
                                         sport,
                                         country,
                                         liga]
                            print(match_url)
                            self.add_game_in_db(out_match)
                            self.add_bet_in_db(match_data[1], out_match)
            except KeyError:
                print('[WARNING] Not odds')

    def add_game_in_db(self, data_parsing: list):
        con = sqlite3.connect('oddsportal2.db')
        cur = con.cursor()
        cur.execute('INSERT INTO game (command1,command2,url,date,timematch,'
                    'result,sport,country,liga) '
                    'VALUES(?,?,?,?,?,?,?,?,?)', data_parsing)
        con.commit()
        print('[INFO] игра %s добавлен в базу' % str(data_parsing[0:2]))
        cur.close()
        con.close()

    def add_bet_in_db(self, bets_dict: dict, data_parsing: list):
        con = sqlite3.connect('oddsportal2.db')
        cur = con.cursor()
        query = 'SELECT id,command1,command2,url,date,timematch,result,sport,country,liga FROM game'
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
            self.add_bookmaker_in_db(key)
            key_bookmaker = None
            query = 'SELECT * FROM bookmaker'
            cur.execute(query)
            data_bookmakers = [[el for el in bookmaker] for bookmaker in cur.fetchall()]
            for bookmaker in data_bookmakers:
                if bookmaker[1] == key:
                    key_bookmaker = bookmaker[0]
                    break
            data_out = []
            if len(item) == 3:
                data_out = [key_bookmaker, item[0], item[1], item[2], key_game]
            elif len(item) == 2:
                data_out = [key_bookmaker, item[0], 0, item[1], key_game]
            cur.execute('INSERT INTO bet (bookmaker_id,p1,x,p2,game_id) VALUES(?,?,?,?,?)', data_out)
            con.commit()
            print('[INFO] Ставка добавлена в базу')
        cur.close()
        con.close()

    def add_bookmaker_in_db(self, name: str):
        con = sqlite3.connect('oddsportal2.db')
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

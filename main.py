#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread
import requests
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sqlite3
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import mainwindow
import dialog


class MainApp(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.logotypes_path = {
            '18bet': 'logotypes/18bet.png',
            '1xBet': 'logotypes/1xbet.png',
            'Asianodds': 'logotypes/assianodds.png',
            'bet-at-home': 'logotypes/bet_at_home.png',
            'bet365': 'logotypes/bet365.png',
            'Bethard': 'logotypes/bethard.png',
            'bwin': 'logotypes/bwin.png',
            'Coolbet': 'logotypes/coolbet.png',
            'Marathonbet': 'logotypes/marathon_bet.png',
            'MrGreen': 'logotypes/mrgreen.png',
            'Pinnacle': 'logotypes/pinnacle.png',
            'Unibet': 'logotypes/unibet.png',
            'William Hill': 'logotypes/willian_hill.png'
        }

        self.setupUi(self)
        self.con = sqlite3.connect('oddsportal2.db')
        self.data_bookmaker = []
        self.checkboxlist = []
        self.update_bookmakers()
        self.matches_finded = []
        self.games = []
        self.liga_dict = {}
        self.comboBox_2.popupAboutToBeShown.connect(self.update_combobox)
        self.pushButton_3.clicked.connect(self.filtered)
        self.pushButton_2.clicked.connect(self.open_dialog)
        self.pushButton_4.clicked.connect(self.start_thread_parsing)


    def update_bookmakers(self):
        print('[INFO] Берём из базы букмекерские конторы')
        cur = self.con.cursor()
        query = 'SELECT * FROM bookmaker'
        cur.execute(query)
        self.data_bookmaker = [[bookmaker[0], bookmaker[1]] for bookmaker in cur.fetchall()]
        data_bookmaker_checklist = []
        print('[INFO] Получаем кол-во матчей для каждого букмекера')
        for bookmaker in self.data_bookmaker:
            query = 'SELECT * FROM bet WHERE bookmaker_id = ?'
            cur.execute(query, [bookmaker[0]])
            count_bookmaker_match = len(cur.fetchall())
            data_bookmaker_checklist.append([count_bookmaker_match, bookmaker[1]])
        cur.close()
        data_bookmaker_checklist.sort(reverse=True)
        print('[INFO] Строим виджеты CheckBox')
        self.checkboxlist = []
        for bookmaker in data_bookmaker_checklist:
            label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            label.setPixmap(QtGui.QPixmap(self.logotypes_path[bookmaker[1]]))
            self.formLayout_2.setWidget(data_bookmaker_checklist.index(bookmaker),
                                        QtWidgets.QFormLayout.LabelRole, label)
            checkBox = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
            checkBox.setText(bookmaker[1] + ' (' + str(bookmaker[0])+')')
            self.checkboxlist.append(checkBox)
            self.formLayout_2.setWidget(data_bookmaker_checklist.index(bookmaker),
                                        QtWidgets.QFormLayout.FieldRole, checkBox)
            self.verticalLayout.addLayout(self.formLayout_2)
        for check_box in self.checkboxlist:
            check_box.clicked.connect(lambda state, chck = check_box: self.unselect_allcheckbox(chck))
        self.pushButton.clicked.connect(self.find_match)

    def find_match(self):
        select_bk = None
        for check_box in self.checkboxlist:
            if check_box.isChecked():
                select_bk = check_box.text().rsplit(' ', maxsplit=1)[0]
        bookmaker_id = None
        for bk in self.data_bookmaker:
            if bk[1] == select_bk:
                bookmaker_id = bk[0]
                break
        if not select_bk:
            print('[WARNING] Не выбрана букмекерская контора')
            return
        # Добавить разные инфо если не введени какие нибудь из значений
        p1 = self.lineEdit.text()
        x = self.lineEdit_2.text()
        p2 = self.lineEdit_3.text()
        print('[INFO] Поиск в базе игры с букмекером {} П1 = {} X = {} П2 = {}'.format(select_bk, p1, x, p2))
        cur = self.con.cursor()
        query = 'SELECT game_id FROM bet WHERE bookmaker_id = ? AND p1 = ? AND x = ? AND p2 = ?'
        cur.execute(query, [bookmaker_id, p1, x, p2])
        self.matches_finded = [match_id[0] for match_id in cur.fetchall()]
        self.label.setText('Найдено матчей: ' + str(len(self.matches_finded)))
        print('[INFO] Найдено матчей: ' + str(len(self.matches_finded)))
        self.games = []
        if self.matches_finded:
            for game_id in self.matches_finded:
                print(game_id)
                query = 'SELECT * FROM game WHERE id = ?'
                cur.execute(query, [game_id])
                game_data = [el for el in cur.fetchone()]
                self.games.append(game_data)
        p1_out = 0
        p2_out = 0
        x_out = 0
        if self.games:
            for game in self.games:
                result = game[6]
                result_out = result.replace('Final result ','').split(' ')[0]
                p1_r = result_out.split(':')[0]
                p2_r = result_out.split(':')[1]
                if float(p1_r) > float(p2_r):
                    p1_out += 1
                elif float(p1_r) < float(p2_r):
                    p2_out += 1
                elif float(p1_r) == float(p2_r):
                    x_out += 1
        all_out = p1_out + p2_out + x_out
        if all_out:
            p1_out = 100 * p1_out/ all_out
            p2_out = 100 * p2_out / all_out
            x_out = 100 * x_out / all_out
        self.label_6.setText('П1: ' + str(round(p1_out)) + '%')
        self.label_5.setText('X: ' + str(round(x_out)) + '%')
        self.label_7.setText('П2: ' + str(round(p2_out)) + '%')
        self.comboBox.clear()
        countrys = []
        self.liga_dict = {}
        for game in self.games:
            if game[8] not in countrys:
                countrys.append(game[8])
            if game[8] not in self.liga_dict:
                self.liga_dict[game[8]] = [game[9]]
            else:
                if game[9] not in self.liga_dict[game[8]]:
                    self.liga_dict[game[8]].append(game[9])
        print(self.liga_dict)
        self.comboBox.addItems(countrys)
        cur.close()

    def unselect_allcheckbox(self, check_box):
        for check in self.checkboxlist:
            if check != check_box:
                check.setChecked(False)

    def update_combobox(self):
        self.comboBox_2.clear()
        if self.liga_dict:
            self.comboBox_2.addItems(self.liga_dict[self.comboBox.currentText()])

    def filtered(self):
        country = self.comboBox.currentText()
        liga = self.comboBox_2.currentText()
        games_out = []
        for game in self.games:
            if game[8] == country and game[9] == liga:
                games_out.append(game)
        self.games = games_out
        self.label.setText('Найдено матчей: ' + str(len(self.games)))

    def open_dialog(self):
        dialog = Dialog()
        dialog.update_games(self.games)
        dialog.exec_()

    def start_thread_parsing(self):
        self.parsing = ParsingThread()
        self.parsing.start()


class Dialog(QtWidgets.QDialog,dialog.Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def update_games(self, games):
        self.tableWidget.setRowCount(len(games))
        for game in games:
            item_index = QtWidgets.QTableWidgetItem()
            item_index.setText(str(games.index(game)))
            self.tableWidget.setVerticalHeaderItem(games.index(game), item_index)
            item_command1 = QtWidgets.QTableWidgetItem()
            item_command1.setText(game[1])
            self.tableWidget.setItem(games.index(game), 0, item_command1)
            item_command2 = QtWidgets.QTableWidgetItem()
            item_command2.setText(game[2])
            self.tableWidget.setItem(games.index(game), 1, item_command2)
            item_url = QtWidgets.QTableWidgetItem()
            item_url.setText(game[3])
            self.tableWidget.setItem(games.index(game), 2, item_url)
            item_date = QtWidgets.QTableWidgetItem()
            item_date.setText(game[4])
            self.tableWidget.setItem(games.index(game), 3, item_date)
            item_time = QtWidgets.QTableWidgetItem()
            item_time.setText(game[5])
            self.tableWidget.setItem(games.index(game), 4, item_time)
            item_result = QtWidgets.QTableWidgetItem()
            item_result.setText(game[6])
            self.tableWidget.setItem(games.index(game), 5, item_result)
            item_sport = QtWidgets.QTableWidgetItem()
            item_sport.setText(game[7])
            self.tableWidget.setItem(games.index(game), 6, item_sport)
            item_country = QtWidgets.QTableWidgetItem()
            item_country.setText(game[8])
            self.tableWidget.setItem(games.index(game), 7, item_country)
            item_liga = QtWidgets.QTableWidgetItem()
            item_liga.setText(game[9])
            self.tableWidget.setItem(games.index(game), 8, item_liga)




class ParsingThread(QThread):
    def __init__(self):
        super().__init__()

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

    def update_db(self):
        options = Options()
        options.headless = True
        soccer_url = 'https://www.oddsportal.com/results/#soccer'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'
        }
        print('[INFO] Открываем браузер')
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
                        for page in years_pages:
                            year_page = 'https://www.oddsportal.com' + page['href']
                            browser.get(year_page)
                            try:
                                if len(soup_liga.select('#pagination')) == 0:
                                    self.get_liga_data_in_year(year_page, browser, sport, country, liga)
                                else:
                                    max_page = soup_liga.select('#pagination')[0].select('a')[-1]['x-page']
                                    p = 2
                                    while p != int(max_page):
                                        year_page_add = 'https://www.oddsportal.com' + page[
                                            'href'] + '#/page/%s/' % str(p)
                                        self.get_liga_data_in_year(year_page_add, browser, sport, country, liga)
                                        p += 1
                            except TimeoutException:
                                print('[EROR] TimeoutException')
        browser.quit()

    def get_liga_data_in_year(self, url, browser, sport, country, liga):
        date = None
        browser.get(url)
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
                        print(match_url)
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

    def run(self):
        self.update_db()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
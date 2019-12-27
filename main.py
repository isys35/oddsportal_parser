#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import sqlite3
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread

import mainwindow


class MainApp(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.checkBox = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        # self.checkBox.setObjectName("checkBox")
        # self.verticalLayout.addWidget(self.checkBox)
        # self.widget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        # self.widget.setObjectName("widget")
        # self.verticalLayout.addWidget(self.widget)
        self.con = sqlite3.connect('oddsportal2.db')
        self.data_bookmaker = []
        self.checkboxlist = []
        self.update_bookmakers()
        self.matches_finded = []
        self.games = []
        self.liga_dict = {}
        self.comboBox_2.popupAboutToBeShown.connect(self.update_combobox)

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
            checkBox = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
            checkBox.setObjectName("checkBox{}".format(str(data_bookmaker_checklist.index(bookmaker))))
            checkBox.setText(bookmaker[1] + ' (' + str(bookmaker[0])+')')
            self.checkboxlist.append(checkBox)
            self.verticalLayout.addWidget(checkBox)
            widget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
            widget.setObjectName("widget")
            self.verticalLayout.addWidget(widget)
        for check_box in self.checkboxlist:
            check_box.clicked.connect(lambda state, chck = check_box: self.unselect_allcheckbox(chck))
        self.pushButton.clicked.connect(self.find_match)

    def find_match(self):
        #cur = self.con.cursor()
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




def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
import sqlite3
from collections import Counter

con = sqlite3.connect('oddsportal2.db')
cur = con.cursor()
query = 'SELECT * FROM game'
cur.execute(query)
data = [[el for el in game] for game in cur.fetchall()]
query = 'SELECT url FROM game'
cur.execute(query)
data_url = [game[0] for game in cur.fetchall()]
c = Counter(data_url)
print(c)
counters = []
for key,items in c.items():
    if items > 1:
        counters.append(key)
print(counters)

cur.close()
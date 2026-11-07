"""ホームの「今日は 天一国○年 天暦○月○日」の表を作り、index.html の TENREKI の行を書き換える。

天暦は韓国の陰暦として計算する（真の父母経・実録の 2010〜2013 年の日付で確かめた）。
korean_lunar_calendar が 2050 年までなので、表もそこで終わる。

  pip install korean_lunar_calendar
  python -I -X utf8 _tools/tenreki/build_tenreki.py
"""
import datetime as dt
import os
import re

from korean_lunar_calendar import KoreanLunarCalendar

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, 'index.html')
START = dt.date(2026, 2, 17)  # 天暦 2026年1月1日


def lunar(day):
    c = KoreanLunarCalendar()
    if not c.setSolarDate(day.year, day.month, day.day):
        return None
    return c.lunarYear, c.lunarMonth, c.lunarDay, bool(c.isIntercalation)


# 陽暦を1日ずつ進めて、(年, 月, 閏) ごとの日数を数える
months = []
day = START
while True:
    l = lunar(day)
    if l is None:
        break
    key = (l[0], l[1], l[3])
    if not months or months[-1][0] != key:
        months.append([key, 0])
    months[-1][1] += 1
    day += dt.timedelta(days=1)

# 表の終わりの月は途中で切れているかもしれないので、その年ごと捨てる
last_year = months[-1][0][0]
rows = []
for year in range(START.year, last_year):
    ms = [m for m in months if m[0][0] == year]
    assert all(n in (29, 30) for _, n in ms), year
    leap = next((k[1] for k, _ in ms if k[2]), 0)
    # 閏月は16進の1字（2033年は閏11月なので b）
    rows.append('%x%s' % (leap, ''.join('1' if n == 30 else '0' for _, n in ms)))

line = "var T = '%s'.split(' ');" % ' '.join(rows)
with open(INDEX, encoding='utf-8', newline='') as f:
    html = f.read()
html, n = re.subn(r"var T = '[0-9a-c ]*'\.split\(' '\);", line, html)
assert n == 1, n
with open(INDEX, 'w', encoding='utf-8', newline='') as f:
    f.write(html)
print('%d〜%d年（天暦）、%d字' % (START.year, last_year - 1, len(line)))

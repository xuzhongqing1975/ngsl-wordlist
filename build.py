#!/usr/bin/env python3
"""把 NGSL 词表做成带美式音标、词性、中文释义的清单。

输出三份：
  output/NGSL_前2000词.md    表格，阅读用
  output/NGSL_前2000词.csv   表格，Excel / Anki 用
  output/NGSL点读.html       网页，点一下就念（用系统语音）

首次运行会下载约 70MB 原始数据到 data/，之后复用。
用法：python3 build.py [--limit 2000]
"""

import argparse
import csv
import html
import os
import re
import sys
import urllib.request

from ipa import VOWELS, load_cmu, to_ipa

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'data')
OUT = os.path.join(ROOT, 'output')

SOURCES = {
    'ngsl': ('https://www.newgeneralservicelist.com/s/NGSL_12_stats.csv', 'ngsl12.csv'),
    'ecdict': ('https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv', 'ecdict.csv'),
    'cmudict': ('https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict', 'cmudict.dict'),
}

POS_MAP = {
    'n': 'n.', 'v': 'v.', 'vt': 'vt.', 'vi': 'vi.', 'a': 'adj.', 'adj': 'adj.',
    'ad': 'adv.', 'adv': 'adv.', 'prep': 'prep.', 'pron': 'pron.', 'conj': 'conj.',
    'art': 'art.', 'num': 'num.', 'int': 'int.', 'interj': 'int.', 'aux': 'aux.',
    'abbr': 'abbr.', 'pl': 'pl.',
}
POS_RE = re.compile(r'^(%s)\.\s*(.+)$' % '|'.join(POS_MAP))
SKIP = ('过去式', '过去分词', '复数', '比较级', '最高级')

# NGSL 里几个功能词，词典给的是别的义项，手工订正
OVERRIDE = {
    'a': ('art.', '一个（不定冠词）'),
    'an': ('art.', '一个（不定冠词）'),
    'i': ('pron.', '我'),
    'the': ('art.', '这，那（定冠词）'),
    'online': ('adj./adv.', '在线的，联网的'),
}


def fetch(key):
    url, name = SOURCES[key]
    dest = os.path.join(DATA, name)
    if os.path.exists(dest):
        return dest
    os.makedirs(DATA, exist_ok=True)
    print('下载 %s ...' % name, flush=True)
    urllib.request.urlretrieve(url, dest)
    return dest


def parse_translation(text):
    """从 ECDICT 的 translation 字段里取出「词性 + 中文」，最多两条义项。"""
    text = (text or '').replace('\\r\\n', '\\n')
    senses, plain = [], []
    for line in text.split('\\n'):
        line = line.strip()
        if not line or line[0] in '[(' or any(k in line for k in SKIP):
            continue
        m = POS_RE.match(line)
        if m:
            pos = POS_MAP[m.group(1)]
            mean = m.group(2).strip().strip(';；,，')
            items = [x.strip() for x in re.split(r'[,，;；]', mean) if x.strip()][:3]
            senses.append((pos, '，'.join(items)))
        else:
            plain.append(line)
    if not senses and plain:
        senses = [('', plain[0][:40])]
    seen, keep = set(), []
    for pos, mean in senses:
        if mean and mean not in seen:
            seen.add(mean)
            keep.append((pos, mean))
    return keep[:2]


def ipa_for(word, cmu, ecdict):
    phones = cmu.get(word.lower())
    if phones:
        s = to_ipa(phones)
        if s:
            if sum(1 for p in phones if p.rstrip('012') in VOWELS) == 1:
                s = s.replace('ˈ', '').replace('ˌ', '')
            return s
    alt = (ecdict.get(word.lower()) or {}).get('phonetic', '')
    return '/' + alt.split('.')[0].strip().strip("/'") + '/' if alt else ''


def build_rows(limit):
    ngsl = fetch('ngsl')
    rows = list(csv.DictReader(open(ngsl, encoding='utf-8', newline='')))[:limit]

    print('读取词典 ...', flush=True)
    ecdict = {}
    with open(fetch('ecdict'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            ecdict.setdefault(r['word'].strip().lower(), r)
    cmu = load_cmu(fetch('cmudict'))

    data = []
    for r in rows:
        word = r['Lemma']
        if word.lower() in OVERRIDE:
            senses = [OVERRIDE[word.lower()]]
        else:
            senses = parse_translation((ecdict.get(word.lower()) or {}).get('translation', ''))
        pos, seen = [], set()
        for p, _ in senses:
            if p and p not in seen:
                seen.add(p)
                pos.append(p)
        meaning = '；'.join(m for _, m in senses)
        if len(meaning) > 50:
            meaning = meaning[:48] + '…'
        data.append((r['SFI Rank'], word, ipa_for(word, cmu, ecdict), '/'.join(pos), meaning))
    return data


def write_csv(data, path):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['排序', '单词', '音标', '词性', '中文释义'])
        w.writerows(data)


def write_md(data, path):
    lines = [
        '# NGSL 前 %d 词（音标 + 词性 + 中文）\n' % len(data),
        '词表：NGSL 1.2（newgeneralservicelist.com）；音标：CMU 发音词典转国际音标（美式）；',
        '词性与释义：ECDICT 英汉词典（开源，MIT）。',
        '按使用频次排序，序号越小越常用。ˈ 主重音、ˌ 次重音，ɚ / ɝ 是美音特有的卷舌元音。\n',
        '| # | 单词 | 音标 | 词性 | 中文 |',
        '|---:|---|---|---|---|',
    ]
    for rank, word, ipa, pos, meaning in data:
        lines.append('| %s | %s | %s | %s | %s |' % (rank, word, ipa, pos, meaning))
    open(path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')


def write_html(data, path):
    tpl = open(os.path.join(ROOT, 'template.html'), encoding='utf-8').read()
    body = []
    for rank, word, ipa, pos, meaning in data:
        body.append(
            '<tr><td class="n">%s</td><td class="w">%s</td><td class="i">%s</td>'
            '<td class="p">%s</td><td class="c">%s</td></tr>'
            % tuple(html.escape(x) for x in (rank, word, ipa, pos, meaning)))
    open(path, 'w', encoding='utf-8').write(
        tpl.replace('{{TITLE}}', 'NGSL 前 %d 词 · 点读' % len(data)).replace('<!--ROWS-->', '\n'.join(body)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=2000, help='取前多少个词，默认 2000')
    args = ap.parse_args()

    data = build_rows(args.limit)
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, 'NGSL_前%d词' % len(data))
    write_csv(data, base + '.csv')
    write_md(data, base + '.md')
    write_html(data, os.path.join(OUT, 'NGSL点读.html'))
    write_html(data, os.path.join(ROOT, 'index.html'))   # GitHub Pages 的入口页

    missing = [r[1] for r in data if not r[2]]
    print('完成：%d 词，缺音标 %d 个' % (len(data), len(missing)))
    if missing:
        print('  ' + '、'.join(missing[:10]))


if __name__ == '__main__':
    main()

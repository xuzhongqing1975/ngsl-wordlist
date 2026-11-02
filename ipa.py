#!/usr/bin/env python3
"""ARPAbet（CMU 发音词典记法）转国际音标（美式）。"""

import re

VOWELS = {'AA','AE','AH','AO','AW','AY','EH','ER','EY','IH','IY','OW','OY','UH','UW'}

IPA = {
    'AA':'ɑ','AE':'æ','AH':'ʌ','AO':'ɔ','AW':'aʊ','AY':'aɪ','EH':'ɛ','ER':'ɝ',
    'EY':'eɪ','IH':'ɪ','IY':'iː','OW':'oʊ','OY':'ɔɪ','UH':'ʊ','UW':'uː',
    'B':'b','CH':'tʃ','D':'d','DH':'ð','F':'f','G':'ɡ','HH':'h','JH':'dʒ','K':'k',
    'L':'l','M':'m','N':'n','NG':'ŋ','P':'p','R':'r','S':'s','SH':'ʃ','T':'t',
    'TH':'θ','V':'v','W':'w','Y':'j','Z':'z','ZH':'ʒ',
}

# 出现在词首的三个辅音串，重音符号应放在整个音串之前
ONSETS = {'s p r','s p l','s t r','s t j','s k r','s k w','s k j','s p j'}


def to_ipa(phones):
    parsed = []
    for p in phones:
        m = re.match(r'^([A-Z]+)([012])?$', p)
        if not m:
            return None
        parsed.append((m.group(1), m.group(2) or ''))

    out = []
    for i, (ph, stress) in enumerate(parsed):
        sym = IPA.get(ph)
        if sym is None:
            return None

        if ph in VOWELS:
            if ph == 'ER':
                sym = 'ɚ' if stress == '0' else 'ɝ'
            if ph == 'AH' and stress == '0':
                sym = 'ə'
            if ph == 'IY' and stress == '0':
                sym = 'i'
            if ph == 'UW' and stress == '0':
                sym = 'u'

            mark = 'ˈ' if stress == '1' else 'ˌ' if stress == '2' else ''
            if mark:
                onset = []
                k = i - 1
                while k >= 0 and parsed[k][0] not in VOWELS:
                    onset.insert(0, parsed[k][0])
                    k -= 1
                take = min(len(onset), 2)
                if len(onset) >= 3 and ' '.join(onset[-3:]).lower() in ONSETS:
                    take = 3
                where = len(out) - take if take and len(out) >= take else len(out)
                out.insert(where, mark)

        out.append(sym)

    s = ''.join(out)
    if s.count('ˈ') > 1:                      # 复合词会有两个主重音，保留最后一个
        i = s.rfind('ˈ')
        s = s[:i].replace('ˈ', 'ˌ') + s[i:]
    return '/' + s + '/'


def load_cmu(path):
    """返回 {单词: [音素, ...]}，同一词条取第一套读音。"""
    d = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.split('#')[0].strip()
            if not line:
                continue
            parts = line.split()
            if parts[0].endswith(')'):        # 变体读法 xxx(2)
                continue
            d.setdefault(parts[0].lower(), parts[1:])
    return d

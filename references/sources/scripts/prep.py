# -*- coding: utf-8 -*-
"""样本清洗：PDF/HTML 抽取 -> 可统计纯文本。
原则：只删“可判定的非正文行”（页码、页眉、脚注、英文摘要），不删正文段落。
"""
import re, html

CIRC = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
CJK = r'\u4e00-\u9fa5'

REF_TAIL = re.compile(r'(页。|版。|页$|版$|pp\..*\.)$')
PAGE_NO = re.compile(r'^[·\-\s]*\d{1,3}[·\-\s]*$')
RUNHEAD = re.compile(r'^(中国社会科学|文史哲|思想理论教育导刊|山东大学学报).{0,30}(年第\d+期|20\d\d年第\d+期)$')
HEADING = re.compile(r'^(\d+[．.、]|[一二三四五六七八九十]+、|（[一二三四五六七八九十]+）)')

def fw2hw(s):
    out = []
    for ch in s:
        o = ord(ch)
        if 0xFF10 <= o <= 0xFF19 or 0xFF21 <= o <= 0xFF3A or 0xFF41 <= o <= 0xFF5A:
            out.append(chr(o - 0xFEE0))
        elif ch == '\u3000':
            out.append(' ')
        else:
            out.append(ch)
    return ''.join(out)

def cut_english(t):
    lines = t.split('\n')
    for i, l in enumerate(lines):
        if re.search(r'^(Abstract|Keywords|英文摘要|\[Abstract\])', l.strip()):
            return '\n'.join(lines[:i])
    for i, l in enumerate(lines):
        s = l.strip()
        if len(s) > 40:
            asc = sum(1 for c in s if ord(c) < 128)
            if asc / len(s) > 0.8 and re.search(r'[A-Za-z]{4}', s):
                return '\n'.join(lines[:i])
    return t

def clean_lines(text):
    """返回 (正文行列表, 被删行列表, 标题行列表)"""
    t = cut_english(fw2hw(text))
    kept, dropped, heads = [], [], []
    for raw in t.split('\n'):
        l = raw.strip()
        if not l:
            continue
        if PAGE_NO.match(l) or RUNHEAD.match(l):
            dropped.append(l); continue
        if all(c in CIRC or c.isspace() for c in l):
            dropped.append(l); continue
        if REF_TAIL.search(l) and re.search(r'(第\d+(-\d+)?页|出版社|年第|第\d+期|版。|页。)', l):
            dropped.append(l); continue
        if HEADING.match(l) and len(l) < 45:
            heads.append(l)
        kept.append(l)
    return kept, dropped, heads

def to_text(kept, sep=''):
    return sep.join(kept)

def ocr_clean(text):
    t = fw2hw(text)
    for _ in range(6):
        t = re.sub(r'([%s])\s+([%s])' % (CJK, CJK), r'\1\2', t)
        t = re.sub(r'([%s])\s+([，。、；：？！“”‘’（）《》])' % CJK, r'\1\2', t)
        t = re.sub(r'([，。、；：？！“”‘’（）《》])\s+([%s])' % CJK, r'\1\2', t)
    t = re.sub(r'\n{2,}', '\n', t)
    return t

def html_body(path):
    h = open(path, encoding='utf-8', errors='ignore').read()
    h = re.sub(r'<script.*?</script>', '', h, flags=re.S)
    h = re.sub(r'<style.*?</style>', '', h, flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', '\n', h))
    return '\n'.join(l.strip() for l in t.split('\n') if l.strip())

# -*- coding: utf-8 -*-
"""构建最终样本文件（A-*.txt），并打印清洗诊断。"""
import re, os, html, sys

CIRC = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
CJK = r'\u4e00-\u9fa5'

PAGE_NO = re.compile(r'^[·\-\s]*\d{1,3}[·\-\s]*$')
RUNHEAD = re.compile(r'(年第\s*\d+\s*期|20\d\d\s*年\s*第\s*\d+\s*期)')
CITE_SENT = re.compile(r'(出版社|第\d+(-\d+)?页|pp[．.]|Press|Journal|年第\d+期|第\d+卷|印书馆|\[M\]|\[N\]|\[J\])')

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
    """持续型英文段（>=400 字符两连窗）才截断，避免误伤脚注里的外文条目。"""
    n = len(t)
    def eng(i, w=200):
        s = t[i:i+w]
        if len(s) < w*0.8: return False
        cjk = sum(1 for c in s if '\u4e00' <= c <= '\u9fa5')
        asc = sum(1 for c in s if ord(c) < 128 and c.isalpha())
        return cjk <= 3 and asc >= w*0.35
    i = 1000
    while i < n - 450:
        if eng(i) and eng(i+200):
            return t[:i]
        i += 20
    return t

def line_clean(text, drop_extra=()):
    kept, dropped = [], []
    for raw in text.split('\n'):
        l = raw.strip()
        if not l:
            continue
        if PAGE_NO.match(l) or (RUNHEAD.search(l) and len(l) < 40) or all(c in CIRC or c.isspace() for c in l):
            dropped.append(l); continue
        if any(re.search(p, l) for p in drop_extra):
            dropped.append(l); continue
        if re.search(r'(页。|版。|pp[．.].*[．.])$', l) and CITE_SENT.search(l):
            dropped.append(l); continue
        kept.append(l)
    return kept, dropped

def sent_filter(text):
    parts = re.split(r'(?<=[。！？])', text)
    keep, drop = [], []
    for p in parts:
        if CITE_SENT.search(p) and len(p) < 110 and ('《' in p or '，' in p):
            drop.append(p)
        else:
            keep.append(p)
    return ''.join(keep), drop

def build(raw_path, drop_extra=(), ocr=False, html_mode=False, start=None, end=None):
    raw = open(raw_path, encoding='utf-8', errors='ignore').read()
    if html_mode:
        h = re.sub(r'<script.*?</script>', '', raw, flags=re.S)
        h = re.sub(r'<style.*?</style>', '', h, flags=re.S)
        raw = html.unescape(re.sub(r'<[^>]+>', '\n', h))
    raw = fw2hw(raw)
    if ocr:
        for _ in range(6):
            raw = re.sub(r'([%s])\s+([%s])' % (CJK, CJK), r'\1\2', raw)
            raw = re.sub(r'([%s])\s+([，。、；：？！“”‘’（）《》])' % CJK, r'\1\2', raw)
            raw = re.sub(r'([，。、；：？！“”‘’（）《》])\s+([%s])' % CJK, r'\1\2', raw)
        raw = re.sub(r'(?<=\d)\s+(?=\d)', '', raw)
    kept, dropped = line_clean(raw, drop_extra)
    text = ''.join(kept)
    if start:
        i = text.find(start)
        if i > 0:
            text = text[i:]
    if end:
        j = text.find(end)
        if j > 0:
            text = text[:j]
    text = cut_english(text)
    text, cdrop = sent_filter(text)
    return text, dropped, cdrop

JOBS = {
 'A-xiandaihua-2019': dict(path='a1.txt'),
 'A-jianshe-pipan-2019': dict(path='a2.txt', end='参考文献'),
 'A-dangjian-buju-2018': dict(path='a3.txt', start='党的十九大报告对新时代党的建设新的伟大工程', end='来源：《人民日报》'),
 'A-diyiguoji-2015': dict(path='a4.txt', ocr=True),
 'A-zishen-xiandaihua-2025': dict(path='b1.html', html_mode=True, start='党在领导现代化进程中推进自身现代化本文刊发于', end='版权所有'),
 'A-zhengdangfazhi-2005': dict(path='a6.txt', start='一种新型的政党文明形态王韶兴'),
}

if __name__ == '__main__':
    only = sys.argv[1:] or list(JOBS)
    for name in only:
        kw = dict(JOBS[name]); path = kw.pop('path')
        text, dropped, cdrop = build(path, **kw)
        print('%-28s chars=%6d lines_dropped=%3d sent_dropped=%2d' % (name, len(text), len(dropped), len(cdrop)))
        print('   HEAD:', text[:70])
        print('   TAIL:', text[-70:])

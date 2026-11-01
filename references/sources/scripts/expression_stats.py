# -*- coding: utf-8 -*-
"""王韶兴表达风格：统计脚本（可复跑）
用法：python analyze.py <样本目录>
输出：stdout 的 markdown 表 + hits/*.txt 供人工抽检
"""
import re, os, json, statistics, glob, sys

CJK = r'\u4e00-\u9fa5'
ART = sys.argv[1] if len(sys.argv) > 1 else r'C:/Users/yingqc/.workbuddy-ai/skills/wang-shaoxing-perspective/references/sources/articles'
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hits')

def load(p):
    s = open(p, encoding='utf-8').read()
    lines = [l for l in s.split('\n') if not l.startswith('#')]
    return ''.join(lines)

def sents(t):
    parts = re.split(r'(?<=[。！？])', t)
    return [p.strip() for p in parts if p.strip()]

def stats(t):
    d = {}
    d['chars'] = len(re.sub(r'\s', '', t))
    S = sents(t)
    L = [len(s) for s in S]
    d['sent_n'] = len(S)
    d['mean'] = round(statistics.mean(L), 1)
    d['median'] = statistics.median(L)
    d['max'] = max(L); d['min'] = min(L)
    d['gt100'] = round(sum(1 for x in L if x > 100) * 100 / len(L), 1)
    d['gt150'] = round(sum(1 for x in L if x > 150) * 100 / len(L), 1)
    d['lt30'] = round(sum(1 for x in L if x < 30) * 100 / len(L), 1)
    d['gt80'] = round(sum(1 for x in L if x > 80) * 100 / len(L), 1)
    return d, S

PUN = [('逗号', '，'), ('分号', '；'), ('顿号', '、'), ('冒号', '：'), ('引号对', '“'), ('括号', '（'), ('破折号', '—{1,2}'), ('问号', '？'), ('感叹号', '！')]

def punct(t):
    n = len(re.sub(r'\s', '', t))
    return {k: round(len(re.findall(v, t)) * 1000.0 / n, 2) for k, v in PUN}

STRUCT = ['首先', '其次', '再次', '最后', '第一', '第二', '第三', '总之', '因此', '但是', '然而',
          '不过', '同时', '另一方面', '也就是说', '换言之', '事实上', '当然', '只有', '才能',
          '必须', '应当', '需要', '关键在于', '本质上', '根本', '归根到底']

VERBS = ['建构', '构建', '塑造', '生成', '揭示', '阐明', '论证', '分析', '考察', '梳理', '厘清',
         '界定', '提出', '认为', '强调', '指出', '表明', '意味着', '蕴含', '彰显', '体现']

def freq(t, words):
    n = len(re.sub(r'\s', '', t))
    return {w: (len(re.findall(w, t)), round(len(re.findall(w, t)) * 10000.0 / n, 1)) for w in words}

DUIJIAO = {
    '不仅…而且': r'不仅[^。；]{0,40}?而且',
    '既…又': r'既[^。；]{0,25}?又',
    '不是…而是': r'不是[^。；]{0,40}?而是',
    '所谓': r'所谓',
    '既…也': r'既[^。；]{0,30}?也',
    '越…越': r'越[^。；]{0,15}?越',
    '只有…才': r'只有[^。；]{0,40}?才',
    '从…到': r'从[^。；]{2,30}?到[^。；]{2,30}?[，。；]',
    '一方面…另一方面': r'一方面[^。]{0,60}?另一方面',
    '既是…也是': r'既是[^。；]{0,40}?也是',
    '不在于…而在于': r'不在于[^。；]{0,40}?而在于',
}

CITE = {
    '马克思': '马克思', '恩格斯': '恩格斯', '列宁': '列宁', '斯大林': '斯大林',
    '毛泽东': '毛泽东', '邓小平': '邓小平', '江泽民': '江泽民', '习近平': '习近平',
    '韦伯': '韦伯', '熊彼特': '熊彼特', '萨托利': '萨托利', '达尔': '达尔',
    '亨廷顿': '亨廷顿', '奥斯特罗果尔斯基': '奥斯特罗果尔斯基|Ostrogorski', '米歇尔斯': '米歇尔斯|Michels',
    '谢茨施耐德': '谢茨施耐德', '林尚立': '林尚立', '王绍光': '王绍光',
}

def main():
    files = sorted(glob.glob(os.path.join(ART, 'A-*.txt')))
    os.makedirs(OUTDIR, exist_ok=True)
    rows = {}
    allq = []
    for f in files:
        name = os.path.basename(f)[:-4]
        t = load(f)
        d, S = stats(t)
        d['punct'] = punct(t)
        d['struct'] = freq(t, STRUCT)
        d['verbs'] = freq(t, VERBS)
        d['duijiao'] = {k: len(re.findall(v, t)) for k, v in DUIJIAO.items()}
        d['cite'] = {k: len(re.findall(v, t)) for k, v in CITE.items()}
        d['num'] = round(len(re.findall(r'\d+(?:\.\d+)?', t)) * 1000.0 / d['chars'], 2)
        d['pct_num'] = round(len(re.findall(r'\d+(?:\.\d+)?%', t)) * 1000.0 / d['chars'], 2)
        d['q'] = t.count('？')
        # 引号内容
        qs = re.findall(r'“([^”]{1,80})”', t)
        d['quote_n'] = len(qs)
        d['quote_len_mean'] = round(sum(len(x) for x in qs) / len(qs), 1) if qs else 0
        d['quote_1to4'] = sum(1 for x in qs if len(x) <= 4)
        d['quote_5to12'] = sum(1 for x in qs if 5 <= len(x) <= 12)
        d['quote_13plus'] = sum(1 for x in qs if len(x) >= 13)
        rows[name] = d
        allq.append((name, qs, S, t))
    json.dump(rows, open('stats.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
    names = list(rows)
    def line(label, getter):
        vals = [getter(rows[n]) for n in names]
        print('| %s | %s |' % (label, ' | '.join(str(v) for v in vals)))
    print('| 指标 | ' + ' | '.join(n.replace('A-','') for n in names) + ' |')
    for k in ['chars','sent_n','mean','median','max','min','gt80','gt100','gt150','lt30']:
        line(k, lambda d,k=k: d[k])
    for k in ['逗号','分号','顿号','冒号','引号对','括号','破折号','问号','感叹号']:
        line('‰'+k, lambda d,k=k: d['punct'][k])
    for w in STRUCT:
        line('S:'+w, lambda d,w=w: d['struct'][w][0])
    for w in VERBS:
        line('V:'+w, lambda d,w=w: d['verbs'][w][0])
    for k in DUIJIAO:
        line('D:'+k, lambda d,k=k: d['duijiao'][k])
    for k in CITE:
        line('C:'+k, lambda d,k=k: d['cite'][k])
    for k in ['num','pct_num','q','quote_n','quote_len_mean','quote_1to4','quote_5to12','quote_13plus']:
        line(k, lambda d,k=k: d[k])
    # 抽检文件
    for name, qs, S, t in allq:
        with open(os.path.join(OUTDIR, name + '-quotes.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join('「%s」' % q for q in qs))
        with open(os.path.join(OUTDIR, name + '-sent.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join('%3d| %s' % (len(s), s) for s in S))

if __name__ == '__main__':
    main()

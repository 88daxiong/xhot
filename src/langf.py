"""语言过滤：主要保留中文/英文。"""
import re
OTHER=re.compile(r'[\u3040-\u30ff\u31f0-\u31ff\uac00-\ud7af\u1100-\u11ff\u0400-\u04ff\u0600-\u06ff\u0590-\u05ff\u0e00-\u0e7f\u0900-\u097f\u0980-\u0dff]')
CJK=re.compile(r'[\u4e00-\u9fff]');LAT=re.compile(r'[A-Za-z]')
NEUTRAL={'','zxx','art','und','qme','qam','qht','qct','qst'}
def strip(t): return re.sub(r'https?://\S+|@\w+|#\w+','',t or '')
def script_ok(t):
    t=strip(t); o=len(OTHER.findall(t)); c=len(CJK.findall(t)); l=len(LAT.findall(t))
    if o==0: return True
    if re.search(r'[\u3040-\u30ff]',t) and o>=3: return False  # 含假名 → 日文
    return o/(o+c+l) < 0.3
def ok(text,lang=''):
    lang=(lang or '').lower()
    if lang in ('zh','en'): return script_ok(text)
    if lang in NEUTRAL: return script_ok(text)
    letters=len(LAT.findall(strip(text)))+len(CJK.findall(strip(text)))
    return letters<25 and script_ok(text)  # 很短的文本 X 常误判语言

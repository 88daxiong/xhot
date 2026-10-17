"""v15.6 公开页隐私处理：①脱敏邮箱 / 手机号 / 微信号；②内网与裸 IP 链接不渲染成链接。
redact(text)：返回脱敏后的纯文本（先脱敏、再转义）。private_url(u)：True 表示不应作为链接输出。"""
import re,ipaddress
from urllib.parse import urlsplit
EMAIL=re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}')
PHONE=re.compile(r'(?<![\dA-Za-z])(?:\+?86[ \-]?)?1[3-9]\d[ \-]?\d{4}[ \-]?\d{4}(?![\dA-Za-z])')
# 微信：标签（VX / V信 / WX / WeChat / 微信 / 微信号 / 薇信 / 威信）+ 冒号 + 账号；或「加微信 xxx」
WX1=re.compile(r'(?i)((?:vx|v信|wx|we ?chat|微信号?|薇信|威信|vx号|wx号)\s*[:：=]\s*)@?[A-Za-z][-_A-Za-z0-9]{4,24}')
WX2=re.compile(r'(?i)((?:加|add|联系)\s*(?:我的?)?\s*(?:vx|v信|wx|wechat|微信|薇信)\s*[:：]?\s*)[A-Za-z][-_A-Za-z0-9]{4,24}')
def redact(t):
    if not t: return t
    t=str(t)
    if '@' in t: t=EMAIL.sub('[邮箱已隐藏]',t)
    t=PHONE.sub('[手机号已隐藏]',t)
    if re.search(r'(?i)vx|v信|wx|chat|微信|薇信|威信',t):
        t=WX1.sub(lambda m:m.group(1)+'[微信号已隐藏]',t); t=WX2.sub(lambda m:m.group(1)+'[微信号已隐藏]',t)
    return t
def private_url(u):
    """内网 / 回环 / 链路本地 / 裸 IP（含十进制、十六进制写法）/ localhost / .local / .internal"""
    try: p=urlsplit(str(u).strip()); h=(p.hostname or '').lower().rstrip('.')
    except ValueError: return True
    if not h: return True
    if h in('localhost','ip6-localhost') or h.endswith(('.local','.localhost','.internal','.lan','.home','.corp','.intranet')): return True
    if re.fullmatch(r'(?:0x[0-9a-f]+|\d+)(?:\.(?:0x[0-9a-f]+|\d+)){0,3}',h): return True   # 任何数字形式的裸 IPv4（含 2130706433 / 0x7f.1）
    try: ipaddress.ip_address(h); return True                                              # IPv6 字面量
    except ValueError: return False

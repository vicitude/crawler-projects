"""
Cookie 处理工具。
把浏览器复制的 cookie 字符串直接转成字典，方便 Scrapy 用。
"""


def parse_cookie_string(cookie_str: str) -> dict:
    """
    把浏览器 DevTools 复制的 cookie 字符串转成 dict。

    支持的输入形式（豆瓣实际复制过来长这样）：
        'll=<ll>; bid=<bid>; viewed="<viewed_items>"; __utmz=...|utmccn=...'

    关键点：
        - 用 ';' 切
        - 用 '=' 切（只切一次，因为 value 里可能有 '='）
        - value 两边有引号要去掉
        - 空段跳过
    """
    cookies = {}
    if not cookie_str:
        return cookies

    for pair in cookie_str.split(";"):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        key, _, value = pair.partition("=")  # partition 只切第一个 '='
        key = key.strip()
        value = value.strip().strip('"')    # 去掉首尾的引号
        if key:
            cookies[key] = value
    return cookies


if __name__ == "__main__":
    raw = (
        'll=<ll>; bid=<bid>; _vwo_uuid_v2=<uuid>; '
        'viewed="<viewed_items>"; '
        '__utmz=<utmz_value>|utmcmd=<source>|utmcct=/'
    )
    print(parse_cookie_string(raw))
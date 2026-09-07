import re
from pathlib import Path

BOT_NAME = "lianjia_project"

# 将 Scrapy 运行日志保存到项目根目录，便于后续查看和排查验证码跳转。
LOG_ENABLED = True
LOG_LEVEL = "INFO"
LOG_FILE = str(Path(__file__).resolve().parent.parent / "lianjia_crawl.log")
LOG_ENCODING = "utf-8-sig"

SPIDER_MODULES = ["lianjia_project.spiders"]
NEWSPIDER_MODULE = "lianjia_project.spiders"

ADDONS = {}


def read_request_value(name):
    """从项目根目录的“爬虫数据项.txt”读取请求头，避免重复保存 Cookie。"""
    data_file = Path(__file__).resolve().parent.parent / "爬虫数据项.txt"
    text = data_file.read_text(encoding="utf-8-sig")
    match = re.search(rf"(?im)^\s*{re.escape(name)}\s*[：:]\s*(.+?)\s*$", text)
    if not match:
        raise RuntimeError(f"未在 {data_file} 中找到 {name}")
    return match.group(1).strip()


ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 0.5

# 翻页测试最多抓取 5 个列表页。
FOLLOW_PAGINATION = True
MAX_PAGES = 5

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "User-Agent": read_request_value("user-agent"),
    "Cookie": read_request_value("cookie"),
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "lianjia_project.middlewares.LianjiaProjectSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.cookies.CookiesMiddleware": None,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "lianjia_project.pipelines.LianjiaProjectPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORTERS = {
    "lianjia_csv": "lianjia_project.exporters.Utf8SigCsvItemExporter",
}

# 本轮测试关闭 CSV 文件输出，仅在终端查看日志。
FEEDS = {}

FEED_EXPORT_ENCODING = "utf-8-sig"

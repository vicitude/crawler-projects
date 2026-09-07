# Scrapy settings for iresearch project

import os

BOT_NAME = "iresearch"

SPIDER_MODULES = ["iresearch.spiders"]
NEWSPIDER_MODULE = "iresearch.spiders"

ADDONS = {}

# 不遵循 robots.txt（接口型站点）
ROBOTSTXT_OBEY = False

# 并发与限速：接口爬取，串行即可
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# 默认请求头
DEFAULT_REQUEST_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Referer": "https://www.iresearch.com.cn/report.shtml?type=4",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Cookie：示例中给出的值，可按需更新
DEFAULT_REQUEST_COOKIES = {
    "refCookie": "www.iresearch.com.cn",
}

# 启用随机 UA 中间件
DOWNLOADER_MIDDLEWARES = {
    "iresearch.middlewares.RandomUserAgentMiddleware": 400,
}

# Pipeline
ITEM_PIPELINES = {
    "iresearch.pipelines.IresearchDeduplicatePipeline": 100,
    "iresearch.pipelines.IresearchJsonLinesPipeline": 300,
    "iresearch.pipelines.IresearchImagesPipeline": 400,
}

# 数据保存路径（绝对路径，避免 cwd 不一致）
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
IMAGES_STORE = os.path.join(DATA_DIR, "images")
IMAGES_EXPIRES = 90  # 防止 304
IMAGES_THUMBS = {}

# Jsonl 输出文件（绝对路径）
JSONL_OUTPUT = os.path.join(DATA_DIR, "iresearch_charts.jsonl")

# 爬虫参数（Spider 默认值，可通过命令行 -a 覆盖）
TARGET_COUNT = 8500
PAGE_SIZE = 10
START_LAST_ID = 45893

# 日志
LOG_LEVEL = "INFO"

FEED_EXPORT_ENCODING = "utf-8"

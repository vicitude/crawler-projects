# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapySinaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class SinaNewsItem(scrapy.Item):
    """详情页最终入库的 Item"""
    title = scrapy.Field()           # 新闻标题
    publish_time = scrapy.Field()    # 发布时间（datetime 对象）
    content = scrapy.Field()         # 正文+图片（HTML 拼接）
    spider_time = scrapy.Field()     # 爬虫抓取时间（数据库自动填/或代码填）
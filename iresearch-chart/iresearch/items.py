# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class IresearchItem(scrapy.Item):
    """艾瑞咨询图表条目"""
    chart_id = scrapy.Field()      # 唯一标识，例如 chart.45882
    title = scrapy.Field()         # 标题
    industry = scrapy.Field()      # 行业分类
    uptime = scrapy.Field()        # 发布时间
    small_img = scrapy.Field()     # 缩略图 URL
    image_paths = scrapy.Field()   # ImagesPipeline 下载后的本地路径列表

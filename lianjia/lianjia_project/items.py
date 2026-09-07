# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class LianjiaProjectItem(scrapy.Item):
    title = scrapy.Field()
    house_tag = scrapy.Field()
    total_price = scrapy.Field()
    unit_price = scrapy.Field()
    community_name = scrapy.Field()
    region_name = scrapy.Field()
    layout = scrapy.Field()
    area = scrapy.Field()
    orientation = scrapy.Field()
    decorate_status = scrapy.Field()
    floor = scrapy.Field()
    building_type = scrapy.Field()
    is_near_subway = scrapy.Field()
    tax_free_type = scrapy.Field()
    is_has_key = scrapy.Field()

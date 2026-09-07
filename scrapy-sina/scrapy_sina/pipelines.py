# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from datetime import datetime

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from scrapy_sina.items import SinaNewsItem
from scrapy_sina.models import SinaNews


class ScrapySinaPipeline:
    def process_item(self, item, spider):
        return item


class MysqlSinaNewsPipeline:
    """用 peewee ORM 把 SinaNewsItem 写入 ai_news 表"""

    def open_spider(self, spider):
        # 爬虫启动时连接数据库
        if SinaNews._meta.database.is_closed():
            SinaNews._meta.database.connect()
            spider.logger.info("MySQL 连接已打开")

    def close_spider(self, spider):
        # 爬虫关闭时断开数据库连接
        if not SinaNews._meta.database.is_closed():
            SinaNews._meta.database.close()
            spider.logger.info("MySQL 连接已关闭")

    def process_item(self, item, spider):
        # 只处理 SinaNewsItem，其他类型跳过
        if not isinstance(item, SinaNewsItem):
            return item

        adapter = ItemAdapter(item)

        try:
            # 按 title 查重（模型里 title 是 unique 字段）
            # 只 SELECT id 列，避免 SELECT 所有列导致的 Unknown column 问题
            exists_record = SinaNews.select(SinaNews.id).where(
                SinaNews.title == adapter["title"]
            ).get_or_none()
            if exists_record is not None:
                spider.logger.info(
                    f"已存在，跳过：{adapter['title']}"
                )
                raise DropItem(f"Duplicate item found: {adapter['title']}")

            # 插入新记录，spider_time 手动填当前时间
            SinaNews.create(
                title=adapter["title"],
                publish_time=adapter["publish_time"],
                content=adapter["content"],
                spider_time=datetime.now(),
            )
            spider.logger.info(
                f"入库成功：{adapter['title']} ({adapter['publish_time']})"
            )
        except DropItem:
            raise  # DropItem 必须 raise
        except Exception as e:
            spider.logger.error(f"入库失败：{adapter['title']}，错误：{e}")
            raise

        return item
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
import os

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request


class IresearchDeduplicatePipeline:
    """基于 chart_id 的去重

    进程内通过内存集合去重；
    跨进程通过启动时读取 JSONL 历史记录恢复 seen 集合，
    避免重复写入 jsonl 与重复下载图片。
    """

    def __init__(self):
        self.seen = set()
        self._loaded_count = 0

    @classmethod
    def from_crawler(cls, crawler):
        instance = cls()
        jsonl_path = crawler.settings.get("JSONL_OUTPUT", "iresearch_charts.jsonl")
        if jsonl_path and os.path.exists(jsonl_path):
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    chart_id = row.get("chart_id")
                    if chart_id:
                        instance.seen.add(chart_id)
                        instance._loaded_count += 1
        return instance

    def open_spider(self, spider):
        spider.logger.info(
            "IresearchDeduplicatePipeline 已加载 %s 条历史 chart_id",
            self._loaded_count,
        )

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        chart_id = adapter.get("chart_id")
        if not chart_id:
            raise DropItem("缺少 chart_id，已丢弃")
        if chart_id in self.seen:
            raise DropItem(f"重复条目 {chart_id}，已丢弃")
        self.seen.add(chart_id)
        return item


class IresearchJsonLinesPipeline:
    """把 item 追加写入 jsonl 文件"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.fp = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            file_path=crawler.settings.get("JSONL_OUTPUT", "iresearch_charts.jsonl")
        )

    def open_spider(self, spider):
        os.makedirs(os.path.dirname(self.file_path) or ".", exist_ok=True)
        self.fp = open(self.file_path, "a", encoding="utf-8")

    def close_spider(self, spider):
        if self.fp:
            self.fp.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        line = json.dumps(dict(adapter), ensure_ascii=False)
        self.fp.write(line + "\n")
        return item


class IresearchImagesPipeline(ImagesPipeline):
    """下载 small_img 到 images/full/，文件名使用 chart_id"""

    def get_media_requests(self, item, info):
        url = item.get("small_img")
        if not url:
            return
        yield Request(
            url=url,
            meta={"chart_id": item.get("chart_id")},
            headers={"Referer": "https://www.iresearch.com.cn/"},
        )

    def file_path(self, request, response=None, info=None, *, item=None):
        chart_id = request.meta.get("chart_id") or "unknown"
        # 保留扩展名
        ext = os.path.splitext(request.url)[1].split("?")[0] or ".png"
        return f"full/{chart_id}{ext}"

    def item_completed(self, results, item, info):
        paths = []
        for ok, info_dict in results:
            if ok and isinstance(info_dict, dict):
                paths.append(info_dict.get("path"))
        if not paths:
            spider = info.spider
            spider.logger.warning("图片下载失败: %s", item.get("chart_id"))
        item["image_paths"] = paths
        return item

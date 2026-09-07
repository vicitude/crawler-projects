# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import re
from decimal import Decimal, InvalidOperation

from itemadapter import ItemAdapter


class LianjiaProjectPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for field_name in adapter.field_names():
            value = adapter.get(field_name)
            if isinstance(value, str):
                adapter[field_name] = self.clean_text(value)

        adapter["total_price"] = self.total_price_to_yuan(
            adapter.get("total_price")
        )
        adapter["unit_price"] = self.to_integer(adapter.get("unit_price"))
        adapter["area"] = self.clean_area(adapter.get("area"))
        adapter["tax_free_type"] = self.clean_tax_type(
            adapter.get("tax_free_type")
        )
        adapter["is_near_subway"] = bool(adapter.get("is_near_subway"))
        adapter["is_has_key"] = bool(adapter.get("is_has_key"))

        return item

    @staticmethod
    def clean_text(value):
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def total_price_to_yuan(value):
        """详情页总价单位是万元，输出时转换为元。"""
        if value in (None, ""):
            return None
        number = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
        if not number:
            return None
        try:
            return int(Decimal(number.group()) * 10000)
        except InvalidOperation:
            return None

    @staticmethod
    def to_integer(value):
        if value in (None, ""):
            return None
        number = re.search(r"\d+", str(value).replace(",", ""))
        return int(number.group()) if number else None

    @staticmethod
    def clean_area(value):
        if not value:
            return ""
        value = str(value).replace("㎡", "平米").replace("m²", "平米")
        number = re.search(r"\d+(?:\.\d+)?", value)
        return f"{number.group()}平米" if number else value

    @staticmethod
    def clean_tax_type(value):
        value = value or ""
        if "满五" in value:
            return "房本满五年"
        if "满二" in value or "满两" in value:
            return "房本满两年"
        return value

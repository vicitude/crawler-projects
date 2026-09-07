import json
import re

import scrapy

from lianjia_project.items import LianjiaProjectItem


class LianjiaSpider(scrapy.Spider):
    name = "lianjia"
    allowed_domains = ["bj.lianjia.com"]
    start_urls = [
        "https://bj.lianjia.com/ershoufang/rs%E5%A4%A9%E9%80%9A%E8%8B%91/"
    ]

    def parse(self, response):
        """解析列表页，并进入每套房源的详情页。"""
        page_num = response.meta.get("page_num", 1)
        houses = response.css("ul.sellListContent > li.clear")
        self.logger.info(
            "第 %s 页：%s；找到 %s 套房源", page_num, response.url, len(houses)
        )

        for house in houses:
            detail_url = house.css("div.title > a::attr(href)").get()
            if not detail_url:
                continue

            tag_texts = self.clean_text_list(house.css("div.tag span::text").getall())
            house_tags = [
                text
                for text in tag_texts
                if not any(
                    keyword in text
                    for keyword in ("地铁", "房本", "满五", "满二", "VR", "随时看房")
                )
            ]

            yield response.follow(
                detail_url,
                callback=self.parse_detail,
                cb_kwargs={"list_tags": house_tags},
            )

        # 分页逻辑：从 comp-module="page" 的 div 读 page-data 与 page-url，

        if not self.settings.getbool("FOLLOW_PAGINATION", False):
            return

        max_pages = self.settings.getint("MAX_PAGES", 5)
        if page_num >= max_pages:
            self.logger.info(
                "第 %s 页达到 MAX_PAGES=%s，停止翻页", page_num, max_pages
            )
            return

        page_box = response.xpath(
            '//div[contains(@class, "house-lst-page-box")]'
        )
        if not page_box:
            self.logger.info(
                "第 %s 页未找到分页节点，停止翻页 url=%s", page_num, response.url
            )
            return

        page_box = page_box[0]
        page_url_tpl = page_box.attrib.get("page-url") or ""
        page_data_raw = (page_box.attrib.get("page-data") or "").replace(
            "&quot;", '"'
        )
        try:
            page_data = json.loads(page_data_raw) if page_data_raw else {}
        except json.JSONDecodeError:
            page_data = {}

        try:
            total_page = int(page_data.get("totalPage") or 0)
            cur_page = int(page_data.get("curPage") or page_num)
        except (TypeError, ValueError):
            total_page, cur_page = 0, page_num

        self.logger.info(
            "PAGE_STATUS page=%s curPage=%s totalPage=%s houses=%s",
            page_num,
            cur_page,
            total_page,
            len(houses),
        )

        if cur_page >= total_page:
            self.logger.info(
                "第 %s 页已是最后一页（totalPage=%s），停止翻页",
                cur_page,
                total_page,
            )
            return

        if not page_url_tpl:
            self.logger.warning("page-url 为空，无法翻页")
            return

        next_url = "https://bj.lianjia.com" + page_url_tpl.format(page=cur_page + 1)
        self.logger.info(
            "第 %s 页下一页 URL：%s", page_num, next_url
        )

        if next_url == response.url:
            self.logger.info("下一页 URL 与当前页相同，停止翻页")
            return

        yield response.follow(
            next_url,
            callback=self.parse,
            meta={"page_num": page_num + 1},
        )

    def parse_detail(self, response, list_tags):
        base_info = self.label_value_map(
            response.css("#introduction div.base div.content li")
        )
        transaction_info = self.label_value_map(
            response.css("#introduction div.transaction div.content li")
        )

        region_links = self.clean_text_list(
            response.css("div.areaName span.info a::text").getall()
        )
        region_name = ""
        if len(region_links) >= 2:
            region_name = region_links[1]
        elif region_links:
            region_name = region_links[0]

        subway_text = self.clean_text(
            response.css("a.supplement[title*='地铁']::attr(title)").get()
            or response.css("a.supplement[title*='地铁']::text").get()
            or ""
        )
        visit_text = self.clean_text(
            " ".join(response.css("div.visitTime span.info::text").getall())
        )

        item = LianjiaProjectItem()
        item["title"] = response.css("h1.main::attr(title)").get() or response.css(
            "h1.main::text"
        ).get()
        item["house_tag"] = "|".join(list_tags)
        item["total_price"] = response.css("span.total::text").get()
        item["unit_price"] = response.css("span.unitPriceValue::text").get()
        item["community_name"] = response.css(
            "div.communityName a.info::text"
        ).get()
        item["region_name"] = region_name
        item["layout"] = base_info.get("房屋户型", "")
        item["area"] = base_info.get("建筑面积", "")
        item["orientation"] = base_info.get("房屋朝向", "")
        item["decorate_status"] = base_info.get("装修情况", "")
        item["floor"] = base_info.get("所在楼层", "")
        item["building_type"] = base_info.get("建筑类型", "")
        item["is_near_subway"] = bool(subway_text)
        item["tax_free_type"] = transaction_info.get("房屋年限", "")
        item["is_has_key"] = "随时" in visit_text
        self.logger.info("房源数据：%s", dict(item))
        yield item

    def label_value_map(self, selectors):
        result = {}
        for selector in selectors:
            label = self.clean_text(" ".join(selector.css("span.label::text").getall()))
            all_text = self.clean_text(" ".join(selector.xpath(".//text()").getall()))
            if not label:
                continue
            value = re.sub(rf"^{re.escape(label)}\s*", "", all_text, count=1)
            result[label] = value
        return result

    @staticmethod
    def clean_text(value):
        return re.sub(r"\s+", " ", value or "").strip()

    def clean_text_list(self, values):
        return [text for text in (self.clean_text(value) for value in values) if text]

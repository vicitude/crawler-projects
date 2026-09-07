import json
from urllib.parse import urlencode

import scrapy

from iresearch.items import IresearchItem


class IresearchChartSpider(scrapy.Spider):
    """艾瑞咨询图表爬虫

    起始入参 lastId=chart.45893，pageSize=10，
    每次请求结束后将 lastId 整数部分 -10，直到累计抓取条数 >= TARGET_COUNT。
    """

    name = "iresearch_chart"
    allowed_domains = ["iresearch.com.cn", "pic.iresearch.cn"]

    # 默认参数，可在 settings 中覆盖
    TARGET_COUNT = 8500
    PAGE_SIZE = 10
    START_LAST_ID = 45893
    ROOT_ID = "14"
    # 遇到空数据时向前回退探测的步长
    PROBE_BACK_STEP = 100

    API_URL = "https://www.iresearch.com.cn/api/products/getdatasapi"

    def __init__(self, target_count=None, page_size=None, start_last_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if target_count is not None:
            self.TARGET_COUNT = int(target_count)
        if page_size is not None:
            self.PAGE_SIZE = int(page_size)
        if start_last_id is not None:
            self.START_LAST_ID = int(start_last_id)
        self.fetched = 0  # 已抓取条数

    def _build_url(self, last_id: int) -> str:
        params = {
            "rootId": self.ROOT_ID,
            "channelId": "",
            "userId": "",
            "lastId": f"chart.{last_id}",
            "pageSize": str(self.PAGE_SIZE),
        }
        return f"{self.API_URL}?{urlencode(params)}"

    async def start(self):
        yield scrapy.Request(
            url=self._build_url(self.START_LAST_ID),
            method="GET",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.iresearch.com.cn/report.shtml?type=4",
            },
            meta={"last_id": self.START_LAST_ID},
            dont_filter=True,
            callback=self.parse,
        )

    def start_requests(self):
        # 兼容旧版本 Scrapy；Scrapy 2.13+ 优先调用 start()
        yield scrapy.Request(
            url=self._build_url(self.START_LAST_ID),
            method="GET",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.iresearch.com.cn/report.shtml?type=4",
            },
            meta={"last_id": self.START_LAST_ID},
            dont_filter=True,
            callback=self.parse,
        )

    def parse(self, response):
        last_id = response.meta["last_id"]

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("无法解析 JSON 响应: %s", response.text[:200])
            return

        # 接口返回结构可能为列表，也可能包裹在 data/list 字段，先尝试多种取值方式
        items = self._extract_items(data)

        # 当 Status=fail 时（如 lastId 越界），区分提示但不改变探测逻辑
        if isinstance(data, dict) and data.get("Status") == "fail":
            self.logger.warning(
                "第 %s 页 API 报错: %s",
                last_id,
                data.get("Msg") or data.get("List", {}).get("erroMsg"),
            )

        if not items:
            self.logger.warning(
                "第 %s 页数据为空，向前回退 %s 个探测",
                last_id, self.PROBE_BACK_STEP,
            )
            probe_last_id = last_id - self.PROBE_BACK_STEP
            if probe_last_id <= 0:
                self.logger.info("探测点已 <=0，停止爬取")
                return
            yield scrapy.Request(
                url=self._build_url(probe_last_id),
                method="GET",
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://www.iresearch.com.cn/report.shtml?type=4",
                },
                meta={
                    "last_id": probe_last_id,
                    "empty_at": last_id,  # 记住引发探测的"空位置"
                    "probe": True,
                },
                dont_filter=True,
                callback=self.parse_probe,
            )
            return

        for row in items:
            if self.fetched >= self.TARGET_COUNT:
                self.logger.info("已达目标条数 %s，停止爬取", self.TARGET_COUNT)
                return

            chart_id = row.get("Id") or ""
            item = IresearchItem(
                chart_id=chart_id,
                title=row.get("Title") or "",
                industry=row.get("industry") or "",
                uptime=row.get("Uptime") or "",
                small_img=row.get("SmallImg") or "",
            )
            self.fetched += 1
            yield item

        # 翻页：lastId 整数部分 -10
        next_last_id = last_id - self.PAGE_SIZE
        if next_last_id <= 0:
            self.logger.info("lastId 已小于等于 0，停止爬取")
            return
        if self.fetched >= self.TARGET_COUNT:
            return

        next_url = self._build_url(next_last_id)
        yield scrapy.Request(
            url=next_url,
            method="GET",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.iresearch.com.cn/report.shtml?type=4",
            },
            meta={"last_id": next_last_id},
            dont_filter=True,
            callback=self.parse,
        )

    def parse_probe(self, response):
        """探测回调：判断空数据位置之前是否还有数据"""
        last_id = response.meta["last_id"]
        empty_at = response.meta["empty_at"]

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("探测响应 JSON 解析失败: %s", response.text[:200])
            return

        items = self._extract_items(data)
        if isinstance(data, dict) and data.get("Status") == "fail":
            self.logger.warning(
                "探测点 %s API 报错: %s",
                last_id,
                data.get("Msg") or data.get("List", {}).get("erroMsg"),
            )
        if items:
            self.logger.info(
                "探测点 %s 有 %s 条数据，回到空位置 %s 的下一页 %s 继续",
                last_id, len(items), empty_at, empty_at - self.PAGE_SIZE,
            )
            # 回到"空位置"的前一页（即 empty_at - PAGE_SIZE）继续
            resume_last_id = empty_at - self.PAGE_SIZE
            if resume_last_id <= 0:
                self.logger.info("恢复点已 <=0，停止爬取")
                return
            yield scrapy.Request(
                url=self._build_url(resume_last_id),
                method="GET",
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://www.iresearch.com.cn/report.shtml?type=4",
                },
                meta={"last_id": resume_last_id},
                dont_filter=True,
                callback=self.parse,
            )
        else:
            self.logger.info(
                "探测点 %s 仍为空（空区间 [%s, %s]），停止爬取",
                last_id, last_id, empty_at,
            )

    @staticmethod
    def _extract_items(data):
        """兼容接口返回结构：列表 / {'data': [...]} / {'list': [...]}"""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("List", "data", "list", "rows", "items", "result"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []

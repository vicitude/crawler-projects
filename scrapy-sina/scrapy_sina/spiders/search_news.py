import scrapy
import json
import re
from datetime import datetime
from urllib.parse import urlencode

from scrapy.exceptions import CloseSpider

from scrapy_sina.items import SinaNewsItem
from scrapy_sina.models import SinaNews

class SearchNewsSpider(scrapy.Spider):
    name = "search_news"
    allowed_domains = ["sina.com.cn"]

    # start_urls = ["https://sina.com.cn"]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # 根据 settings 里的 LOG_FILE_APPEND 决定是覆盖还是追加
        log_file = crawler.settings.get("LOG_FILE")
        if log_file and not crawler.settings.getbool("LOG_FILE_APPEND"):
            # LOG_FILE_APPEND 未设置或为 False → 覆盖：清空文件
            open(log_file, "w", encoding="utf-8").close()
        # LOG_FILE_APPEND = True → 追加：什么都不做，让 Scrapy 正常追加
        spider = super().from_crawler(crawler, *args, **kwargs)
        # peewee 数据库连接（pipeline 已经在 open_spider 里 connect 了，
        # 这里不再重复 connect，复用同一个 database 对象）
        return spider

    def start_requests(self):
        # 入口：和原来一样从第 1 页开始，yield 第一个请求
        yield self.create_page_request(1)

    def create_page_request(self, page):
        # 翻页控制：和原来 page > 10 一样的停止条件
        if page > 10:
            return None

        # 接口参数（按你 Postman 抓到的字段）
        query_params = {
            "q": "ai",
            "tp": "mix",
            "sort": "0",
            "page": str(page),
            "size": "10",
            "from": "search_result",
        }
        # 和原来拼 body 一样，这里拼 query string
        query_string = urlencode(query_params)
        url = f"https://search.sina.com.cn/api/search?{query_string}"

        headers = {
            # 接口返回 JSON，不是表单，所以 content-type 不再需要 form
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://search.sina.com.cn/",
        }

        return scrapy.Request(
            url=url,
            method="GET",  # 原来是 POST，这里换成 GET
            headers=headers,
            callback=self.parse,
            meta={"page": page},
        )

    def parse(self, response):
        # 和原来的 self.logger.debug(...) 保持一致
        page = response.meta["page"]
        self.logger.info(f"当前请求第{page}页")

        try:
            # 接口返回 JSON，不再是 HTML，所以换成 response.json()
            data = json.loads(response.text)

            # 取列表：实际结构是 data.data.list（和 Postman 返回一致）
            result_list = data.get("data", {}).get("list", [])
            self.logger.info(f"页面中有{len(result_list)}条新闻")

            for item in result_list:
                # title 里可能带 <font color='red'>AI</font> 这类高亮标签，用正则去掉 HTML 标签只留纯文本
                raw_title = item.get("title", "")
                clean_title = re.sub(r"<[^>]+>", "", raw_title).strip()

                news = {
                    "title": clean_title,
                    "url": item.get("url", ""),
                    "media": item.get("media_show", ""),
                    "ctime": item.get("ctime", ""),
                    "time": item.get("time", ""),
                    "intro": item.get("intro", ""),
                    "thumb": item.get("thumb", ""),
                }
                self.logger.info(f"新闻标题：{news['title']}，详情页url：{news['url']}")
                # 断点续爬：用 peewee 按 title 查重
                # 用 .get_or_none() 而不是 len(select)，避免触发 SELECT 所有列
                exists_record = SinaNews.select(SinaNews.id).where(
                    SinaNews.title == news["title"]
                ).get_or_none()
                if exists_record is not None:
                    self.logger.info(
                        f"发现已存在的新闻（{news['title']}），认为后续都已爬取，终止爬虫"
                    )
                    raise CloseSpider(f"duplicate_found: {news['title']}")
                # 没找到，发详情页请求
                yield scrapy.Request(
                    url=news["url"],
                    method="GET",
                    callback=self.parse_news_detail,
                    meta={"title": news["title"]},
                )





            # 翻页：和原来思路一样，请求下一页
            next_request = self.create_page_request(page + 1)
            if next_request:
                yield next_request
        except CloseSpider:
            raise  # CloseSpider 必须透传，让 Scrapy 正常终止
        except Exception as e:
            self.logger.error(f"解析第{page}页失败: {e}")

    def parse_news_detail(self, response):
        # 详情页解析逻辑（按你给的版本原样保留）
        news_title = response.meta["title"]
        try:
            news_publish_time = response.xpath("//span[@class='date']/text()").get()
            if news_publish_time is None or news_publish_time.strip() == "":
                raise Exception(f"详情页获取发布时间失败，URL：{response.url}")
            news_publish_time = news_publish_time.strip()
            news_publish_time = datetime.strptime(news_publish_time, "%Y年%m月%d日 %H:%M")
            content_element_list = response.xpath(
                "//div[@class='article']//p | //div[@class='article']//img"
            )
            if len(content_element_list) == 0:
                is_media_only = response.xpath(
                    "//video | //div[contains(@class,'video') or contains(@class,'player')]"
                ).get() is not None
                if is_media_only:
                    self.logger.info(f"详情页无文本正文，URL：{response.url}")
                    return
                else:
                    raise Exception(f"详情页获取正文内容失败，URL：{response.url}")
            news_content = ""
            for content_element in content_element_list:
                if content_element.xpath("self::p"):
                    p_text = content_element.xpath("./text()").get()
                    if p_text is not None and p_text.strip() != "":
                        news_content = news_content + f"{p_text}\n"
                if content_element.xpath("self::img"):
                    img_src = content_element.xpath("./@src").get()
                    if img_src is not None and img_src.strip() != "":
                        news_content = news_content + f"<img src='{img_src}' />\n"
            self.logger.info(
                f"解析新闻详情页，url：{response.request.url}\n"
                f"标题：{news_title}, 日期：{news_publish_time}\n"
                f"正文长度：{len(news_content)} 字，前200字：{news_content[:200]}"
            )
            item = SinaNewsItem(
                title=news_title,
                publish_time=news_publish_time,
                content=news_content,
            )
            yield item
        except Exception as e:
            self.logger.error(f"详情页解析出现异常：{e}")
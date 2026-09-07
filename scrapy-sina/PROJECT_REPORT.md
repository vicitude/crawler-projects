# Sina 新闻爬虫项目报告（scrapy_sina）

> 本报告记录了本项目的架构、关键设计决策、踩过的坑和最终实现。任何要做类似 Scrapy + peewee + MySQL 项目的 AI / 工程师，都可以参考本报告作为模板。

---

## 1. 项目目标

从新浪搜索 API 抓取"AI"关键词相关的新闻，包含：
- **列表页**：调用新浪搜索 API（GET），分页拉取新闻条目
- **详情页**：请求每条新闻的详情页 URL，提取正文
- **入库**：用 peewee ORM 写入 MySQL
- **断点续爬**：数据库中已有 title 不再爬取
- **日志**：保存到文件，每次启动覆盖（不留历史）

---

## 2. 项目结构

```
scrapy_sina/
├── scrapy.cfg                  # Scrapy 项目配置
├── scrapy_sina/                # Python 包
│   ├── __init__.py
│   ├── items.py                # Item 定义（SinaNewsItem）
│   ├── models.py               # peewee ORM 模型（SinaNews → ai_news 表）
│   ├── pipelines.py            # 数据入库 pipeline
│   ├── settings.py             # 全局配置（日志、DB、ITEM_PIPELINES）
│   ├── middlewares.py          # （默认空，未使用）
│   └── spiders/
│       ├── __init__.py
│       └── search_news.py      # 爬虫主逻辑
└── logs/
    └── search_news.log         # 爬虫日志（覆盖式）
```

---

## 3. 数据流

```
1. start_requests() → 发起第 1 页 GET 请求（API）
2. parse(response) → 解析 JSON，遍历列表
   ├─ 查 peewee：title 是否已在 ai_news？
   │   ├─ 在 → raise CloseSpider，终止爬虫（断点续爬）
   │   └─ 不在 → yield 详情页 Request
   └─ 翻页 → 继续 create_page_request(page+1)
3. parse_news_detail(response) → XPath 解析详情页
   ├─ 有 <p>/<img> → yield SinaNewsItem
   ├─ 有 <video>（纯视频）→ return 跳过（不入库）
   └─ 既无正文又无视频 → raise Exception（logger.error）
4. MysqlSinaNewsPipeline.process_item(item, spider) → peewee 查重 + INSERT
```

---

## 4. 关键文件说明

### 4.1 [scrapy_sina/items.py](file:///D:/python/Program/scrape/fourth_week/scrapy_sina/scrapy_sina/items.py)

定义 Scrapy Item：

```python
class SinaNewsItem(scrapy.Item):
    title = scrapy.Field()
    publish_time = scrapy.Field()
    content = scrapy.Field()
    spider_time = scrapy.Field()
```

### 4.2 [scrapy_sina/models.py](file:///D:/python/Program/scrape/fourth_week/scrapy_sina/scrapy_sina/models.py)

peewee ORM 模型，映射到 `spider_sina.ai_news` 表：

```python
from peewee import MySQLDatabase, Model, AutoField, CharField, DateTimeField, TextField
from scrapy.utils.project import get_project_settings

settings = get_project_settings()
db = MySQLDatabase(
    database=settings.get("MYSQL_DATABASE"),
    host=settings.get("MYSQL_HOST"),
    port=settings.get("MYSQL_PORT"),
    user=settings.get("MYSQL_USERNAME"),
    password=settings.get("MYSQL_PASSWORD"),
)

class SinaNews(Model):
    id = AutoField()
    title = CharField(unique=True)        # ← unique 是断点续爬的基础
    publish_time = DateTimeField()
    content = TextField()
    spider_time = DateTimeField()

    class Meta:
        database = db
        db_table = "ai_news"
```

**关键决策**：
- 用 `get_project_settings()` 读 Scrapy settings
- `title` 设为 `unique=True`，数据库层也有 UNI 约束
- `db` 是**全局单例**，spider 和 pipeline 共享

### 4.3 [scrapy_sina/pipelines.py](file:///D:/python/Program/scrape/fourth_week/scrapy_sina/scrapy_sina/pipelines.py)

入库 pipeline，连接管理 + 去重 + INSERT：

```python
class MysqlSinaNewsPipeline:
    def open_spider(self, spider):
        if SinaNews._meta.database.is_closed():
            SinaNews._meta.database.connect()
            spider.logger.info("MySQL 连接已打开")

    def close_spider(self, spider):
        if not SinaNews._meta.database.is_closed():
            SinaNews._meta.database.close()
            spider.logger.info("MySQL 连接已关闭")

    def process_item(self, item, spider):
        if not isinstance(item, SinaNewsItem):
            return item

        adapter = ItemAdapter(item)
        try:
            # 关键写法：只用 select(id) + get_or_none()，不要 .exists() 或 select()
            exists_record = SinaNews.select(SinaNews.id).where(
                SinaNews.title == adapter["title"]
            ).get_or_none()
            if exists_record is not None:
                raise DropItem(f"Duplicate item found: {adapter['title']}")

            SinaNews.create(
                title=adapter["title"],
                publish_time=adapter["publish_time"],
                content=adapter["content"],
                spider_time=datetime.now(),
            )
        except DropItem:
            raise
        except Exception as e:
            spider.logger.error(f"入库失败：{adapter['title']}，错误：{e}")
            raise
        return item
```

### 4.4 [scrapy_sina/settings.py](file:///D:/python/Program/scrape/fourth_week/scrapy_sina/scrapy_sina/settings.py)

关键配置块（项目通用部分省略）：

```python
# 日志
LOG_FILE = "logs/search_news.log"
LOG_LEVEL = "INFO"
LOG_FILE_APPEND = False   # 覆盖写，每次启动清空旧日志

# Item pipeline
ITEM_PIPELINES = {
    "scrapy_sina.pipelines.MysqlSinaNewsPipeline": 300,
}

# MySQL
MYSQL_DATABASE = "spider_sina"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USERNAME = "root"
MYSQL_PASSWORD = "<your_mysql_password>"

# 爬虫节奏
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 0.25
ROBOTSTXT_OBEY = False
```

### 4.5 [scrapy_sina/spiders/search_news.py](file:///D:/python/Program/scrape/fourth_week/scrapy_sina/scrapy_sina/spiders/search_news.py)

爬虫主文件，包含：
1. `from_crawler` - 日志覆盖写入预处理
2. `start_requests` - 入口，发第 1 页
3. `create_page_request(page)` - 翻页控制（page > 10 停止）
4. `parse(response)` - 列表页，JSON 解析 + peewee 查重 + CloseSpider
5. `parse_news_detail(response)` - 详情页 XPath 解析

---

## 5. 关键技术决策（踩坑总结）

### 5.1 列表页用 GET，不用 POST

- **决策**：原项目是 POST + form body；新浪改版后 API 是 GET + query string
- **依据**：Postman 抓包返回的 URL 是完整 query string 形式
- **写法**：

```python
query_string = urlencode(query_params)
url = f"https://search.sina.com.cn/api/search?{query_string}"
yield scrapy.Request(url=url, method="GET", headers=headers, callback=self.parse, meta={"page": page})
```

### 5.2 title 含 `<font>` 标签，要清洗

- **现象**：新浪 API 返回的 `title` 字段含 `<font color='red'>AI</font>` 高亮标签
- **解决**：用正则去掉 HTML 标签

```python
raw_title = item.get("title", "")
clean_title = re.sub(r"<[^>]+>", "", raw_title).strip()
```

### 5.3 peewee 查重要用 `select(id).get_or_none()`，**绝对不要**用 `.exists()` 或 `len(select)`

- **坑**：`.exists()` 或 `len(select())` 会让 peewee 生成 `SELECT *` 语句，**会查所有列**
- **症状**：`Unknown column 't1.publish_time' in 'field list'`（即使列存在也会报）
- **根本原因**：peewee 在某些情况下生成的 column 名带 `t1.` 别名前缀，且会查所有 model 字段对应的列。如果 schema 不一致（比如迁移后 peewee 缓存了旧 schema、或某些 MySQL 字符集配置导致列名解析异常），就会报这个错。
- **解决**：**明确指定只查 `id` 列**，生成的 SQL 就只有 `SELECT t1.id FROM ai_news t1 WHERE t1.title = %s LIMIT 1`

```python
# ✅ 推荐写法
exists_record = SinaNews.select(SinaNews.id).where(
    SinaNews.title == some_title
).get_or_none()
if exists_record is not None:
    ...

# ❌ 不要这样写（会触发 SELECT 所有列）
SinaNews.select().where(...).exists()
len(SinaNews.select().where(...))
```

### 5.4 断点续爬用 `CloseSpider`，不要 `break` + 手动终止

- **决策**：列表页命中已存在 title 时，抛 `CloseSpider`
- **优势**：
  - `finish_reason` 会显示具体原因（如 `duplicate_found: xxx`）
  - Scrapy 优雅关闭，不再发新请求
  - 不会污染日志成 `ERROR`
- **关键**：`except` 中必须透传 `CloseSpider`，否则终止信号会被吞

```python
try:
    ...
    if exists_record is not None:
        raise CloseSpider(f"duplicate_found: {news['title']}")
    ...
except CloseSpider:
    raise  # 必须透传！
except Exception as e:
    self.logger.error(f"解析第{page}页失败: {e}")
```

### 5.5 详情页"纯视频页"判断逻辑

- **规则**：详情页只解析 `<div class="article">` 容器里的 `<p>` 和 `<img>`
- **兜底**：如果该容器内没有任何 `<p>/<img>`，但页面里有 `<video>` 或 class 含 `video/player` 的 div → 视为纯视频页，return 跳过
- **判断逻辑 XPath 对比**：

| XPath | 范围 |
|---|---|
| 正文：`<div class="article">` 内的 `<p>/<img>` | 严格限定容器 |
| video 兜底：`//video` 或 class 含 `video/player` 的 div | 全页面（兜底要宽松）|

### 5.6 日志覆盖式写入

- **需求**：每次启动爬虫清空旧日志，文件里只有本次的
- **实现**：在 `from_crawler` 里手动 `open(log_file, "w")` 清空
- **为什么 Scrapy 的 `LOG_FILE_APPEND` 不靠谱**：
  - 在 Scrapy 2.13.4 上实测，默认行为是**追加**而不是覆盖
  - 即便源码里写的是 `mode = "a" if LOG_FILE_APPEND else "w"`，实际行为却不是这样
- **兜底方案**：

```python
@classmethod
def from_crawler(cls, crawler, *args, **kwargs):
    log_file = crawler.settings.get("LOG_FILE")
    if log_file and not crawler.settings.getbool("LOG_FILE_APPEND"):
        open(log_file, "w", encoding="utf-8").close()  # 强制清空
    return super().from_crawler(crawler, *args, **kwargs)
```

### 5.7 Scrapy `start_requests` vs `async def start`

- **决策**：用 `start_requests`，不用 `async def start`
- **理由**：
  - 初学阶段更直观
  - 所有 Scrapy 文档都用这个
  - `async def start` 里**不能传 callback**，要靠 Scrapy 默认路由到 `parse`
- **警告**：Scrapy 2.13+ 已经 deprecate `start_requests`，未来要迁移到 `start()`

### 5.8 scrapy.Request `dont_filter` 的使用

- **决策**：**不使用** `dont_filter=True`
- **作用**：Scrapy 默认按 URL + method + headers + body 生成指纹去重
- **坑**：同一页 URL 多次访问时，`dont_filter=True` 会强制不去重

---

## 6. 数据库表设计

```sql
CREATE TABLE ai_news (
    id            INT          NOT NULL AUTO_INCREMENT,
    title         VARCHAR(500) NOT NULL,
    publish_time  DATETIME     NOT NULL,
    content       TEXT,
    spider_time   DATETIME     NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY title (title)
);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 主键，自增 |
| `title` | varchar(500) | 新闻标题，**唯一约束** |
| `publish_time` | datetime | 新闻发布时间（从详情页 XPath 解析）|
| `content` | text | 正文 + 图片（HTML 拼接）|
| `spider_time` | datetime | 抓取时间（代码填入 `datetime.now()`）|

---

## 7. 运行方式

```bash
cd D:\python\Program\scrape\fourth_week\scrapy_sina
scrapy crawl search_news
```

预期日志输出（断点续爬命中后）：

```
INFO: 当前请求第1页
INFO: 页面中有10条新闻
INFO: 新闻标题：xxx
...
INFO: 发现已存在的新闻（xxx），认为后续都已爬取，终止爬虫
INFO: Closing spider (duplicate_found: xxx)
INFO: MySQL 连接已关闭
INFO: Dumping Scrapy stats:
'finish_reason': 'duplicate_found: xxx',
'log_count/ERROR': 0,
```

---

## 8. 复现这个项目的步骤（给 AI/新人的 checklist）

要做类似项目（Scrapy + peewee + MySQL + JSON API + 详情页 + 断点续爬）：

- [ ] 1. 用 `scrapy startproject <name>` 创建项目
- [ ] 2. Postman 抓包，确认 API 是 GET 还是 POST、参数怎么传、返回 JSON 结构
- [ ] 3. 在 [items.py](file:///D:/python/Program/scrape/fourth_week/scrapy_sina/scrapy_sina/items.py) 定义 Item 字段
- [ ] 4. 在 [models.py](file:///D:/python/Program/scrape/fourth_week/scrapy_sina/scrapy_sina/models.py) 定义 peewee 模型
- [ ] 5. 在 settings.py 配置 MySQL、日志、ITEM_PIPELINES
- [ ] 6. 在 [pipelines.py](file:///D:/python/Program/scrape/fourth_week/scrapy_sina/scrapy_sina/pipelines.py) 写 `MysqlXxxPipeline`，**必须用 `select(id).get_or_none()` 查重**
- [ ] 7. 在 spider 里实现：`start_requests` / `create_page_request` / `parse` / `parse_detail`
- [ ] 8. 在 `parse` 列表循环里加 peewee 查重，命中抛 `CloseSpider`
- [ ] 9. 在 `from_crawler` 里加日志覆盖写入逻辑
- [ ] 10. 数据库表加 `UNIQUE` 约束（防并发写入时重复）
- [ ] 11. 测试运行：`scrapy crawl <name>`

---

## 9. 已知的坑和限制

| 坑 | 描述 | 影响 |
|---|---|---|
| Scrapy 2.13.4 日志覆盖行为 | 默认是追加不是覆盖 | 已通过手动 `open(w)` 兜底 |
| peewee `.exists()` / `len(select)` | 会触发 `SELECT *` | 已改为 `select(id).get_or_none()` |
| 详情页 XPath 容错 | `//span[@class='date']` 在新版新浪可能失效 | 当前未处理（XPath 改版需手动维护）|
| 断点续爬假设"按时间倒序" | 如果接口顺序乱了可能漏数据 | 当前未处理（依赖新浪 API 默认排序）|
| `start_requests` 已 deprecate | Scrapy 2.13 警告，未来版本可能移除 | 暂未迁移，未来需用 `async def start` |
| 详情页"图文视频混排但 video 在 article 外" | 会被当成纯图文，video 不入库 | 已识别，未修 |

---

## 10. 未来优化方向

| 优化 | 说明 |
|---|---|
| 详情页 XPath fallback | 准备多套 XPath，主路径失败时试 fallback |
| 数据库迁移用 peewee | 用 `playhouse.migrate` 管理 schema 变更 |
| 接入代理池 | 当前没限速容易被 ban，可加代理 middleware |
| 详情页 video 入库 | 改 `parse_news_detail` 把 `<video>` 也拼进 content |
| 迁移到 `async def start` | 跟上 Scrapy 2.13+ 新写法 |
| 数据库迁移工具 | peewee 自带 `migrate`，管理 schema |

---

## 11. 关键技术关键词

供未来 AI 检索：

- Scrapy 2.13.4
- peewee ORM（不是 peewee-async）
- MySQL / pymysql 兼容
- POST → GET 转换（API 改版）
- CloseSpider 异常 + 透传
- Scrapy `LOG_FILE` 覆盖写入
- peewee `.get_or_none()` 查重模式
- `select(field).where()` 显式列查询
- 断点续爬 + 唯一索引去重
- JSON API + 详情页混合爬虫

---

## 12. 一句话总结

**这是一个"列表用 API + 详情用 HTML"的混合爬虫，关键在于 peewee查重要用 `select(id).get_or_none()` 而不是 `.exists()`，以及 `CloseSpider` 一定要在 except 中透传。**
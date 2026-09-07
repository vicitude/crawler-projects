# crawler-projects

本仓库收录 7 个 Python 爬虫与浏览器自动化项目，覆盖 Scrapy、接口采集、数据持久化和 Selenium 页面操作等场景。

| # | 项目 | 核心技术 | 场景 | 量级 | 位置 |
|---|---|---|---|---|---|
| 1 | [iresearch-chart](./iresearch-chart) | Scrapy 全套组件 + JSONL + ImagesPipeline | 批量采集图表元数据 + 缩略图 | 8500 条 | [`iresearch-chart/`](./iresearch-chart) |
| 2 | [scrapy-sina](./scrapy-sina) | Scrapy + peewee + MySQL | 混合爬虫（API + HTML）、跨进程去重、优雅终止 | 多页连续 | [`scrapy-sina/`](./scrapy-sina) |
| 3 | [eastmoney](./eastmoney) | curl_cffi + peewee + JSONP | 金融数据接口逆向 + 4 表事务化写入 | 全市场 2317 只 | [`eastmoney/`](./eastmoney) |
| 4 | [lianjia](./lianjia) | Scrapy + CSS/XPath + 自定义 ItemExporter | 整站房产数据采集、UTF-8 BOM CSV 导出 | 单页 30 套 | [`lianjia/`](./lianjia) |
| 5 | [selenium-douban-login](./selenium-douban-login) | Selenium + iframe + 显式等待 | 安全的登录流程演示，验证码人工完成 | 单页交互 | [`selenium-douban-login/`](./selenium-douban-login) |
| 6 | [selenium-baidu-map](./selenium-baidu-map) | Selenium + 路线查询 + 截图 | 公交路线列表读取与页面截图 | 多路线 | [`selenium-baidu-map/`](./selenium-baidu-map) |
| 7 | [selenium-bilibili](./selenium-bilibili) | Selenium + DOM 解析 | UP 主公开代表作信息提取 | 多卡片 | [`selenium-bilibili/`](./selenium-bilibili) |

## 技术共性

- **Python 3.9+** · **Scrapy** · **peewee ORM** · **MySQL**
- **反爬对抗**：`curl_cffi` 绕过 TLS 指纹 / 随机 UA / Referer 防盗链 / 限流节奏
- **工程化**：断点续爬 / 跨进程去重 / 事务一致性 / 日志覆盖 / Scrapy 绘制扩展
- **AI 辅助开发**：Trae / Codex 常规使用，并能独立 Debug

## 项目结构

```
crawler-projects/
├── iresearch-chart/     # 项目 1：艾瑞咨询图表批量采集
│   ├── scrapy.cfg
│   └── iresearch/
│       ├── items.py / middlewares.py / pipelines.py / settings.py
│       └── spiders/iresearch_chart.py
├── scrapy-sina/         # 项目 2：新浪新闻混合爬虫
│   ├── scrapy.cfg
│   ├── PROJECT_REPORT.md
│   ├── run_scrapya_spider.bat
│   └── scrapy_sina/
│       ├── cookie_helper.py / items.py / middlewares.py
│       ├── models.py / pipelines.py / settings.py
│       └── spiders/search_news.py
├── eastmoney/          # 项目 3：东方财富股票行情
│   ├── main.py          # 解析层：API + JSONP + 主循环
│   ├── data_header.py   # 数据库层：4 个 peewee 模型
│   └── 项目总结文档.md
├── lianjia/            # 项目 4：链家二手房整站采集
│   ├── scrapy.cfg
│   └── lianjia_project/
│       ├── exporters.py / items.py / middlewares.py / pipelines.py / settings.py
│       └── spiders/lianjia.py
├── selenium-douban-login/ # 项目 5：豆瓣滑块验证码自动登录
├── selenium-baidu-map/    # 项目 6：百度地图公交路线查询
└── selenium-bilibili/     # 项目 7：B 站 UP 主代表作采集
```

## 按项目详情

### 1. 艾瑞咨询图表批量采集 ⭐

**场景**：从艾瑞咨询图表 API 批量拉取图表元数据 + 缩略图，目标量 8500 条。

**技术亮点**：
- 探测式翻页：自研 `parse_probe` 回调，遇空数据回退 `PROBE_BACK_STEP=100` 步探测边界
- 跨进程断点续爬：`IresearchDeduplicatePipeline.open_spider` 从历史 JSONL 恢复 `seen` 集合
- 图片防盗链：自定义 `ImagesPipeline.get_media_requests` 注入 `Referer`，`file_path` 用 `chart_id` 命名
- 接口结构兼容：`_extract_items` 同时识别 6 种返回 key

详见：[`iresearch-chart/PROJECT.md`](./iresearch-chart/PROJECT.md)

### 2. 新浪新闻分布式爬虫

**场景**：抓取「AI」关键词相关新闻，列表 JSON 接口 + 详情 HTML，构建可断点续爬的入库系统。

**技术亮点**：
- 混合爬虫架构：列表 GET API + 详情 XPath
- peewee 查重优化：必须用 `SinaNews.select(SinaNews.id).where(...).get_or_none()`，规避 `.exists()` 触发 `SELECT *` 隐患
- CloseSpider 优雅终止：`except CloseSpider: raise` 必须透传
- 日志覆盖写入：Scrapy 2.13 默认追加不覆盖，需手动 `open(log_file, 'w').close()`
- MySQL `UNIQUE KEY` 最后一道防重

详见：[`scrapy-sina/PROJECT_REPORT.md`](./scrapy-sina/PROJECT_REPORT.md)

### 3. 东方财富股票行情数据采集

**场景**：抓取 A 股全市场 2317 只个股行情 + 所属板块 + 个股-板块多对多关联，持久化到 MySQL 4 张关联表。

**技术亮点**：
- TLS 指纹绕过：`curl_cffi` 而非 `requests`，模拟 Chrome JA3 指纹过 WAF
- JSONP 协议解析：正则 `r'\((.*)\)\s*;?\s*$'` 剥离 jQuery 包裹
- 字段单位换算：JSONP 字段 f43~f288 价格 /100、成交量 /10000、市值 /1亿等
- 4 表关联建模：`stock_info_least` + `stock_info_history` + `sector_info` + `stock_sector`
- peewee 事务化写入：`db.atomic()` 包住 4 张表写入，失败全回滚

详见：[`eastmoney/项目总结文档.md`](./eastmoney/%E9%A1%B9%E7%9B%AE%E6%80%BB%E7%BB%93%E6%96%87%E6%A1%A3.md)

### 4. 链家二手房整站采集系统

**场景**：抓取链家二手房列表 + 详情，提取 14 维房源字段后导出为 UTF-8 BOM CSV。

**技术亮点**：
- 列表页精准翻页：从 `page-data` JSON 读 `totalPage + curPage`，模板拼下一页
- 14 字段抽取：CSS Selector + XPath，`label_value_map` 正则切字典
- Pipeline 数据标准化：万元 → 元换算、平米单位统一、税费类型归一
- UTF-8 BOM CSV：自定义 `Utf8SigCsvItemExporter`，Excel 打开中文不乱码

### 5–7. Selenium 浏览器自动化项目

- 豆瓣：演示 iframe、显式等待和环境变量读取；验证码保留人工完成
- 百度地图：查询公交路线、读取路线列表并保存页面截图
- 哔哩哔哩：解析公开主页的代表作卡片信息
- 均使用 Selenium Manager 管理 ChromeDriver，不提交 Chrome 用户目录、Cookie 或缓存

## 环境要求

- Python 3.9+
- Scrapy 2.x（项目 1 / 2 / 4）
- curl_cffi 0.5+ （项目 3）
- peewee 3.x + pymysql（项目 2 / 3）
- MySQL 5.7+（项目 2 / 3）
- Selenium 4.11+（项目 5 / 6 / 7）

## 敏感信息说明

本仓库中任何地方都不含真实账号 / Cookie / 密码。如需本地运行：

- 复制 `.env.example` 为 `.env`，填入 MySQL 密码
- 项目 4（链家）需自行创建 `爬虫数据项.txt` 填入 Cookie

## License

MIT

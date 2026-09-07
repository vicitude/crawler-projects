"""
data_header.py

东方财富网爬虫的数据库层：定义 4 张表的 peewee 模型 + 写入函数
- stock_info_least: 个股最新行情（按 stock_code 单主键）
- stock_info_history: 个股历史行情（联合主键 history_date + stock_code）
- sector_info: 板块信息（按 sector_code 单主键，字典表）
- stock_sector: 个股与板块的关联关系（联合主键 stock_code + sector_code，中间表）

依赖：peewee（mysql orm），main.py 负责调用 write_spider_data 写入
"""

# ==================== 第三方库 ====================
import datetime  # 入库时间戳
import traceback  # 出错时打印完整堆栈

# ==================== peewee 数据库相关 ====================
from peewee import MySQLDatabase, Model  # mysql数据库
from peewee import AutoField, CharField, IntegerField, DecimalField  # 字段类型
from peewee import DateField, DateTimeField, BooleanField, CompositeKey  # 日期、时间、布尔、联合主键


# ==================== 数据库连接 ====================
import os
db = MySQLDatabase(
    database=os.getenv('MYSQL_DB', 'spider_eastmoney'),
    host=os.getenv('MYSQL_HOST', 'localhost'),
    port=int(os.getenv('MYSQL_PORT', '3306')),
    user=os.getenv('MYSQL_USER', 'root'),
    password=os.getenv('MYSQL_PASSWORD', '')
)


# ==================== 模型定义 ====================

# 个股最新行情表（按 stock_code 单主键）
class Stock_Info_Least(Model):
    stock_code = CharField(max_length=255, primary_key=True)  # 股票ID
    stock_name = CharField(max_length=255, null=True)  # 股票名称
    update_time = DateTimeField(null=True)  # 行情时间
    least_price = DecimalField(max_digits=10, decimal_places=2, null=True)  # 最新价
    high_price = DecimalField(max_digits=10, decimal_places=2, null=True)  # 最高价
    low_price = DecimalField(max_digits=10, decimal_places=2, null=True)  # 最低价
    volume = DecimalField(max_digits=10, decimal_places=2, null=True)  # 成交量（万手）
    turnover = DecimalField(max_digits=10, decimal_places=2, null=True)  # 成交额（亿元）
    total_market = DecimalField(max_digits=10, decimal_places=2, null=True)  # 总市值（亿元）
    circulate_market = DecimalField(max_digits=10, decimal_places=2, null=True)  # 流通市值（亿元）
    pe_dynamic = DecimalField(max_digits=10, decimal_places=2, null=True)  # 动态市盈率
    pe_static = DecimalField(max_digits=10, decimal_places=2, null=True)  # 静态市盈率
    pe_ttm = DecimalField(max_digits=10, decimal_places=2, null=True)  # 滚动市盈率
    turnover_rate_percent = DecimalField(max_digits=10, decimal_places=2, null=True)  # 换手率（%）
    change_rate_percent = DecimalField(max_digits=10, decimal_places=2, null=True)  # 当日涨跌幅（%）
    is_profit = CharField(max_length=255, null=True)  # 是否盈利

    class Meta:
        database = db
        table_name = "stock_info_least"

    # 工厂方法：从 stock_info_dict 构造模型实例
    @classmethod
    def get_instance(cls, stock_info_dict):
        return cls(
            stock_code=stock_info_dict['stock_code'],
            stock_name=stock_info_dict.get('stock_name'),
            update_time=stock_info_dict.get('quote_datetime'),
            least_price=stock_info_dict.get('price'),
            high_price=stock_info_dict.get('high_price'),
            low_price=stock_info_dict.get('low_price'),
            volume=stock_info_dict.get('volume_wan_hand'),
            turnover=stock_info_dict.get('turnover_yi'),
            total_market=stock_info_dict.get('total_market_yi'),
            circulate_market=stock_info_dict.get('circulate_market_yi'),
            pe_dynamic=stock_info_dict.get('pe_dynamic'),
            pe_static=stock_info_dict.get('pe_static'),
            pe_ttm=stock_info_dict.get('pe_ttm'),
            turnover_rate_percent=stock_info_dict.get('turnover_rate_percent'),
            change_rate_percent=stock_info_dict.get('change_rate_percent'),
            is_profit=stock_info_dict.get('is_profit'),
        )


# 个股历史行情表（联合主键 history_date + stock_code）
class Stock_Info_History(Model):
    history_date = DateField()  # 历史日期（联合主键1）
    stock_code = CharField(max_length=255)  # 股票ID（联合主键2）
    stock_name = CharField(max_length=255, null=True)  # 股票名称
    update_time = DateTimeField(null=True)  # 行情时间
    least_price = DecimalField(max_digits=10, decimal_places=2, null=True)  # 最新价
    high_price = DecimalField(max_digits=10, decimal_places=2, null=True)  # 最高价
    low_price = DecimalField(max_digits=10, decimal_places=2, null=True)  # 最低价
    volume = DecimalField(max_digits=10, decimal_places=2, null=True)  # 成交量（万手）
    turnover = DecimalField(max_digits=10, decimal_places=2, null=True)  # 成交额（亿元）
    total_market = DecimalField(max_digits=10, decimal_places=2, null=True)  # 总市值（亿元）
    circulate_market = DecimalField(max_digits=10, decimal_places=2, null=True)  # 流通市值（亿元）
    pe_dynamic = DecimalField(max_digits=10, decimal_places=2, null=True)  # 动态市盈率
    pe_static = DecimalField(max_digits=10, decimal_places=2, null=True)  # 静态市盈率
    pe_ttm = DecimalField(max_digits=10, decimal_places=2, null=True)  # 滚动市盈率
    turnover_rate_percent = DecimalField(max_digits=10, decimal_places=2, null=True)  # 换手率（%）
    change_rate_percent = DecimalField(max_digits=10, decimal_places=2, null=True)  # 当日涨跌幅（%）
    is_profit = CharField(max_length=255, null=True)  # 是否盈利

    class Meta:
        database = db
        table_name = "stock_info_history"
        primary_key = CompositeKey('history_date', 'stock_code')  # 联合主键

    # 工厂方法：从 stock_info_dict 构造模型实例，history_date 从行情时间取日期部分
    @classmethod
    def get_instance(cls, stock_info_dict):
        quote_dt = stock_info_dict.get('quote_datetime')
        history_date_val = quote_dt.date() if quote_dt else None
        return cls(
            history_date=history_date_val,
            stock_code=stock_info_dict['stock_code'],
            stock_name=stock_info_dict.get('stock_name'),
            update_time=quote_dt,
            least_price=stock_info_dict.get('price'),
            high_price=stock_info_dict.get('high_price'),
            low_price=stock_info_dict.get('low_price'),
            volume=stock_info_dict.get('volume_wan_hand'),
            turnover=stock_info_dict.get('turnover_yi'),
            total_market=stock_info_dict.get('total_market_yi'),
            circulate_market=stock_info_dict.get('circulate_market_yi'),
            pe_dynamic=stock_info_dict.get('pe_dynamic'),
            pe_static=stock_info_dict.get('pe_static'),
            pe_ttm=stock_info_dict.get('pe_ttm'),
            turnover_rate_percent=stock_info_dict.get('turnover_rate_percent'),
            change_rate_percent=stock_info_dict.get('change_rate_percent'),
            is_profit=stock_info_dict.get('is_profit'),
        )


# 板块信息表（字典表，按 sector_code 单主键）
class Sector_Info(Model):
    sector_code = CharField(max_length=255, primary_key=True)  # 板块ID
    sector_name = CharField(max_length=255, null=True)  # 板块名称

    class Meta:
        database = db
        table_name = "sector_info"

    # 工厂方法：从 sector_dict 构造模型实例
    @classmethod
    def get_instance(cls, sector_dict):
        return cls(
            sector_code=sector_dict['sector_code'],
            sector_name=sector_dict.get('sector_name'),
        )


# 个股与板块关联表（中间表，联合主键 stock_code + sector_code）
class Stock_Sector(Model):
    stock_code = CharField(max_length=255)  # 股票ID（联合主键1）
    sector_code = CharField(max_length=255)  # 板块ID（联合主键2）

    class Meta:
        database = db
        table_name = "stock_sector"
        primary_key = CompositeKey('stock_code', 'sector_code')  # 联合主键


# ==================== 写入函数 ====================

# 写入个股最新行情表，并返回 stock_code
def write_to_stock_info_least(stock_info):
    # 判断个股最新行情是否存在（按 stock_code 主键查）
    select_result = Stock_Info_Least.select().where(Stock_Info_Least.stock_code == stock_info.stock_code)
    if len(select_result) > 0:  # 存在
        # 存在则走显式 update（不用 save()，避免 lastrowid 误导）
        print(f'个股最新行情已存在，执行更新操作，股票代码：{stock_info.stock_code}')
        update_count = Stock_Info_Least.update(
            stock_name=stock_info.stock_name,
            update_time=stock_info.update_time,
            least_price=stock_info.least_price,
            high_price=stock_info.high_price,
            low_price=stock_info.low_price,
            volume=stock_info.volume,
            turnover=stock_info.turnover,
            total_market=stock_info.total_market,
            circulate_market=stock_info.circulate_market,
            pe_dynamic=stock_info.pe_dynamic,
            pe_static=stock_info.pe_static,
            pe_ttm=stock_info.pe_ttm,
            turnover_rate_percent=stock_info.turnover_rate_percent,
            change_rate_percent=stock_info.change_rate_percent,
            is_profit=stock_info.is_profit,
        ).where(Stock_Info_Least.stock_code == stock_info.stock_code).execute()
        print(f'个股最新行情已更新，影响了{update_count}条数据')
    else:  # 不存在
        # 不存在则走显式 insert（不用 save()，因为 CharField 主键的 save() 返回 lastrowid 永远是 0）
        print(f'个股最新行情不存在，执行插入操作，股票代码：{stock_info.stock_code}')
        Stock_Info_Least.insert(
            stock_code=stock_info.stock_code,
            stock_name=stock_info.stock_name,
            update_time=stock_info.update_time,
            least_price=stock_info.least_price,
            high_price=stock_info.high_price,
            low_price=stock_info.low_price,
            volume=stock_info.volume,
            turnover=stock_info.turnover,
            total_market=stock_info.total_market,
            circulate_market=stock_info.circulate_market,
            pe_dynamic=stock_info.pe_dynamic,
            pe_static=stock_info.pe_static,
            pe_ttm=stock_info.pe_ttm,
            turnover_rate_percent=stock_info.turnover_rate_percent,
            change_rate_percent=stock_info.change_rate_percent,
            is_profit=stock_info.is_profit,
        ).execute()
        print(f'个股最新行情已插入，股票代码：{stock_info.stock_code}')
    return stock_info.stock_code


# 写入个股历史行情表（联合主键：history_date + stock_code）
def write_to_stock_info_history(stock_info):
    # 判断该日期+股票代码是否已存在（联合主键查）
    select_result = Stock_Info_History.select().where(
        (Stock_Info_History.history_date == stock_info.history_date) &
        (Stock_Info_History.stock_code == stock_info.stock_code)
    )
    if len(select_result) > 0:
        # 存在：执行更新
        print(f'个股历史行情已存在，执行更新操作，日期+股票代码：{stock_info.history_date}, {stock_info.stock_code}')
        update_count = Stock_Info_History.update(
            stock_name=stock_info.stock_name,
            update_time=stock_info.update_time,
            least_price=stock_info.least_price,
            high_price=stock_info.high_price,
            low_price=stock_info.low_price,
            volume=stock_info.volume,
            turnover=stock_info.turnover,
            total_market=stock_info.total_market,
            circulate_market=stock_info.circulate_market,
            pe_dynamic=stock_info.pe_dynamic,
            pe_static=stock_info.pe_static,
            pe_ttm=stock_info.pe_ttm,
            turnover_rate_percent=stock_info.turnover_rate_percent,
            change_rate_percent=stock_info.change_rate_percent,
            is_profit=stock_info.is_profit,
        ).where(
            (Stock_Info_History.history_date == stock_info.history_date) &
            (Stock_Info_History.stock_code == stock_info.stock_code)
        ).execute()
        print(f'个股历史行情已更新，影响了{update_count}条数据')
    else:
        # 不存在：执行显式 insert（联合主键无自增，save() 返回 lastrowid=0 会被误判为失败）
        print(f'个股历史行情不存在，执行插入操作，日期+股票代码：{stock_info.history_date}, {stock_info.stock_code}')
        Stock_Info_History.insert(
            history_date=stock_info.history_date,
            stock_code=stock_info.stock_code,
            stock_name=stock_info.stock_name,
            update_time=stock_info.update_time,
            least_price=stock_info.least_price,
            high_price=stock_info.high_price,
            low_price=stock_info.low_price,
            volume=stock_info.volume,
            turnover=stock_info.turnover,
            total_market=stock_info.total_market,
            circulate_market=stock_info.circulate_market,
            pe_dynamic=stock_info.pe_dynamic,
            pe_static=stock_info.pe_static,
            pe_ttm=stock_info.pe_ttm,
            turnover_rate_percent=stock_info.turnover_rate_percent,
            change_rate_percent=stock_info.change_rate_percent,
            is_profit=stock_info.is_profit,
        ).execute()
        print(f'个股历史行情已插入，日期+股票代码：{stock_info.history_date}, {stock_info.stock_code}')


# 写入板块信息表（字典表：不存在则插入，存在直接返回 code）
def write_to_sector_info(sector_info):
    # 判断板块是否已存在
    select_result = Sector_Info.select().where(Sector_Info.sector_code == sector_info.sector_code)
    if len(select_result) == 0:  # 不存在则走显式 insert
        Sector_Info.insert(
            sector_code=sector_info.sector_code,
            sector_name=sector_info.sector_name,
        ).execute()
        print(f'写入板块信息成功，板块代码：{sector_info.sector_code}')
    else:
        print(f'板块信息已存在，板块代码：{sector_info.sector_code}')
    return sector_info.sector_code


# 写入个股与板块关系表（中间表）
def write_to_stock_sector_relationship(stock_code, sector_code):
    # 先看关系是否存在
    select_result = Stock_Sector.select().where(
        (Stock_Sector.stock_code == stock_code) &
        (Stock_Sector.sector_code == sector_code)
    )
    if len(select_result) == 0:
        # 不存在则走显式 insert（联合主键模型 save() 会报 'no data to save'，用 insert() 绕过）
        print(f'个股与板块关系不存在，进行插入操作')
        Stock_Sector.insert(
            stock_code=stock_code,
            sector_code=sector_code,
        ).execute()
        print(f'写入stock_sector表成功，股票代码：{stock_code}，板块代码：{sector_code}')
    else:
        # 已存在则跳过
        print(f'个股与板块关系已经存在，股票代码：{stock_code}，板块代码：{sector_code}')


# ==================== 总写入函数（事务入口） ====================

# 对外只暴露一个 write_spider_data，内部开事务，按依赖顺序依次写表
# 三个参数都是 main.py 里通过 Xxx_Info.get_instance() 构造好的模型实例
def write_spider_data(stock_info_least, stock_info_history, sector_info_list):
    # 连接数据库
    try:
        db.connect(reuse_if_open=True)
    except Exception as e:
        print(f'数据库连接失败：{e}')
        return
    # 开启事务
    with db.atomic():
        # 1. 写入个股最新行情表
        write_to_stock_info_least(stock_info_least)
        # 2. 写入个股历史行情表
        write_to_stock_info_history(stock_info_history)
        # 3. 遍历板块实例，先写板块字典表，再写个股-板块关系表
        for sector_info in sector_info_list:
            write_to_sector_info(sector_info)
            write_to_stock_sector_relationship(stock_info_least.stock_code, sector_info.sector_code)

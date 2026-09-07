from curl_cffi import requests  # 发请求（能模拟浏览器TLS指纹，过基本反爬）
import json  # 解析api返回的jsonp
import re  # 正则，提取jsonp里的json
import datetime  # 时间戳处理
import time  # 暂停，防止反爬
import traceback  # 出错时打印完整堆栈

from data_header import Stock_Info_Least, Stock_Info_History, Sector_Info, write_spider_data  # 导入数据库模型与写入函数



#股票所属板块
def get_stock_sector_list(stock_code,page_size=50):


    url = f"https://push2.eastmoney.com/api/qt/slist/get?fltt=1&invt=2&cb=jQuery351001477480648310936_1787154563964&fields=f14%2Cf12%2Cf13%2Cf3%2Cf152%2Cf4%2Cf128%2Cf140%2Cf141&secid=1.{stock_code}&ut=<anti_token>&pi=0&po=1&np=1&pz={page_size}&spt=3&wbp2u=%7C0%7C0%7C0%7Cweb&_=1787154563965"

    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0'
    }
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
        result_json=convert_response_text_to_json(response.text)
        data=result_json["data"]
        total_cnt=int(data['total'])
        if total_cnt>page_size:
            page_size=total_cnt
            return get_stock_sector_list(stock_code,page_size)
        sector_list= data['diff']
        sector_dict_list=[]
        for sector in sector_list:
            sector_dict={
                'sector_code': sector['f12'],
                'sector_name': sector['f14']
            }
            sector_dict_list.append(sector_dict)
        print(f'从属于{len(sector_dict_list)}个板块')
        return sector_dict_list



    except Exception as e:
        traceback.print_exc()
        raise Exception(f'获取所属板块列表失败，e:{e}')






def get_stock_detail(stock_code):

    #1：请求api
    import requests

    url = "https://push2.eastmoney.com/api/qt/stock/get?invt=2&fltt=1&cb=jQuery351017137207856910242_1787148835747&fields=f58%2Cf734%2Cf107%2Cf57%2Cf43%2Cf59%2Cf169%2Cf301%2Cf60%2Cf170%2Cf152%2Cf177%2Cf111%2Cf46%2Cf44%2Cf45%2Cf47%2Cf260%2Cf48%2Cf261%2Cf279%2Cf277%2Cf278%2Cf288%2Cf19%2Cf17%2Cf531%2Cf15%2Cf13%2Cf11%2Cf20%2Cf18%2Cf16%2Cf14%2Cf12%2Cf39%2Cf37%2Cf35%2Cf33%2Cf31%2Cf40%2Cf38%2Cf36%2Cf34%2Cf32%2Cf211%2Cf212%2Cf213%2Cf214%2Cf215%2Cf210%2Cf209%2Cf208%2Cf207%2Cf206%2Cf161%2Cf49%2Cf171%2Cf50%2Cf86%2Cf84%2Cf85%2Cf168%2Cf108%2Cf116%2Cf167%2Cf164%2Cf162%2Cf163%2Cf92%2Cf71%2Cf117%2Cf292%2Cf51%2Cf52%2Cf191%2Cf192%2Cf262%2Cf294%2Cf181%2Cf295%2Cf748%2Cf747%2Cf803&secid=1.688836&ut=<anti_token>&wbp2u=%7C0%7C0%7C0%7Cweb&dect=1&_=1787148835748"

    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
        'Cookie': 'qgqp_b_id=78373761385f0b5f2f2d2649d94911f5; websitepoptg_api_time=1787126872999; st_si=10717146564378; st_nvi=nIvt50bSWeRFgfrfMEwT406b7; nid18=08ec8a14ab13a7b35d51c0cbe3227d00; nid18_create_time=1787126875510; gviem=HY1ftKSPM0ZuPckslVSZnb8f5; gviem_create_time=1787126875510; fullscreengg=1; fullscreengg2=1; wsc_checkuser_ok=1; st_asi=delete; st_pvi=97756208187663; st_sp=2026-08-19%2016%3A07%3A53; st_inirUrl=https%3A%2F%2Fcn.bing.com%2F; st_sn=78; st_psi=20260819221142334-113200313000-4329784632'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)

    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
        # 2：拿出api中所需要的数据
        result_json=convert_response_text_to_json(response.text)
        '''
          "data": {
        "f43": 84500,（最新股价，/100）
        "f44": 110000,（最高股价，/100）
        "f45": 80008,（最低股价，/100）
        "f47": 256579,成交量/100单位万
        "f48": 23159535334.0,成交额：/1000单位亿
        "f57": "688836",（股票id）
        "f58": "N宇树-W",（股票名字）
        "f86": 1787127097,（时间戳）
        "f116": 341772367300.0,总市值：换成单位亿
        "f117": 25424123400.0,流通市值：	换成单位亿
        "f162": 62367,（动态市盈率，/100）
        "f163": 122847,（静态市盈率，/100）
        "f164": 58499,（滚动市盈率，/100）
        "f168": 8528,（换手率/100%）
        "f170": 46034,（交易日涨跌幅/100）
        "f288": 0,是否盈利，0为是，1为否

    }
        '''
        data=result_json['data']
        # 原始字段
        price_raw = data['f43']
        if '-'in str(price_raw):
            print(f'股票已经退市，跳过爬取，股票代码：{stock_code}')
            return None
        high_price_raw = data['f44']  # 原始最高股价，需要除以100
        low_price_raw = data['f45']  # 原始最低股价，需要除以100
        volume_raw = data['f47']  # 原始成交量，单位换算除以100，结果为万
        turnover_amount_raw = data['f48']  # 原始成交额，单位换算除以1000，结果为亿
        stock_id = data['f57']  # 股票ID
        stock_name = data['f58']  # 股票名称
        timestamp = data['f86']  # Unix时间戳
        total_market_value_raw = data['f116']  # 原始总市值，除以1亿得到亿单位
        circulate_market_value_raw = data['f117']  # 原始流通市值，除以1亿得到亿单位
        pe_dynamic_raw = data['f162']  # 原始动态市盈率，除以100
        pe_static_raw = data['f163']  # 原始静态市盈率，除以100
        pe_ttm_raw = data['f164']  # 原始滚动市盈率(TTM)，除以100
        turnover_rate_raw = data['f168']  # 原始换手率，除以100得到百分比数值
        change_rate_raw = data['f170']  # 原始交易日涨跌幅，除以100得到百分比数值
        is_profit = data['f288']  # 是否盈利：0=盈利，1=亏损

        # 3：对数据进行转换单位
        # 换算成真实业务数值
        price = price_raw / 100  # 最新股价
        high_price = high_price_raw / 100  # 最高股价
        low_price = low_price_raw / 100  # 最低股价
        volume_wan = volume_raw / 10000  # 成交量，单位：万手
        turnover_yi = turnover_amount_raw / 100000000  # 成交额，单位：亿元
        total_market_yi = total_market_value_raw / 100000000  # 总市值，单位：亿元
        circulate_market_yi = circulate_market_value_raw / 100000000  # 流通市值，单位：亿元
        pe_dynamic = pe_dynamic_raw / 100  # 动态市盈率
        pe_static = pe_static_raw / 100  # 静态市盈率
        pe_ttm = pe_ttm_raw / 100  # 滚动市盈率(TTM)
        turnover_rate_percent = turnover_rate_raw / 100  # 换手率，单位%
        change_rate_percent = change_rate_raw / 100  # 当日涨跌幅，单位%
        # 时间戳转本地时间字符串
        dt = datetime.datetime.fromtimestamp(timestamp)  # datetime对象，行情时间，用于入库时间运算
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")  # 字符串，用于打印日志
        if is_profit==0:
            is_profit='是'
        else:
            is_profit='否'

        # =====调试打印=====
        print(f'''
        【解析后业务数据】
        股票ID：{stock_id}
        股票名称：{stock_name}
        最新股价：{price}
        最高股价：{high_price}
        最低股价：{low_price}
        成交量(万手)：{volume_wan}
        成交额(亿元)：{turnover_yi}
        行情datetime对象：{dt}
        总市值(亿元)：{total_market_yi}
        流通市值(亿元)：{circulate_market_yi}
        动态市盈率：{pe_dynamic}
        静态市盈率：{pe_static}
        滚动市盈率(TTM)：{pe_ttm}
        换手率(%)：{turnover_rate_percent}
        当日涨跌幅(%)：{change_rate_percent}
        是否盈利：{is_profit}
        ''')




        # 4：获取所属板块列表
        sector_dict_list=get_stock_sector_list(stock_code)
        # 5：装成字典，返回数据
        stock_info_dict = {
            "stock_code": stock_code,
            "stock_id": stock_id,
            "stock_name": stock_name,
            "price": price,
            "high_price": high_price,
            "low_price": low_price,
            "volume_wan_hand": volume_wan,  # 万手
            "turnover_yi": turnover_yi,  # 亿元
            "total_market_yi": total_market_yi,  # 总市值亿元
            "circulate_market_yi": circulate_market_yi,  # 流通市值亿元
            "pe_dynamic": pe_dynamic,
            "pe_static": pe_static,
            "pe_ttm": pe_ttm,
            "turnover_rate_percent": turnover_rate_percent,
            "change_rate_percent": change_rate_percent,
            "is_profit": is_profit,
            "quote_datetime": dt,
            "quote_datetime_str": dt_str,
            "sector_list": sector_dict_list
        }

        return stock_info_dict





    except Exception as e:
        raise Exception(f'获取个股详情失败：error{e}')





def convert_response_text_to_json(response_text):
    #print(f'{response_text=}')
    json_text = re.search(r'\((.*)\)\s*;?\s*$', response_text, flags=re.S).group(1)
    #json_text = re.search(r'jQuery.*?\((\{.*\})\)', response_text).group(1)
    result_json=json.loads(json_text)
    #print(f'{result_json=}')
    return result_json


def get_stock_list(market_tpye,page_num):
    print(f"请求页码：{page_num}")
    #1:请求列表api

    url = f"https://pushguest.eastmoney.com/api/qt/clist/get?timil=1&np=1&fltt=1&invt=2&cb=jQuery371010638135809202687_1787131015272&fs={market_tpye}&fields=f12,f13,f14,f1,f2,f4,f3,f152,f5,f6,f7,f15,f18,f16,f17,f10,f8,f9,f23&fid=f3&pn={page_num}&pz=20&po=1&dect=1&ut=<anti_token>&wbp2u=|0|0|0|web&_=1787131015280"

    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0'
    }

    try:

        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()

        # 2：从返回结果里面，提取股票总数，和股票列表
        result_json=convert_response_text_to_json(response.text)
        data=result_json['data']
        stock_cnt=data['total']
        stock_list=data['diff']
        stock_code_list=[]
        for stock in stock_list:
            stock_code_list.append(stock['f12'])


        # 3：将结果放到一个字典返回
        stock_list_dict = {
            'stock_cnt': stock_cnt,
            'stock_code_list': stock_code_list

        }
        #print(f'{stock_list_dict=}')
        return stock_list_dict

    except Exception as e:
        traceback.print_exc()
        raise Exception(f'获取股票列表失败，e:{e}')











def spider_stock_data(marker_type):
    try:
        #1：请求股票列表接口，获得股票总数
        stock_list_dict=get_stock_list(marker_type,1)
        stock_cnt=stock_list_dict['stock_cnt']
        print(f'{stock_cnt=}')

        #2：根据总数实现分页循环
        page_size = 20
        for start in range(0, stock_cnt, page_size):
            pagee_num = (start // page_size) + 1
            # #TODO:测试时只测试一页
            # if pagee_num > 1:
            #     break


            #3：在这个循环里面，请求股票列表接口，获取股票列表

            stock_list_dict = get_stock_list(marker_type, pagee_num)
            stock_code_list = stock_list_dict['stock_code_list']


            #4：循环这个股票列表，得到详情页的url，
            for stock_code in stock_code_list:
                print(f'获取个股详情：{stock_code}')
                stock_info_dict=get_stock_detail(stock_code)
                if stock_info_dict is None:
                    continue
                # =========所有数据全部拿到之后，再构造模型实例==========
                stock_info_least = Stock_Info_Least.get_instance(stock_info_dict)
                stock_info_history = Stock_Info_History.get_instance(stock_info_dict)
                # 遍历所属板块字典，构造板块模型实例列表
                sector_info_list = []
                for sector_dict in stock_info_dict.get('sector_list', []):
                    sector_info_list.append(Sector_Info.get_instance(sector_dict))
                # ==========写入数据库（一只股票入库失败不影响后续）==========
                try:
                    write_spider_data(stock_info_least, stock_info_history, sector_info_list)
                except Exception as e:
                    print(f'写入数据库失败，跳过该股票：{stock_code=}, {e}')
                    traceback.print_exc()
                time.sleep(1)  # 改为1秒一次，防止触发东方财富限流
                print(f' ')






    except Exception as e:
        print(e)
        traceback.print_exc()



if __name__ == '__main__':
    spider_stock_data('m:1+t:2+f:!2,m:1+t:23+f:!2')
    #get_stock_detail(688836)
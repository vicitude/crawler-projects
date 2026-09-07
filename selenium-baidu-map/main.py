from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
import random
import time

from selenium.webdriver.common.by import By #按什么方式找元素
from selenium.webdriver.support.ui import WebDriverWait #显示等待类
from selenium.webdriver.support import expected_conditions as EC# #常用等待条件模块

from PIL import Image #用于图像处理
from io import BytesIO #把图片转换为二进制字节流
from curl_cffi import requests #请求图片
import os #处理文件

import cv2

from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.chrome.options import Options


#把字符串清洗成合法的文件名/目录名（替换掉 Windows 禁用的字符）
def sanitize_filename(name):
    # Windows 文件名禁用字符: \ / : * ? " < > | 以及方括号 [ ]
    illegal_chars = r'\/:*?"<>|[]'
    for ch in illegal_chars:
        name = name.replace(ch, '_')
    return name


#截图路线地图
def screenshot_line(scheme_name):
    mask_element=driver.find_element(By.ID,'mask')
    map_img_bytes=mask_element.screenshot_as_png
    safe_start = sanitize_filename(start)
    safe_end = sanitize_filename(end)
    img_file_dir=f'map_images/{safe_start}--{safe_end}'
    if not os.path.exists(img_file_dir):
        os.makedirs(img_file_dir)
        print(f'已创建图片目录{img_file_dir}')
    image_obj=Image.open(BytesIO(map_img_bytes))
    safe_scheme_name = sanitize_filename(scheme_name)
    image_file_path=f'{img_file_dir}/{safe_scheme_name}.png'
    image_obj.save(image_file_path)






#解析路线详情信息
def parse_route_detail(route_list_element):
    """
    详情列表：
位于 class="info‑table" 的 table 标签下面的 tr 标签，每个 tr 标签的 data‑type 表示步行或者公交 / 地铁。
tr class data-type="bus"
tr class data-type="walk"


步行：
<td class="transferDetail">
      <p class="walkdisinfo">步行&nbsp;
      <a class="cs">10米</a>
      </p>
  </td>

BUS：
    <!-- ①上车点 -->
    <div class="getonstop">
        <a class="ks">农林大学</a>站 &nbsp;上车
    </div>

     <!-- ②线路名、方向、站数 -->
    <span class="kl">
        <span class="line-name">地铁16号线</span>
        <span class="l‑grey direction">（绿汀路方向）</span>
        <a class="cs tf">9站</a>
    </span>


    <!-- ③下车点 -->
    <div class="getoffstop">
        <a class="ks">绿汀路</a>站 下车&nbsp;&nbsp;
        <span>（D2口出）</span>
    </div>


沿途站点数
class =cs tf

    """
    route_list_element.click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'table.info-table'))
    )
    table_element=route_list_element.find_element(By.CLASS_NAME,'info-table')
    tr_elements=table_element.find_elements(By.TAG_NAME,'tr')
    print(f'以下是路线的分段路径')
    for tr_element in tr_elements:
        data_type=tr_element.get_attribute('data-type')
        transfer_detail_element=tr_element.find_element(By.CLASS_NAME,'transferDetail')
        if data_type.strip()=='walk':
            walk_distance_element=transfer_detail_element.find_element(By.CLASS_NAME,'cs')
            walk_distance=walk_distance_element.text
            print(f'分段类型：{data_type},距离{walk_distance}')
        elif data_type.strip()=='bus':
            getonstop_element=transfer_detail_element.find_element(By.CLASS_NAME,'getonstop')
            start_station=getonstop_element.text
            getoffstop_element = transfer_detail_element.find_element(By.CLASS_NAME, 'getoffstop')
            end_station=getoffstop_element.text
            kl_element=transfer_detail_element.find_element(By.CLASS_NAME,'kl')
            line_name_element=kl_element.find_element(By.CLASS_NAME,'line-name')
            line_name=line_name_element.text

            line_direction='无方向信息'
            try:
                line_direction_element=kl_element.find_element(By.CSS_SELECTOR,'.l‑grey.direction')
                line_direction=line_direction_element.text
            except NoSuchElementException:
                pass

            line_via_station_cnt_element=kl_element.find_element(By.CSS_SELECTOR,'.cs.tf')
            line_via_station_cnt=line_via_station_cnt_element.text
            print(f"分段类型:{data_type}, 线路名:{line_name}, 上车站点:{start_station}, 下车站点:{end_station}")
            print(f"线路始末站:{line_direction}, 途经站点数:{line_via_station_cnt}")
        else:
            print(f'未知{data_type=}')






#解析路线的基本信息
def parse_route_basic(route_list_element):
    """
    票价到步行距离之间的数据都在：
class=route-head
这个里面


票价：
<span class="schemePrice">
    <font>票价<span class="yuanStance">¥</span>10</font>
</span>

路线标签：最佳，最快，直达之类的
<span class="schemeTag" style="background: #67C395">
    <font color="#ffffff">最佳</font>
</span>


耗时：
<span class="bus_time">1小时31分钟</span>

公共交通距离：这里记得用blDis_来模糊检索
<span id="blDis_0">44.0公里</span>

步行距离：
class=route-head
里面的最后一个span

    """
    route_head_element=route_list_element.find_element(By.CLASS_NAME, "route-head")

    # 票价不是每条路线都有（比如某些路线显示"参考票价"或干脆没票价），加 try/except
    scheme_price='无'
    try:
        scheme_price_element=route_head_element.find_element(By.CLASS_NAME, "schemePrice")
        scheme_price=scheme_price_element.text
    except Exception:
        pass

    scheme_tag='无'
    try:
        scheme_tag_element=route_head_element.find_element(By.CLASS_NAME, "schemeTag")
        scheme_tag=scheme_tag_element.text
    except Exception:
        pass

    #路线名称
    scheme_name_element=route_head_element.find_element(By.CLASS_NAME, "schemeName")
    scheme_name_text=scheme_name_element.text
    scheme_name_text=scheme_name_text.replace(" → ","→")
    scheme_name_text_list=scheme_name_text.split(' ')
    scheme_name=scheme_name_text_list[-1]

    bus_time_element = route_head_element.find_element(By.CLASS_NAME, "bus_time")
    total_time = bus_time_element.text

    bl_dis_element=route_head_element.find_element(By.XPATH,'//span[contains(@id,"blDis_")]')
    total_distance=bl_dis_element.text

    span_elements=route_head_element.find_elements(By.TAG_NAME,"span")
    walk_distance_element=span_elements[-1]
    walk_distance=walk_distance_element.text

    # ========== 新增打印输出 ==========
    print("-" * 60)
    print(f"票价: {scheme_price}")
    print(f"路线标签: {scheme_tag}")
    print(f"路线名称: {scheme_name}")
    print(f"总耗时: {total_time}")
    print(f"公共交通总距离: {total_distance}")
    print(f"步行距离: {walk_distance}")
    print("-" * 60)

    return scheme_name




#解析路线列表
def parse_route_list():
    wait=WebDriverWait(driver,10)
    route_list_element=wait.until(
        EC.visibility_of_element_located((By.ID,'route_list'))
    )
    route_list_elements=route_list_element.find_elements(By.TAG_NAME,'li')
    print(f'找到{len(route_list_elements)}条路线')

    for route_list_element in route_list_elements:
        #解析路线基本信息
        scheme_name= parse_route_basic(route_list_element)
        #解析路线详细信息
        parse_route_detail(route_list_element)
        #路线截图
        screenshot_line(scheme_name)
        print(f'  ')




#随机等待时间
def random_delay(min_delay=1.0, max_delay=3.0):
    time.sleep(random.uniform(min_delay, max_delay))

#模仿人输入
def slow_input(element,input_str):
    for c in input_str:
        element.send_keys(c)
        random_delay(0.01,0.07)
    random_delay()



#输入起点和终点
def input_start_and_end(start,end):
    start_input=driver.find_element(By.CLASS_NAME,'route-start-input')
    end_input=driver.find_element(By.CLASS_NAME,'route-end-input')
    slow_input(start_input,start)
    time.sleep(0.5)
    slow_input(end_input,end)


#点击搜索按钮

def click_search_button():
    search_button=driver.find_element(By.ID,"search-button")
    search_button.click()
    time.sleep(2)



#展开路线查询输入框
def show_search_box():
    route_button=driver.find_element(By.XPATH,"//div[@data-title='路线']")
    route_button.click()
    time.sleep(1)


#点击公共交通按钮
def click_bus_button():
    bus_button=driver.find_element(By.XPATH,"//div[@data-index='bus']")
    bus_button.click()
    time.sleep(1)

#点击驾车按钮
def click_drive_button():
    drive_button=driver.find_element(By.XPATH,"//div[@data-index='drive']")
    drive_button.click()
    time.sleep(1)




if __name__ == '__main__':
    service = Service(r"D:\SeleniumChromeDrive\chromedriver.exe")

    # 配置 Chrome，使用固定的 user-data-dir
    # 首次运行需手动授权位置/登录等，后续自动保留这些状态
    chrome_options = Options()
    chrome_options.add_argument(
        r"user-data-dir=D:\python\Program\scrape\third_week\map_baidu\SeleniumChrome_map_baidu"
    )
    # 禁用自动化提示（避免被反爬识别为自动化脚本）
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)



    driver = webdriver.Chrome(service=service, options=chrome_options)
    #driver = webdriver.Edge()


    url='https://map.baidu.com'
    driver.maximize_window()
    driver.get(url)

    # 展开路线查询输入框
    show_search_box()
    start = "农林大学-地铁站"
    end = '灵隐寺'
    input_start_and_end(start, end)

    #先点驾车按钮
    click_drive_button()
    #点击搜索按钮
    click_search_button()
    # 点击公共交通，切换公共交通
    click_bus_button()
    time.sleep(2.5)


    #解析路线列表
    parse_route_list()

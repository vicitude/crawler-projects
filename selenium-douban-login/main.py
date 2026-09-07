from selenium import webdriver
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


#检查登录状态
def check_login_status():
    time.sleep(3)
    driver.switch_to.default_content()
    login_div_is_visible = element_is_visible(By.CLASS_NAME,'login')
    if not login_div_is_visible:
        print(f'登陆成功')
    else:
        switch_to_login_iframe()
        captcha_iframe_is_visible = element_is_visible(By.ID,'tcaptcha_iframe_dy')
        if not captcha_iframe_is_visible:
            print(f'登陆失败，账号或者密码错误')
        else:
            print(f'登录失败，滑块验证未通过')
            login()




#判断元素是否可见
def element_is_visible(locator_type, locator_value):
    try:
        WebDriverWait(driver,1).until(
            EC.visibility_of_element_located((locator_type , locator_value))   # 1 个元组参数 → 正确
        )
        return True
    except Exception as e:
        print(f'出现异常：{e}')
        return False




#拖动拼图块
def drag_puzzle_piece(puzzle_piece_element,move_distance):
    actions=ActionChains(driver)
    actions.click_and_hold(puzzle_piece_element).perform()

    fast_move_distance=move_distance/4*3
    slow_move_distance=move_distance-fast_move_distance

    drag_slowly(3,fast_move_distance,actions)
    drag_slowly(6,slow_move_distance,actions)

    drag_slowly(3,12,actions)
    drag_slowly(5,-13,actions)

    actions.release().perform()


#缓慢拖拽
def drag_slowly(count,total_distance,actions):
    segment_distance = total_distance/count
    for i in range(count):
        actions.move_by_offset(segment_distance,0).perform()
        random_delay(0.01,0.03)


#得到网页上的拼图块最终移动距离
def get_move_distance(background_img_path,gap_source_pos_x,puzzle_piece_element,background_element):
    source_distance=gap_source_pos_x

    background_img_obj=Image.open(background_img_path)
    background_img_width=background_img_obj.size[0]

    background_img_web_img=get_float_value_from_css_property(background_element,'width')
    scale_width=background_img_web_img/background_img_width

    web_distance=source_distance*scale_width
    left_distance=get_float_value_from_css_property(puzzle_piece_element,'left')
    final_distance=web_distance-left_distance
    print(f'网页上的拼图块最终移动距离为: {final_distance}')
    return final_distance




def get_gap_position(background_img_path,puzzle_piece_img_path):
    background_img = preprocess_from_match(cv2.imread(background_img_path))
    puzzle_piece_img=preprocess_from_match(cv2.imread(puzzle_piece_img_path))
    result=cv2.matchTemplate(background_img,puzzle_piece_img,cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print(f'缺口坐标的匹配率={max_val}')
    print(f'缺口的左上角坐标={max_loc}')
    return max_loc


#对图像进行模糊，及边缘检测预处理
def preprocess_from_match(img):
    blur=cv2.GaussianBlur(img,(3,3),0)
    edge=cv2.Canny(blur,100,200)
    return edge




#截取和存储拼图块图片到本地，拼图块元素，保存图片的文件夹路径，完整图的文件名，截图完完整的拼图块文件名
def process_and_save_slider_image(puzzle_piece_element,image_dir_path,full_img_name,puzzle_piece_img_name):
    full_img_path = os.path.join(image_dir_path,full_img_name)
    puzzle_piece_img_path = os.path.join(image_dir_path,puzzle_piece_img_name)

    style_values=get_puzzle_piece_stype_values(puzzle_piece_element)
    puzzle_piece_img_source_dict=get_puzzle_piece_img_source_pos_from_style(style_values,full_img_path)
    puzzle_piece_img_source_pos=puzzle_piece_img_source_dict['puzzle_piece_img_source_pos']
    puzzle_piece_img_source_size=puzzle_piece_img_source_dict['puzzle_piece_img_source_size']

    puzzle_piece_img_obj=extract_puzzle_piece_image(puzzle_piece_img_source_pos,puzzle_piece_img_source_size,full_img_path)
    puzzle_piece_img_obj.save(puzzle_piece_img_path)
    print(f'拼图块截取成功')




#从完整图片中截取拼图块区域并返回图片对象
def extract_puzzle_piece_image(puzzle_piece_img_pos,puzzle_piece_img_size,source_img_path):
    pos_x_start,pos_y_start =puzzle_piece_img_pos
    pos_x_start=abs(pos_x_start)
    pos_y_start=abs(pos_y_start)

    width,height=puzzle_piece_img_size
    pos_x_end=pos_x_start+width
    pos_y_end=pos_y_start+height
    print(f'截取坐标：起始x={pos_x_start},起始y={pos_y_start},结束x={pos_x_end}，结束y={pos_y_end}')

    source_img_obj=Image.open(source_img_path)
    puzzle_piece_img_obj=source_img_obj.crop((pos_x_start,pos_y_start,pos_x_end,pos_y_end))
    return puzzle_piece_img_obj




#根据网页样式值和图片路径，计算拼图块在原始完整图片中的位置和尺寸
def get_puzzle_piece_img_source_pos_from_style(style_values,slider_full_img_path):
    full_img_web_pos_x,full_img_web_pos_y =style_values["full_img_web_pos"]
    print(f'拼图块在网页上的坐标：x={full_img_web_pos_x}，y={full_img_web_pos_y}')
    full_img_web_width, full_img_web_height = style_values["full_img_web_size"]
    print(f'完整图在网页上的大小：宽={full_img_web_width}，长={full_img_web_height}')

    slider_full_img_path =Image.open(slider_full_img_path)
    full_img_source_width,full_img_source_height = slider_full_img_path.size
    print(f'完整原图的原始大小：宽={full_img_source_width}，长={full_img_source_height}')

    scale_width=full_img_web_width/full_img_source_width
    scale_height=full_img_web_height/full_img_source_height

    puzzle_piece_img_source_pos_x= full_img_web_pos_x/scale_width
    puzzle_piece_img_source_pos_y= full_img_web_pos_y/scale_height
    print(f'拼图在原图的坐标：x={puzzle_piece_img_source_pos_x},y={puzzle_piece_img_source_pos_y}')

    puzzle_piece_img_source_width=style_values["puzzle_piece_img_web_width"]/scale_width
    puzzle_piece_img_source_height=style_values["puzzle_piece_img_web_height"]/scale_height
    print(f'拼图块的原始大小：宽={puzzle_piece_img_source_width}，长={puzzle_piece_img_source_height}')

    return{
        "puzzle_piece_img_source_pos":(puzzle_piece_img_source_pos_x,puzzle_piece_img_source_pos_y),#拼图块在原图的坐标
        "puzzle_piece_img_source_size":(puzzle_piece_img_source_width,puzzle_piece_img_source_height),#拼图块在原图的尺寸
    }




#提取拼图块的background-position，background-size，width，height浮点数值
def get_puzzle_piece_stype_values(element):
    full_img_web_pos=get_float_value_from_css_property(element,'background-position')
    full_img_web_size = get_float_value_from_css_property(element, 'background-size')
    puzzle_piece_img_web_width =get_float_value_from_css_property(element,'width')
    puzzle_piece_img_web_height =get_float_value_from_css_property(element,'height')

    # 组装返回字典
    style_values = {
        "full_img_web_pos": full_img_web_pos,
        "full_img_web_size": full_img_web_size,
        "puzzle_piece_img_web_width": puzzle_piece_img_web_width,
        "puzzle_piece_img_web_height": puzzle_piece_img_web_height
    }

    return style_values


#提取 background-position，background-size，width，height浮点数值
def get_float_value_from_css_property(element,property_name):
    value_str=element.value_of_css_property(property_name)
    value_str_no_px=value_str.replace('px','')
    if property_name=='background-position' or property_name=='background-size':
        value_list=value_str_no_px.split(' ')
        return float(value_list[0]),float(value_list[1])
    else:
        return float(value_str_no_px)




#保存元素背景图为图片文件
def save_element_image(element,save_dir,file_name):
    if element is None:
        print("没找到拼图元素,跳过保存")
        return
    img_url=get_bg_img_url_from_element(element)
    print(f'{file_name}的URL为{img_url}')
    img_obj=get_image_obj_by_url(img_url)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f'创建了图片目录：{save_dir}')
    save_path=os.path.join(save_dir, file_name)
    img_obj.save(save_path)
    print(f'图片下载成功：{file_name}')


#从url里面获取图片对象,十分通用的函数
def get_image_obj_by_url(img_url):
    response = requests.get(img_url)
    byte_img=BytesIO(response.content)
    img_obj=Image.open(byte_img)
    return img_obj




#从元素对象中获取style里面的background-image的url
def get_bg_img_url_from_element(element):
    bg_img_value=element.value_of_css_property('background-image')
    img_url=bg_img_value.replace('url("','').replace('")','')
    return img_url





#查找图块元素
def get_puzzle_piece_element():
    elements= wait_all_elements_visibility(By.CLASS_NAME,"tc-fg-item")
    for element in elements:
        cursor=element.value_of_css_property("cursor")#一般是代表能不能拖动
        z_index=element.value_of_css_property("z-index")#这个玩意越大的越在图层的上方
        if z_index=='1' and cursor=='pointer':
            print(f'成功找到拼图元素')
            return element




#切换到验证码的iframe
def switch_to_captcha_iframe():
    iframe_element = wait_element_visibility(By.ID,'tcaptcha_iframe_dy')
    driver.switch_to.frame(iframe_element)


########################################################################################################
#移动拼图块
def handle_slider_captcha():
    #1.切换到验证码的iframe
    switch_to_captcha_iframe()
    #2.查找拼图块元素对象
    puzzle_piece_element=get_puzzle_piece_element()
    #3.下载带缺口的背景图
    image_dir_path="./slider_images"
    background_img_name="background_image.png"
    full_img_name="slider_full_image.png"
    puzzle_piece_image_name="puzzle_piece_image.png"


    background_element = wait_element_visibility(By.ID,'slideBg')
    save_element_image(background_element,image_dir_path,background_img_name)
    #4.下载包含拼图块的完整图

    save_element_image(puzzle_piece_element, image_dir_path, full_img_name)

    #5.截取拼图块图片
    process_and_save_slider_image(
        puzzle_piece_element,
        image_dir_path,
        full_img_name,
        puzzle_piece_image_name

    )
    #6.比较拼图块与带缺口的背景图，计算移动距离
    gap_source_pos_x=get_gap_position(
        os.path.join(image_dir_path,background_img_name),
        os.path.join(image_dir_path,puzzle_piece_image_name)

    )[0]
    move_distance=get_move_distance(
        os.path.join(image_dir_path, background_img_name),
        gap_source_pos_x,
        puzzle_piece_element,
        background_element
    )

    #7.拖拽拼图块移动指定距离
    drag_puzzle_piece(puzzle_piece_element,move_distance)
    random_delay()

########################################################################################################

#输入账号密码，并点击登录
def submit_username_and_password(username,password):
    account_element=wait_element_visibility(By.NAME,'username')
    slow_input(account_element,username)
    password_element=wait_element_visibility(By.NAME, 'password')
    slow_input(password_element,password)

    login_button_element = wait_element_visibility(By.CSS_SELECTOR, '.btn.btn-account')
    login_button_element.click()


#模仿人输入
def slow_input(element,input_str):
    for c in input_str:
        element.send_keys(c)
        random_delay(0.01,0.07)
    random_delay()




#切换到密码登录选项卡
def switch_to_account_login():
    switch_to_login_iframe()
    account_element=wait_element_visibility(By.CLASS_NAME,'account-tab-account')
    account_element.click()




#切换到登陆页所在的iframe
def switch_to_login_iframe():
    iframe_element=wait_element_visibility(By.XPATH, "//div[@class='login']/iframe[1]")
    driver.switch_to.frame(iframe_element)



#显示要等待的单个元素,然后返回这个元素
def wait_element_visibility(locator_type,locator_value):
    element=wait.until(
        EC.visibility_of_element_located((locator_type , locator_value))
    )
    return element


#显示要等待的一组元素
def wait_all_elements_visibility(locator_type, locator_value):
    elements = wait.until(
        EC.visibility_of_all_elements_located((locator_type, locator_value))
    )
    return elements

#随机等待时间
def random_delay(min_delay=1.0, max_delay=3.0):
    time.sleep(random.uniform(min_delay, max_delay))



########################################################################################################

def login():
    #第一步，访问豆瓣首页
    driver.maximize_window()
    driver.get(url)
    random_delay()
    #补充一步，判断是否已经登录
    if element_is_visible(By.CLASS_NAME,'nav-user-account'):
        print(f'已经处于登录状态')
        time.sleep(5)
        return

    #第二步，切换到'密码登陆'选项卡
    switch_to_account_login()
    random_delay()
    #第三步，输入用户名和密码，点击登陆
    submit_username_and_password('13507526989','Hjw1234567890')
    random_delay(5,6)

    #第四步，处理滑块验证码
    handle_slider_captcha()


    #第五步，判断验证是否成功
    check_login_status()
    random_delay(5.0,6.0)
########################################################################################################


if __name__ == '__main__':
    service = Service(r"D:\SeleniumChromeDrive\chromedriver.exe")
    chrome_options=Options()
    chrome_options.add_argument("--user-data-dir=D:/python/Program/scrape/third_week/SeleniumChrome_douban")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)
    url='https://www.douban.com'
    login()

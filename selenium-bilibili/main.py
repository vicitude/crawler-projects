from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import time
import random
import re


# ============ 字符串清洗（用作控制台正常字符串，非文件名，按参考报告规范保留一份保险） ============
def sanitize_filename(name):
    """替换 Windows 禁用的文件名字符（当前没用到，但保留防止后续保存截图 / 落盘时踩坑）"""
    illegal_chars = r'\/:*?"<>|[]'
    for ch in illegal_chars:
        name = name.replace(ch, '_')
    return name


# ============ 随机等待 / 慢速输入（反爬对抗基础配置） ============
def random_delay(min_delay=1.0, max_delay=3.0):
    time.sleep(random.uniform(min_delay, max_delay))


def slow_input(element, input_str):
    for c in input_str:
        element.send_keys(c)
        random_delay(0.01, 0.07)
    random_delay()


# ============ 单个代表作卡片解析 ============
def parse_masterpiece_card(card_element):
    """
    从一个代表作卡片 (div.masterpiece-block__item) 解析出:
        title / play_count / danmu_count / duration
    字段缺失时默认 '无'
    """
    # ----- 标题 -----
    title = '无'
    try:
        title_element = card_element.find_element(By.CSS_SELECTOR, '.bili-video-card__title a')
        # 优先取 title 属性（更精确），取不到再 fallback 到文本
        title = title_element.get_attribute('title') or title_element.text or '无'
        title = title.strip() or '无'
    except Exception:
        pass

    # ----- 播放次数 -----
    # 每个 .bili-cover-card__stat 里要么含 <i class="sic-BDC-playdata_square_line">
    # 要么含 <i class="sic-BDC-danmu_square_line">，要么只含一个 span（时长）。
    # 因此按 stat 索引拿值更稳。
    play_count = '无'
    danmu_count = '无'
    duration = '无'

    try:
        stat_elements = card_element.find_elements(By.CSS_SELECTOR, '.bili-cover-card__stat')
        for stat in stat_elements:
            span_text = ''
            try:
                span_text = stat.find_element(By.TAG_NAME, 'span').text.strip()
            except Exception:
                pass

            html = stat.get_attribute('class') or ''
            # 看 class 里有没有对应的图标类（应对有些 stat 结构只挂 i 的情况）
            inner_html = stat.get_attribute('innerHTML') or ''

            if 'sic-BDC-playdata_square_line' in inner_html:
                play_count = span_text or '无'
            elif 'sic-BDC-danmu_square_line' in inner_html:
                danmu_count = span_text or '无'
            else:
                # 该 stat 里只有 span，没有 i 图标 → 视为时长
                # 时长形如 "03:16:57" / "10:28"
                if re.fullmatch(r'\d{1,3}:\d{2}(:\d{2})?', span_text):
                    duration = span_text
                # 兜底：如果还无时长，取最后一组 stat 的 span（通常时长在最后）
                elif duration == '无':
                    pass
    except Exception:
        pass

    # 兜底：循环结束时如果 duration 还是无，再按"最后一个 stat 的 span"规则补一次
    if duration == '无':
        try:
            stat_elements = card_element.find_elements(By.CSS_SELECTOR, '.bili-cover-card__stat')
            if stat_elements:
                last_span = stat_elements[-1].find_element(By.TAG_NAME, 'span')
                candidate = last_span.text.strip()
                if re.fullmatch(r'\d{1,3}:\d{2}(:\d{2})?', candidate):
                    duration = candidate
        except Exception:
            pass

    return {
        'title': title,
        'play_count': play_count,
        'danmu_count': danmu_count,
        'duration': duration,
    }


# ============ 主流程：定位代表作模块并解析所有卡片 ============
def parse_masterpiece_block(driver):
    # 1. 等代表作容器出现（异步加载）
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.masterpiece-block__item'))
        )
    except Exception:
        print('未找到「代表作」模块，可能是该 UP 主未设置代表作或页面异步加载失败。')
        return []

    # 2. 多取一次以保证所有卡片插入完
    random_delay(0.5, 1.2)
    card_elements = driver.find_elements(By.CSS_SELECTOR, '.masterpiece-block__item')

    results = []
    print(f'共有 {len(card_elements)} 个代表作\n')

    for card in card_elements:
        info = parse_masterpiece_card(card)
        results.append(info)
        # 按要求的输出格式打印
        print(f"标题：{info['title']}")
        print(f"播放次数：{info['play_count']}")
        print(f"弹幕数：{info['danmu_count']}")
        print(f"视频总时长：{info['duration']}")
        print()

    return results


# ============ 入口 ============
if __name__ == '__main__':
    # chromedriver 路径，按本地实际位置修改
    service = Service(r"D:\SeleniumChromeDrive\chromedriver.exe")

    # Chrome 配置：固定 user-data-dir，避免每次弹授权 / 验证
    chrome_options = Options()
    chrome_options.add_argument(
        r"user-data-dir=D:\python\Program\scrape\third_week\bilibili_selenium\SeleniumChrome_bilibili"
    )
    # 去掉"正受到自动测试软件控制"提示，降低被反爬识别的概率
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.maximize_window()

    # 目标 UP 主主页
    up_url = 'https://space.bilibili.com/131584320?spm_id_from=333.1007.tianma.2-3-6.click'
    try:
        driver.get(up_url)
    except Exception as e:
        print(f'打开主页失败：{e}')
        driver.quit()
        raise SystemExit(1)

    # 等待作品区域出现，模拟人浏览节奏
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#page-index, .masterpiece-block, .i-pin-v2')
            )
        )
    except Exception:
        pass

    random_delay(2.0, 3.0)



    # 滚到代表作模块，触发懒加载
    try:
        masterpiece_section = driver.find_element(By.CSS_SELECTOR, '.masterpiece-block')
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
                              masterpiece_section)
        random_delay(1.0, 2.0)
    except Exception:
        # 找不到就直接滑到中段
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        random_delay(1.0, 2.0)

    # 解析代表作
    parse_masterpiece_block(driver)




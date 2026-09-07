"""读取哔哩哔哩 UP 主公开主页中的代表作信息。"""

import argparse
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def parse_card(card) -> dict[str, str]:
    result = {"title": "无", "play_count": "无", "danmu_count": "无", "duration": "无"}

    try:
        title = card.find_element(By.CSS_SELECTOR, ".bili-video-card__title a")
        result["title"] = (title.get_attribute("title") or title.text or "无").strip()
    except Exception:
        pass

    for stat in card.find_elements(By.CSS_SELECTOR, ".bili-cover-card__stat"):
        text = stat.text.strip()
        html = stat.get_attribute("innerHTML") or ""
        if "playdata" in html:
            result["play_count"] = text or "无"
        elif "danmu" in html:
            result["danmu_count"] = text or "无"
        elif re.fullmatch(r"\d{1,3}:\d{2}(:\d{2})?", text):
            result["duration"] = text

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "url",
        nargs="?",
        default="https://space.bilibili.com/131584320",
        help="公开的哔哩哔哩 UP 主主页地址",
    )
    args = parser.parse_args()

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(args.url)
        driver.maximize_window()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2)")

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".masterpiece-block__item")))
        except Exception:
            print("未找到代表作模块，页面结构可能已经变化或该 UP 主未设置代表作。")
            return

        cards = driver.find_elements(By.CSS_SELECTOR, ".masterpiece-block__item")
        print(f"找到 {len(cards)} 个代表作")
        for index, card in enumerate(cards, start=1):
            item = parse_card(card)
            print(
                f"{index}. {item['title']} | 播放：{item['play_count']} | "
                f"弹幕：{item['danmu_count']} | 时长：{item['duration']}"
            )
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

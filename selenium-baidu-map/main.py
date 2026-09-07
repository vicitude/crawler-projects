"""使用 Selenium 查询百度地图公交路线并保存页面截图。"""

import argparse
import re
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def safe_name(value: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", value).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("start", nargs="?", default="农林大学-地铁站")
    parser.add_argument("end", nargs="?", default="灵隐寺")
    args = parser.parse_args()

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://map.baidu.com/")
        driver.maximize_window()

        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@data-title='路线']"))).click()
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "route-start-input"))).send_keys(args.start)
        driver.find_element(By.CLASS_NAME, "route-end-input").send_keys(args.end)
        driver.find_element(By.ID, "search-button").click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@data-index='bus']"))).click()

        route_list = wait.until(EC.visibility_of_element_located((By.ID, "route_list")))
        routes = route_list.find_elements(By.TAG_NAME, "li")
        print(f"找到 {len(routes)} 条公交路线")

        for index, route in enumerate(routes, start=1):
            text = " ".join(route.text.split())
            if text:
                print(f"{index}. {text}")

        output_dir = Path("map_images")
        output_dir.mkdir(exist_ok=True)
        output = output_dir / f"{safe_name(args.start)}--{safe_name(args.end)}.png"
        driver.save_screenshot(str(output))
        print(f"截图已保存：{output}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

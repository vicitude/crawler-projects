"""豆瓣 Selenium 登录演示。

账号和密码仅从环境变量读取；出现验证码时由用户本人手动完成。
本项目不会识别、破解或自动拖动验证码。
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def main() -> None:
    username = os.getenv("DOUBAN_USERNAME")
    password = os.getenv("DOUBAN_PASSWORD")

    options = webdriver.ChromeOptions()
    profile_dir = os.getenv("DOUBAN_PROFILE_DIR")
    if profile_dir:
        options.add_argument(f"--user-data-dir={profile_dir}")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.douban.com/")
        driver.maximize_window()

        if username and password:
            login_frame = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".login iframe"))
            )
            driver.switch_to.frame(login_frame)
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "account-tab-account"))).click()
            wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(username)
            wait.until(EC.visibility_of_element_located((By.NAME, "password"))).send_keys(password)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-account"))).click()
            driver.switch_to.default_content()
            print("已提交登录信息。如出现验证码，请在浏览器中手动完成。")
        else:
            print("未设置 DOUBAN_USERNAME/DOUBAN_PASSWORD，请在浏览器中手动登录。")

        input("完成登录检查后按 Enter 关闭浏览器：")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

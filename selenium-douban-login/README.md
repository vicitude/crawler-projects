# 豆瓣滑块验证码自动化登录

Selenium 自动登录豆瓣，演示腾讯防水墙（拼图滑块验证码）的识别与拖动流程：
访问豆瓣首页 → 切换到密码登录 iframe → 输入账号密码 → 识别拼图缺口 → 模拟人手轨迹拖动拼图块 → 通过验证码。

## 使用方法

```powershell
python -m pip install -r requirements.txt
python main.py
```

脚本里写死了账号、密码、ChromeDriver 路径与用户数据目录位置，使用前请自行修改 `main.py` 末尾的：

- `service = Service(r"D:\SeleniumChromeDrive\chromedriver.exe")`  ← 你的 chromedriver 路径
- `--user-data-dir=.../SeleniumChrome_douban`                    ← 持久化 Chrome 用户目录
- `submit_username_and_password('账号', '密码')`                   ← 你的账号密码

## 目录说明

- `main.py`：完整脚本（含滑块 7 步流程）。
- `requirements.txt`：依赖列表。
- 运行后会在当前目录生成 `./slider_images/`（背景图、完整图、拼图块原图）。

## 滑块验证码 7 步流程

1. 切换到验证码 iframe（`tcaptcha_iframe_dy`）。
2. 找到拼图块元素（`cursor=pointer` 且 `z-index=1`）。
3. 下载带缺口的背景图（`#slideBg`）。
4. 下载完整图（含拼图块的原图）。
5. 从完整图里按 `background-position` + `background-size` 算出缩放比，裁出拼图块。
6. 用 OpenCV `matchTemplate` 在带缺口背景图上找缺口坐标，换算成网页坐标系下的拖动距离。
7. 用 `ActionChains` 分 4 段拖动（先快后慢 + 微调回弹），模拟人手轨迹。

## 持久化登录态

脚本里给 Chrome 指定了 `--user-data-dir=.../SeleniumChrome_douban`，首次跑过滑块后豆瓣的 cookies 会写盘。**后续再用同一个 user-data-dir 启动，cookies 仍在，可以直接绕过滑块。**

注意：

- 退出脚本时要让 `driver.quit()` 正常关闭 Chrome，否则 cookies 不写盘。
- 想换账号 / 重置登录态，直接删 `SeleniumChrome_douban/` 整个目录。

## 依赖

- Python 3.x
- selenium >= 4.x
- opencv-python（cv2）
- Pillow
- curl_cffi

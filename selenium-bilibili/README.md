# 哔哩哔哩 UP 主代表作采集

使用 Selenium 打开公开的 UP 主主页，定位「代表作」模块并解析每张代表作品的标题、播放次数、弹幕数、时长。支持懒加载触发、字段缺失兜底、随机延迟等反爬基础配置。

## 使用方法

```powershell
python -m pip install -r requirements.txt
python main.py
```

脚本里写死了 chromedriver 路径与 user-data-dir，使用前请自行修改：

- `service = Service(r"D:\SeleniumChromeDrive\chromedriver.exe")`  ← 你的 chromedriver 路径
- `--user-data-dir=.../SeleniumChrome_bilibili`                    ← 持久化 Chrome 用户目录
- `up_url = '...'`                                                  ← 目标 UP 主主页

## 流程

1. 打开 UP 主主页，等待作品区域出现。
2. 滚动到代表作模块，触发懒加载。
3. 等代表作卡片（`.masterpiece-block__item`）渲染完。
4. 解析每张卡片：标题 / 播放数 / 弹幕数 / 时长。字段缺失时统一兜底为 `'无'`。

## 依赖

- Python 3.x
- selenium >= 4.x

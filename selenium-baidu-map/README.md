# 百度地图公交路线查询

使用 Selenium 在百度地图输入起点和终点，切换到"公共交通"模式，解析公交路线列表（票价 / 路线标签 / 路线名称 / 总耗时 / 总距离 / 步行距离 + 分段步行 / 公交详情），并把每条路线的地图截图保存到本地。

## 使用方法

```powershell
python -m pip install -r requirements.txt
python main.py
```

脚本里写死了 chromedriver 路径与 user-data-dir，使用前请自行修改：

- `service = Service(r"D:\SeleniumChromeDrive\chromedriver.exe")`  ← 你的 chromedriver 路径
- `--user-data-dir=.../SeleniumChrome_map_baidu`                    ← 持久化 Chrome 用户目录
- `start = "..."` / `end = "..."`                                    ← 起点终点

## 流程

1. 展开路线查询输入框。
2. 用 `slow_input` 模仿人输入起点 / 终点。
3. 先点一次"驾车"按钮做热身搜索，再切回"公共交通"（解决公交模式异步加载问题）。
4. 解析路线列表：
   - `parse_route_basic` 提取票价 / 路线标签 / 路线名称 / 总耗时 / 总距离 / 步行距离。
   - `parse_route_detail` 提取分段路径（步行 / 公交）。
   - `screenshot_line` 截图路线地图，写到 `map_images/<起点>--<终点>/`。
5. 截图保存（每个 scheme 一张）。

## 目录说明

- `main.py`：完整脚本。
- `requirements.txt`：依赖列表。
- `map_images/`：截图输出目录，被 Git 忽略。

## 依赖

- Python 3.x
- selenium >= 4.x
- Pillow

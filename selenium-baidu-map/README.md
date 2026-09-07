# 百度地图公交路线查询

使用 Selenium 输入起点和终点，读取公交路线列表，并把当前页面保存为截图。截图写入 `map_images/`，该目录已被 Git 忽略。

```powershell
python -m pip install -r requirements.txt
python main.py "农林大学-地铁站" "灵隐寺"
```

代码使用 Selenium Manager 自动管理 ChromeDriver，不需要写死本机驱动路径。

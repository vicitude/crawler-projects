# 豆瓣 Selenium 登录演示

本项目演示 Selenium 的 iframe 切换、显式等待和登录表单填写。账号信息通过环境变量传入，验证码必须由用户本人手动完成。

```powershell
python -m pip install -r requirements.txt
$env:DOUBAN_USERNAME="你的账号"
$env:DOUBAN_PASSWORD="你的密码"
python main.py
```

也可以不设置环境变量，打开页面后完全手动登录。请勿把真实账号、密码、Cookie 或 Chrome 用户目录提交到 Git。

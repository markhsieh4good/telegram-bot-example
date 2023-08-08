# telegram-bot

# use platform
都寫在use_platform 中，用的是 ubuntu22.04 : supervisor 4.2.1

# 特色
remote telegram bot 是持續輪詢的方式達到可以遠端控制的目的 <br/>
user:telegram client --- telegram bot father server [free] --- remote server:telegram-bot

# 設定
```bash
$ vim config.yaml

```
關於和 telegram bot 連線的方式都在此處

# 環境＆模組
參考 use_platform/ <br/>
- install_python_ub22.04.sh
- requirements.txt

可以用 bash file 安裝，這是我的安裝成功步驟記錄 <br/>
也可以利用 pip3.10 install -r requirements.txt

# 執行
> python3 
```bash
# because use __main__.py
$ python3 telegram-bot 

```
請從repo. folder 作為啟動的參數給予 python3

> supervisor
```bash
$ sudo apt install -y supervisor
$ sudo mkdir -p /opt/supervisor.p/logs
$ sudo ln -s /path/to/repo/telegram-bot /opt/supervisor.p/
$ sudo chmod +x /opt/supervisor.p/telegram-bot/get_ip.sh
$ sudo ln -s /opt/supervisor.p/telegram-bot/get_ip.sh /usr/local/bin/get_ip

$ sudo cp telegram-bot/use_platform/supervisor.4.2.1.conf /etc/supervisor/supervisord.conf
$ sudo cp telegram-bot/use_platform/tg-bot.conf /etc/supervisor/conf.d/
$ sudo service supervisor restart
$ sudo supervisorctl status
```

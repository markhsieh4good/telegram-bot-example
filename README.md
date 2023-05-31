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

$ sudo cp telegram-bot/use_platform/supervisor.4.2.1.conf /etc/supervisor/supervisord.conf
$ sudo cp telegram-bot/use_platform/tg-bot.conf /etc/supervisor/conf.d/
$ sudo service supervisor restart
$ sudo supervisorctl status
```

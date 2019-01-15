import json
import psycopg2
import requests
import os

from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=12, minutes = 15)
def scheduled_job():
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    url = 'https://api.scryfall.com/cards/{}'
    usd_list=[]
    try:
        select = "select distinct id from mtg.card_export where lang = 'en'"
        cursor.execute(select)
        mtg_records = cursor.fetchall()
        for id in mtg_records:
            rsp=requests.get(url.format(id[0]))
            rsp = json.loads(rsp.text)
            try:
                usd = rsp['usd']
            except KeyError:
                usd = 0
            usd_list.append({'id':id[0],'usd':usd})
       # with open('usd_list.data','w') as f:
          #  json.dump(usd_list,f)
    #with open('usd_list.data','r') as f:
     #   usd_list = json.loads(f.read())
        print('Start update')
        for item in usd_list:
            insert = "update mtg.card_price set usd = {} where  id = '{}'".format(item['usd'],item['id'])
            cursor.execute(insert)
            conn.commit()
    finally:
        if (conn):
            cursor.close()
            conn.close()

sched.start()
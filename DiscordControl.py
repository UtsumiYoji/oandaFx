import discord
import asyncio
import configparser
import sys
from decimal import Decimal

#自作関数
import LimitOrderControl, OandaControl

#botAPIキーなどを読み込む
ConfigIns = configparser.ConfigParser()
ConfigIns.read('setting.ini', encoding='utf-8')

#各種インスタンスの作成
client = discord.Client()
LimitIns = LimitOrderControl.LimitOrderControl()
OnadaIns  = OandaControl.OandaControl()

#労働中なら1
running = 1

#指値を入れる関数
async def limitOrder(price, units, limit, stop):
    #動いていいのか確認
    if running == 0:
        return
    
    #指値を入れる
    OnadaIns.LimitOrder(price, units, limit, stop)

    #メッセージ送信先チャンネルを設定
    channel = client.get_channel(int(ConfigIns['channel']['limitChannel']))
    #メッセージ送信
    await channel.send(
        '**指値を入れました！**\n\
価格：' + str(price) + '　数量：' + str(units)
    )

#ループして処理させる関数
async def loop():
    while True:
        #5分待つ
        await asyncio.sleep(299)

        #動いていいのか確認
        if running == 0:
            continue

        #現在なんかクローズしてないポジションを持ってないか確認
        if not len(OnadaIns.NowPosition()) == 0:
            continue

        #指値を入れる値を計算させる
        LimitPrice = LimitIns.LimitPriceClac()
        
        #リミットオーダーとストップオーダーを計算
        longLimit = Decimal(LimitPrice['long']) + Decimal('0.01')
        longStop = Decimal(LimitPrice['long']) - Decimal('0.10')
        shortLimit = Decimal(LimitPrice['short']) - Decimal('0.01')
        shortStop = Decimal(LimitPrice['short']) + Decimal('0.10')

        #現在持ってる指値を取得
        Pending = OnadaIns.OrdersPending()
        
        #指値が何もないなら指値をとりあえずもつよ
        if len(Pending) == 0:
            await limitOrder(LimitPrice['long'], 50000, longLimit, longStop)
            await limitOrder(LimitPrice['short'], -50000, shortLimit, shortStop)
        
        #指値をもってるみたい
        else:
            #フラグを初期化
            longFlag = shortFlag = 0

            #持ってる指値が僕の想定したやつか確認
            for i in range(len(Pending)):
                #ロングの指値
                if int(Pending[i]['units']) > 0:
                    #今回のロングについて処理したことをフラグ
                    longFlag = 1

                    if not Pending[i]['price'] == LimitPrice['long']:
                        #想定していない指値だった場合キャンセルする
                        OnadaIns.OrderCancel(int(Pending[i]['id']))
                        #指値を入れなおす
                        await limitOrder(LimitPrice['long'], 50000, longLimit, longStop)

                #ショートの指値
                else:
                    #今回ショートについて処理したことをフラグ
                    shortFlag = 1

                    if not Pending[i]['price'] == LimitPrice['short']:
                        #想定していない指値だった場合キャンセルする
                        OnadaIns.OrderCancel(int(Pending[i]['id']))
                        #指値を入れなおす
                        await limitOrder(LimitPrice['short'], -50000, shortLimit, shortStop)
            
            #ロングフラグが0なら指値もってないので持つ
            if longFlag == 0:
                await limitOrder(LimitPrice['long'], 50000, longLimit, longStop)
            
            #ショートフラグが0なら指値もってないので持つ
            if shortFlag == 0:
                await limitOrder(LimitPrice['short'], -50000, shortLimit, shortStop)
    
@client.event
async def on_ready():
    print('login!')
    await client.change_presence(activity=discord.Game(name='Now running!!!'))
    await loop()

@client.event
async def on_message(msg):
    global running
    #稼働のストップ
    if msg.content == '.stop':
        running = 0
        await client.change_presence(activity=discord.Game(name='Stop'))
        await msg.channel.send('動作を停止しました\n強制ストップは.emstopです')
    
    #労働のスタート
    if msg.content == '.run':
        running = 1
        await client.change_presence(activity=discord.Game(name='Now running!!!'))
        await msg.channel.send('動作を開始しました')
    
    #緊急停止
    if msg.content == '.emstop':
        await msg.channel.send(
            'アプリケーションの終了で動作を停止させます\n\
再開には手動でアプリケーションの再起動が必要です\n\
既に入れている指値は手動でキャンセルして下さい')
        sys.exit()
    
client.run(ConfigIns['discord']['token_key'])

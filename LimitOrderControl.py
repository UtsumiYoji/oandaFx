import numpy as np
import OandaControl

class LimitOrderControl:
    def __init__(self) -> None:
        self.OandaIns = OandaControl.OandaControl()
        self.threshold = 0.21

    def LimitPriceClac(self):
        #OrderBookを取得
        OrderBook = self.OandaIns.OrderBook()
        
        #現在の為替の中値を取得
        NowPrice = self.OandaIns.NowRate()['ltp']
        #0.05の倍数で丸め込み
        NowPrice = round(NowPrice * 20) / 20

        #現在価格を中心に±1と現在の値を0埋めして文字型に
        under = str(NowPrice - 1).ljust(7, '0')
        over = str(NowPrice + 1).ljust(7, '0')
        NowPrice = str(NowPrice).ljust(7, '0')

        #underとoverが位置するインデックスを取得
        under = np.where(OrderBook[:, 0]==under)[0][0]
        over = np.where(OrderBook[:, 0]==over)[0][0]
        NowPrice = np.where(OrderBook[:, 0]==NowPrice)[0][0]

        #orderbookを切り出して数値型に変換
        LongPrice = OrderBook[under:NowPrice, 0]
        ShortPrice = OrderBook[NowPrice:over, 0]
        LongNet = OrderBook[under:NowPrice, 1].astype(np.float32) - OrderBook[under:NowPrice, 2].astype(np.float32)
        ShortNet = OrderBook[NowPrice:over, 1].astype(np.float32) - OrderBook[NowPrice:over, 2].astype(np.float32)

        #価格-純額で2次元リストを作成        
        short = [[ShortPrice[i], ShortNet[i]] for i in range(len(ShortNet))]
        long = [[LongPrice[i], LongNet[i]] for i in range(len(LongNet))][::-1]
        del ShortPrice, LongPrice, ShortNet, LongNet

        #short値反転を検出
        #反転の次の値がスタートになるので注意
        shortStart = longStart = 0
        for i in range(len(short)):
            #ショートの場合buyが多い場合検出
            if short[i][1] > 0:
                shortStart = i + 1
            
            #ロングの場合はsellが多い場合検出
            if long[i][1] < 0:
                longStart = i + 1
        
        #結果を格納する変数を作成
        result = {}

        #反転の値からスタートしてオーダーが閾より多い部分を切り出す
        for i in range(shortStart, len(short)):
            if self.threshold < abs(short[i][1]):
                result['short'] = short[i][0]
                break

        for i in range(longStart, len(long)):
            if self.threshold < long[i][1]:
                result['long'] = long[i][0]
                break
            
        return result
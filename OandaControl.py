import oandapyV20
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.positions as positions

import pandas as pd

class OandaControl:

    def __init__(self) -> None:
        self.client = oandapyV20.API(
            access_token = "54d4d31c83471fc4ee91a5a0f6dda36a-deea989a856d8fd98e35d17726906daa", environment="live")
        
        self.id = "001-009-6560569-001"

    #残金の取得
    def NowSummary(self):
        request = accounts.AccountSummary(self.id)
        response = self.client.request(request)['account']['balance']

        return response
    
    #現在の為替の取得
    def NowRate(self):
        #リクエストを送る
        request = pricing.PricingInfo(self.id, params={"instruments":"USD_JPY"})
        response = self.client.request(request)

        #戻り値の型を用意
        result = {}

        #askとbitだけ抽出
        result['bid'] = float(response['prices'][0]['bids'][0]['price'])
        result['ask'] = float(response['prices'][0]['asks'][0]['price'])
        result['ltp'] = (result['bid']+result['ask']) / 2

        return result

    #orderbookの取得
    def OrderBook(self):
        #リクエストを送る
        request = instruments.InstrumentsOrderBook(instrument="USD_JPY")
        response = self.client.request(request)

        #データをnumpy型に格納
        result = pd.DataFrame(response["orderBook"]["buckets"])
        result = result.values

        return result
    
    #指値注文
    def LimitOrder(self, price, units, limit, stop):
        #注文データの詳細を決定する
        OrderDetails = {
            'order': {
                'price' : str(price),
                'instrument': 'USD_JPY',
                'units': str(units),
                'type': 'LIMIT',
                'positionFill': 'DEFAULT',
                'takeProfitOnFill': {
                    'price' : str(limit)
                },
                'stopLossOnFill': {
                    'price' : str(stop)
                }
            }
        }

        #リクエストを送る
        request = orders.OrderCreate(self.id, data=OrderDetails)
        response = self.client.request(request)

        #レスポンスから注文IDのみを取り出す
        result = response['orderCreateTransaction']['id']
        return result
    
    #指値注文のキャンセル
    def OrderCancel(self, id:int):
        #リクエストを送る
        request = orders.OrderCancel(self.id, id)
        self.client.request(request)
    
    #ペンディング中のデータを取得
    def OrdersPending(self):
        #リクエストを送る
        request = orders.OrdersPending(self.id)
        response = self.client.request(request)

        #オーダー情報だけ取り出す
        result = response['orders']

        #指値中のオーダーをリストにして返す
        return result

    #現在のポジションを取得
    def NowPosition(self):
        #リクエストを送る
        request = positions.OpenPositions(self.id)
        response = self.client.request(request)

        #ポジション情報を取り出す
        result = response['positions']

        return result

    #ポジションの決済
    def PositionClose(self, units:int, type:str):
        #ショートとロングのどっちなのか
        if type == 'long':
            #安い時に買ったから売り払う命令
            data = {'longUnits': str(units)}
        elif type == 'short':
            #高い時に売ったから買い戻す命令
            data = {'shortUnits': str(units)}

        request = positions.PositionClose(self.id, instrument='USD_JPY', data=data)
        self.client.request(request)

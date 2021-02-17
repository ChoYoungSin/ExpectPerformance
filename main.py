from consensus import getConsensus
from expectedResult import getDisclosure, diffStockList, getRceptNum, crawlingRcept
import json

from pandas import DataFrame as df
import time
from pprint import pprint

if __name__ == "__main__":
    while True:
        preDisclosure = json.load(open('data/Disclosure_1.json', 'r', encoding='utf-8'))
        disclosure = getDisclosure()
        diffList = diffStockList(preDisclosure, disclosure)


        # expect   : 잠정 실적 종목 정보들 param : [종목 코드, 종목명, rcept_no, corp_code]
        # thisTerm : 정기 공시 종목 정보들 param : [종목 코드, 종목명, rcept_no, corp_code]

        expect, thisTerm = getRceptNum(diffList)
        result = crawlingRcept(expect)  # result에 신규 잠정실적 크롤링 결과 있음
        output = df(data=result['data'])
        output.to_csv("data/result.csv", encoding='UTF-8-SIG')
        consen = getConsensus(result)

        for ep in result['data']:
            s = consen[ep['종목코드']]['SALES']
            yoy = consen[ep['종목코드']]['YOY']
            o = consen[ep['종목코드']]['OP']
            n = consen[ep['종목코드']]['NP']
            print(ep['종목명'].ljust(15, ' '), "매출액 비교", ep['매출액 성장률'], '\t', yoy)
        print('Done')
        time.sleep(2.5)
        # 개장 시간 : 380분, 22800초
        # 하루에 1만회 조회 가능
        # 22800 / 10000 = 2.28
        # 2.28초에 1회 조희시 개장 시간동안 유지, 넉넉히 2.5초당 한번
        # notice : get_finance_info는 항상 실행되지 않고 하루에 발행되는 정기 공시 만큼 실행되기 때문에 대세에 지장 없음.

        break
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

        expect, thisTerm = getRceptNum(diffList)  # receptNum에 신규 잠정실적 종목리스트 있음
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
        break
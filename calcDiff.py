from consensus import getConsensus
from expectedResult import getDisclosure, diffStockList, getRceptNum, crawlingRcept
import thisTermReport
import json
from multiprocessing import Process, Queue

import pandas as pd
import time
import win32com.client
import telegram

chat_token = "1631423601:AAGfki6HTB0SSB7tDHP_Vj-WbuziwAg7FJg"
bot = telegram.Bot(token=chat_token)

'''updates = bot.getUpdates()
    code_list = []

    for i in updates:
        print(i)'''
id_list = [1170179304]#[1170179304, 1437194944, 1175245571, 1619942450, 1338655098, 1184589601, 1255604220, 1215592271,1227872883]
rate = 1.1  # 컨센 대비 10% 이상
rateUser = int((rate - 1) * 100)


def multi(x):
    if x >= 0:
        return x*rate
    else:
        return x*(2.0-rate)

def calc(x, y): # x : 실적, y : 컨센
    if x == '-' or y == '':
        return '정보없음'
    if x > 0 and y < 0:
       return '컨센대비 흑자 전환'
    elif x<0 and y > 0:
       return '컨센대비 적자 전환'
    elif x > 0 and y > 0:
       return str(round((x-y)/abs(y)*100))
    else:
        return '적자기업'


#if __name__ == "__main__":
result = []
def mainF(q):
    global result
    print('Process Start')
    print('          매출액     영업이익     순이익')
    while True:
        preDisclosure = json.load(open('data/Disclosure.json', 'r', encoding='utf-8'))
        disclosure = getDisclosure()
        if disclosure == False:
            time.sleep(3)
            print('No new msg')
            continue
        diffList = diffStockList(preDisclosure, disclosure)

        # expect   : 잠정 실적 종목 정보들 param : [종목 코드, 종목명, rcept_no, corp_code]
        # thisTerm : 정기 공시 종목 정보들 param : [종목 코드, 종목명, rcept_no, corp_code]
        expect, thisTerm = getRceptNum(diffList)
        result = thisTermReport.run_performance(thisTerm)
        #result = crawlingRcept(expect)  # result에 신규 잠정실적 크롤링 결과 있음

        consen = getConsensus(result)

        for stockCode in consen.keys():
            #expectYoy   = float(consen[stockCode]['YOY'].replace(',', '')) # 전년동기대비 매출액 성장률
            expectSales = consen[stockCode]['SALES'].replace(',', '')  # 매출액
            expectOp = consen[stockCode]['OP'].replace(',', '')  # 영업이익
            expectNp = consen[stockCode]['NP'].replace(',', '')  # 순이익

            flagA = True
            flagB = True
            flagC = True

            if expectSales != '':
                expectSales = float(expectSales) * 10000  # 매출액
            else:
                flagA = False
            if expectOp != '':
                expectOp = float(expectOp) * 10000  # 영업이익
            else:
                flagB = False
            if expectNp != '':
                expectNp = float(expectNp) * 10000  # 순이익
            else:
                flagC = False

            sales = result[stockCode]['매출액']
            op = result[stockCode]['영업이익']
            np = result[stockCode]['순이익']
            unit = result[stockCode]['단위']


            print(result[stockCode]['종목명'], '실적: ', sales, op, np)
            print(result[stockCode]['종목명'], '컨센: ', expectSales, expectOp, expectNp)
            print(result[stockCode]['순이익 성장률'], '\n')

            if sales != '-' and op != '-' and np != '-' and op > 0 and np > 0: # 적자 기업 제거
                sales *= unit
                op *= unit
                np *= unit

                textForm = '매출액    : ' + format(round(sales /10000.0), ',') + '억 (' + result[stockCode]['매출액 성장률'] + '%)' + ' 컨센대비 ' + calc(sales, expectSales) + '%\n' +\
                            '영업이익 : ' + format(round(op /10000.0), ',') + '억 (' + result[stockCode]['영업이익 성장률'] + '%)' + ' 컨센대비 ' + calc(op, expectOp) + '%\n'\
                            '순이익    : ' + format(round(np / 10000.0), ',') + '억 (' + result[stockCode]['순이익 성장률'] + '%)' + ' 컨센대비 ' + calc(np, expectNp) + '%'
                # Case 1 셋다 비교
                if flagA and flagB and flagC and sales > multi(expectSales) and op > multi(expectOp) and np > multi(expectNp):
                    t = '[' + result[stockCode]['종목명'] + '] : 매출액, 영업이익, 순이익 ' + str(rateUser) + '% 이상\n' + textForm
                    #q.put(stockCode)
                    for id in id_list:
                        bot.sendMessage(chat_id=id, text=t)
                    df = pd.read_csv('data/save.csv', encoding='utf-8-sig')
                    df = df.append({'name': result[stockCode]['종목명'], '매출액': format(round(sales / 10000.0), ','),
                                    '영익': format(round(op / 10000.0), ','), '순익': format(round(np / 10000.0), ','),
                                    '매출액 성장률': result[stockCode]['매출액 성장률'] + '%',
                                    '영업이익 성장률': result[stockCode]['영업이익 성장률'] + '%',
                                    '당기순이익 성장률': result[stockCode]['순이익 성장률'] + '%',
                                    '컨센대비 매출액': calc(sales, expectSales), '컨센대비 영익': calc(op, expectOp),
                                    '컨센대비 순익': calc(np, expectNp)}, ignore_index=True)
                    df.to_csv('data/save.csv', index=False, encoding='utf-8-sig')

                # Case 2 매출액,영익
                elif flagA and flagB and sales > multi(expectSales) and op > multi(expectOp):
                    t = '[' + result[stockCode]['종목명'] + '] : 매출액,영업이익' + str(rateUser) + '% 이상\n' + textForm
                    #q.put(stockCode)
                    for id in id_list:
                        bot.sendMessage(chat_id=id, text=t)
                    df = pd.read_csv('data/save.csv', encoding='utf-8-sig')
                    df = df.append(
                        {'name': result[stockCode]['종목명'], '매출액': format(round(sales / 10000.0), ','),
                         '영익': format(round(op / 10000.0), ','), '순익': format(round(np / 10000.0), ','),
                         '매출액 성장률': result[stockCode]['매출액 성장률'] + '%',
                         '영업이익 성장률': result[stockCode]['영업이익 성장률'] + '%',
                         '당기순이익 성장률': result[stockCode]['순이익 성장률'] + '%',
                         '컨센대비 매출액': calc(sales, expectSales), '컨센대비 영익': calc(op, expectOp),
                         '컨센대비 순익': calc(np, expectNp)}, ignore_index=True)
                    df.to_csv('data/save.csv', index=False, encoding='utf-8-sig')

                # Case 3 영익, 순익
                elif flagB and flagC and op > multi(expectOp) and np > multi(expectNp):
                    t = '[' + result[stockCode]['종목명'] + '] : 영업이익, 순이익' + str(rateUser) + '% 이상\n' + textForm
                    #q.put(stockCode)
                    for id in id_list:
                        bot.sendMessage(chat_id=id, text=t)
                    df = pd.read_csv('data/save.csv', encoding='utf-8-sig')
                    df = df.append(
                        {'name': result[stockCode]['종목명'], '매출액': format(round(sales / 10000.0), ','),
                         '영익': format(round(op / 10000.0), ','), '순익': format(round(np / 10000.0), ','),
                         '매출액 성장률': result[stockCode]['매출액 성장률'] + '%)',
                         '영업이익 성장률': result[stockCode]['영업이익 성장률'] + '%',
                         '당기순이익 성장률': result[stockCode]['순이익 성장률'] + '%',
                         '컨센대비 매출액': calc(sales, expectSales), '컨센대비 영익': calc(op, expectOp),
                         '컨센대비 순익': calc(np, expectNp)}, ignore_index=True)
                    df.to_csv('data/save.csv', index=False, encoding='utf-8-sig')

        print('Done')
        break
        time.sleep(5)
        # 개장 시간 : 380분, 22800초
        # 하루에 1만회 조회 가능
        # 22800 / 10000 = 2.28
        # 2.28초에 1회 조희시 개장 시간동안 유지, 넉넉히 2.5초당 한번
        # notice : get_finance_info는 항상 실행되지 않고 하루에 발행되는 정기 공시 만큼 실행되기 때문에 대세에 지장 없음.

q = 0
mainF(q)
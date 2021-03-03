# -*- coding: utf-8 -*-

import json
import requests
from bs4 import BeautifulSoup
import time

nowTime = time.strftime('%Y-%m-%d-%H-%M', time.localtime(time.time()))
API_KEY = '5f07cd939992731e7c66c87fe28923daa3366e94'

pblntf_ty = {"분기": 'A003', "잠정": 'I002'}


def getDisclosure():
    # Disclosure 추출.
    # 결과: Disclosure.json 생성
    # API : 공시정보
    result = {'data': []}
    page_count = 1
    while True:
        param = {
            'crtfc_key': API_KEY,
            #'bgn_de': str(20210216),
            'pblntf_detail_ty': ['I002', 'A001'],  # pblntf_ty["잠정"],
            # 'corp_cls': 'K',
            'page_no': str(page_count),
            'page_count': '100'
        }

        r = requests.get(
            'https://opendart.fss.or.kr/api/list.json', params=param)
        r.raise_for_status()
        data = json.loads(r.text)
        #print(data)
        if data['status'] == '013':
            return False
        result['data'].append(data)
        if data['total_page'] <= page_count:
            break
        print(page_count)
        page_count += 1

    with open('data/Disclosure.json', 'w', encoding='UTF-8') as jf:
        jsonString = json.dumps(result, indent=4, ensure_ascii=False)
        jf.write(jsonString)
    return result


def getRceptNum(diffList):
    expect = []
    thisTerm = []
    for enterprise in diffList:
        if '잠정' in enterprise['report_nm']:
            expect.append([enterprise['stock_code'], enterprise['corp_name'], enterprise['rcept_no'], enterprise['corp_code']])
        elif '보고서' in enterprise['report_nm'] and '정정' not in enterprise['report_nm'] and '추가' not in enterprise['report_nm']:
            thisTerm.append([enterprise['stock_code'], enterprise['corp_name'], enterprise['rcept_no'], enterprise['corp_code']])

    with open('data/RceptNumber.json', 'w', encoding='UTF-8') as outfile:
        json.dump(expect + thisTerm, outfile, indent=4, ensure_ascii=False)

    return expect, thisTerm


def crawlingRcept(rcpNum):
    result = {}
    # print(rcpNum)
    for rcp in rcpNum:
        try:
            res = requests.get(
                'http://dart.fss.or.kr/dsaf001/main.do?rcpNo=' + rcp[2])
            soup = BeautifulSoup(res.content, 'html.parser')
            src = soup.find('a', {'href': '#download'})
            dcmNum = src.get('onclick')[35:42]

            res = requests.get('http://dart.fss.or.kr/report/viewer.do?rcpNo=' +
                               rcp[2]+'&dcmNo='+dcmNum+'&eleId=0&offset=0&length=0&dtd=HTML')
            soup = BeautifulSoup(res.content, 'html.parser')

            table = soup.select(
                'tbody > tr:nth-child(5) > td:nth-child(3) > span')[0]
            sales = table.get_text().split()[-1]
            if sales != '-':
                sales = float(sales.strip('()').replace(',', ''))

            table = soup.select(
                'tbody > tr:nth-child(5) > td:nth-child(7) > span')[0]
            salesRate = table.get_text().split()[-1]

            table = soup.select(
                'tbody > tr:nth-child(7) > td:nth-child(3) > span')[0]
            profits = table.get_text().split()[-1]
            table = soup.select(
                'tbody > tr:nth-child(7) > td:nth-child(7) > span')[0]
            if profits != '-':
                profits = float(profits.strip('()').replace(',', ''))
            profitsRate = table.get_text().split()[-1]

            table = soup.select(
                'tbody > tr:nth-child(11) > td:nth-child(3) > span')[0]
            netProfits = table.get_text().split()[-1]
            if netProfits != '-':
                netProfits = float(netProfits.strip('()').replace(',', ''))
            table = soup.select(
                'tbody > tr:nth-child(11) > td:nth-child(7) > span')[0]
            netProfitsRate = table.get_text().split()[-1]

            table = soup.select(
                'tbody > tr:nth-child(2) > td:nth-child(2) > span')
            if table != []:
                unit = table[0].get_text()
            else:
                table = soup.select(
                    'tbody > tr:nth-child(3) > td:nth-child(1) > span')
                unit = table[0].get_text()
            if '백' in unit:
                unit = 100
            elif '천' in unit:
                unit = 1000
            elif '억' in unit:
                unit = 10000
            else:
                unit = 100

            try:
                profitRate = (int(profits[0].replace(
                    ',', ''))/int(sales[0].replace(',', '')))*100
            except:
                profitRate = '-'

            '''print("rcpNum: ", rcp)
            print('sales: ', sales)
            print('profits: ', profits)
            print('netProfits: ', netProfits, '\n')'''
            result.update({rcp[0] : {'종목명': rcp[1], '단위': unit,
                                   '매출액': sales, '영업이익': profits, '당기순이익': netProfits,
                                   '매출액 성장률': salesRate.strip('()').replace(',', ''), '영업이익 성장률': profitsRate.strip('()').replace(',', ''), '당기순이익 성장률': netProfitsRate.strip('()').replace(',', '')}})

        except Exception as ex:
            print(ex, rcp)

    with open('data/RceptCrawling.json', 'w', encoding='UTF-8') as outfile:
        json.dump(result, outfile, indent=4, ensure_ascii=False)
    return result


def diffStockList(pre, now):
    diffList = []

    pre = pre['data'][0]['list']
    now = now['data'][0]['list']
    for i in now:
        if i not in pre:
            diffList.append(i)
    return diffList


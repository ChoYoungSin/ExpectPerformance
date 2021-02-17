# -*- coding: utf-8 -*-

import json
import requests
import re
from bs4 import BeautifulSoup
from pandas import DataFrame as df
import time
from pprint import pprint

nowTime = time.strftime('%Y-%m-%d-%H-%M', time.localtime(time.time()))
API_KEY = '5f07cd939992731e7c66c87fe28923daa3366e94'

pblntf_ty = {"분기": 'A003', "잠정": 'I002'}


def getDisclosure(begin_date):
    # Disclosure 추출.
    # 결과: Disclosure.json 생성
    # API : 공시정보
    result = {'data': []}
    page_count = 1
    while True:
        param = {
            'crtfc_key': API_KEY,
            'bgn_de': str(begin_date),
            'pblntf_detail_ty': 'I002',  # pblntf_ty["잠정"],
            # 'corp_cls': 'K',
            'page_no': str(page_count),
            'page_count': '100'
        }

        r = requests.get(
            'https://opendart.fss.or.kr/api/list.json', params=param)
        r.raise_for_status()
        data = json.loads(r.text)
        # print(data)

        result['data'].append(data)
        if data['total_page'] <= page_count:
            break
        page_count += 1

    with open('data/Disclosure.json', 'w', encoding='UTF-8') as jf:
        jsonString = json.dumps(result, indent=4, ensure_ascii=False)
        jf.write(jsonString)
    return result


def getRceptNum(diffList):
    temp = []
    for enterprise in diffList:
        if '잠정' in enterprise['report_nm']:
            temp.append([enterprise['stock_code'], enterprise['corp_name'],
                         enterprise['rcept_no']])  # enterprise['report_nm'],

    with open('data/RceptNumber.json', 'w', encoding='UTF-8') as outfile:
        json.dump(temp, outfile, indent=4, ensure_ascii=False)

    return temp


def crawlingRcept(rcpNum):
    result = {'data': []}
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
                'tbody > tr:nth-child(5) > td:nth-child(7) > span')[0]
            sales = table.get_text().split()
            table = soup.select(
                'tbody > tr:nth-child(7) > td:nth-child(7) > span')[0]
            profits = table.get_text().split()
            table = soup.select(
                'tbody > tr:nth-child(11) > td:nth-child(7) > span')[0]
            netProfits = table.get_text().split()

            # sales.append('-')
            # profits.append('-')
            # netProfits.append('-')
            try:
                profitRate = (int(profits[0].replace(
                    ',', ''))/int(sales[0].replace(',', '')))*100
            except:
                profitRate = '-'

            #print("rcpNum: ", rcp)
            #print('sales: ', sales)
            #print('profits: ', profits)
            #print('netProfits: ', netProfits, '\n')

            result['data'].append({'종목코드': rcp[0], '종목명': rcp[1], '유동비율': '-', '부채비율': '-', '영업이익률': str(profitRate),
                                   '매출액 성장률': sales[-1].strip('()'), '영업이익 성장률': profits[-1].strip('()'), '당기순이익 성장률': netProfits[-1].strip('()')})

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


def getConsensus(data):
    """[result 파일 기반으로 네이버 증권 컨센 자료값 서치]

    Args:
        data (dict): [검색 필요한 종목]

    Returns:
        [dict:list]: [data안의 모든 기업 분기별 정보]
    """
    addUp = {}
    data = data['data']
    for comDic in data:
        addUp.update(readWiseReport(comDic['종목코드'], comDic['종목명']))
        pprint(addUp)
    return addUp


def readWiseReport(corp_code, name):
    """[네이버증권 크롤링]

    Args:
        corp_code (String): [증권번호]

    Returns:
        [dict]: [분기별 정보]
    """
    URL = 'https://navercomp.wisereport.co.kr/company/ajax/c1050001_data.aspx?flag=2&cmp_cd=' + \
        str(corp_code)+'&finGubun=MAIN&frq=1&sDT=20210210&chartType=svg'

    res = requests.get(URL)
    jdata = json.loads(res.text)
    jdata = jdata['JsonData'][-2]
    jdata['Name'] = name
    return {corp_code: jdata}


if __name__ == "__main__":
    nowTime = time.strftime('%Y%m%d', time.localtime(time.time()))
    preDisclosure = json.load(
        open('data/Disclosure_1.json', 'r', encoding='utf-8'))
    disclosure = getDisclosure(20210217)
    diffList = diffStockList(preDisclosure, disclosure)

    receptNum = getRceptNum(diffList)  # receptNum에 신규 잠정실적 종목리스트 있음
    result = crawlingRcept(receptNum)  # result에 신규 잠정실적 크롤링 결과 있음
    output = df(data=result['data'])
    output.to_csv("data/result.csv", encoding='UTF-8-SIG')
    print('Done')

    pprint(getConsensus(result))

    '''
    1분기보고서 : 11013
    반기보고서 : 11012
    3분기보고서 : 11014
    사업보고서 : 11011

    bsns_year = 사업연도
    ※ 2015년 이후 부터 정보제공
    '''

import json
import requests

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
        #pprint(addUp)
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
    jdata['JsonData'][-2]['Name'] = name
    return {corp_code: jdata['JsonData'][-2]}
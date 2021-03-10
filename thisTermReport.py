import json
import requests
from expectedResult import API_KEY
from pprint import pprint

def search_dict(section, data):
    gen_dict = (item for item in data if item['account_nm'] == section)
    found_dict = next(gen_dict, False)
    if found_dict:
        if found_dict['thstrm_amount'] == '-':
            return False
        r = int(found_dict['thstrm_amount'].replace(',', ''))
        if type(r) == int:
            return r

def search_growth(section, data):
    gen_dict = (item for item in data if item['account_nm'] == section)
    found_dict = next(gen_dict, False)
    if found_dict:
        if found_dict['thstrm_amount'] == '-' or found_dict['frmtrm_amount'] == '-':
            return [False, False, False]
        now = int(found_dict['thstrm_amount'].replace(',', ''))
        old = int(found_dict['frmtrm_amount'].replace(',', ''))
        if section != '매출액' and now > 0 and old < 0:
            return [9999, old, now]
        else:
            return [(now-old) / old * 100, old, now]

def get_finance_info(business_year, report_code, corp_name, corp_code):
    result = {}
    if '스팩' not in corp_name:
        param = {
            'crtfc_key': API_KEY,
            'corp_code': corp_code,
            'bsns_year': str(business_year),
            'reprt_code': str(report_code),
        }

        # Make Request
        r = requests.get(
            'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json', params=param)
        r.raise_for_status()
        data = json.loads(r.text)
        result[corp_name] = data
        return result

    else:
        print('Corp Name Erorr : '+corp_name)
        return False

def return_performance(finance_info,report_code_is_11011=False):
    # 이 함수에 return으로
    # return = {종목코드 : {매출액: '', 영업이익: '', 순이익: '', 매출액 성장률: '', 영업이익  성장률: '', 순이익  성장률: ''},
    #          종목코드 : {매출액: '', 영업이익: '', 순이익: '', 매출액 성장률: '', 영업이익  성장률: '', 순이익  성장률: ''},
    #           '''}
    # 위 dictionary 안의 dictionary들로 제공해주면 Best

    jCorp = finance_info
    result = {}

    for name, data in jCorp.items():
        if data['status'] == '013':
            return None

    data = data['list']
    stock_code = data[0]['stock_code']

    if not report_code_is_11011:
        result['종목명'] = name
        result['매출액'] = search_dict('매출액', data)/1000000
        result['영업이익'] = search_dict('영업이익', data)/1000000
        result['순이익'] = search_dict('당기순이익', data)/1000000
        result['매출액 성장률'] = str(round(search_growth('매출액', data)[0], 2))
        result['영업이익 성장률'] = str(round(search_growth('영업이익', data)[0], 2))
        result['순이익 성장률'] = str(round(search_growth('당기순이익', data)[0], 2))
        result['단위'] = 100
        return result

    else:
        result['종목명'] = name
        result['매출액'] = search_dict('매출액', data)/1000000
        result['영업이익'] = search_dict('영업이익', data)/1000000
        result['순이익'] = search_dict('당기순이익', data)/1000000
        result['전년도 매출액'] = search_growth('매출액', data)[1]/1000000
        result['전년도 영업이익'] = search_growth('영업이익', data)[1]/1000000
        result['전년도 순이익'] = search_growth('당기순이익', data)[1]/1000000
        result['단위'] = 100
        return result


def run_performance(thisTerm,business_year,report_code):
    result = {}

    for t in thisTerm:
        if report_code != 11011:
            finance_info = get_finance_info(business_year, report_code, t[1], t[3])
            if finance_info == False:
                pass
            else:
                ret = return_performance(finance_info)
                if ret != None:
                    result[t[0]] = ret
        else:
            data = return_performance(get_finance_info(business_year,report_code,t[1], t[3]),True)
            if data is None:
                continue
            for i in range(2,5):
                finance_info = get_finance_info(business_year, int("1101"+str(i)), t[1], t[3])
                past =  return_performance(finance_info,True)
                data['매출액'] -= past['매출액']
                data['영업이익'] -= past['영업이익']
                data['순이익'] -= past['순이익']
                data['전년도 매출액'] -= past['전년도 매출액']
                data['전년도 영업이익'] -= past['전년도 영업이익']
                data['전년도 순이익'] -= past['전년도 순이익']
            data['매출액 성장률'] = str(round((data['매출액']-data['전년도 매출액'])/data['전년도 매출액']*100,3))
            data['영업이익 성장률'] = str(round((data['영업이익']-data['전년도 영업이익'])/data['전년도 영업이익']*100,3))
            data['순이익 성장률'] = str(round((data['순이익']-data['전년도 순이익'])/data['전년도 순이익']*100,3))
            del data['전년도 매출액'], data['전년도 영업이익'], data['전년도 순이익']
            result[t[0]] = data

    return result

if __name__ == "__main__":
    thisTerm = [['039840', '디오', '20210305000233', '00115931'],
                ['017480', '삼현철강', '20210305000102', '00128926'],
                ['039790', '위노바', '20210305000097', '00261735'],
                ['134380', '미원화학', '20210305000063', '00855163']]
    pprint(run_performance(thisTerm,2020,11011))

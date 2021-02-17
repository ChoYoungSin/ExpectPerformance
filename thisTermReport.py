import json
import requests
from expectedResult import API_KEY

def get_finance_info(business_year, report_code, corp_code):
    """[재무 정보 추출]

    Args:
        business_year ([Int]): [사업연도]
        report_code ([Dict]): [1분기보고서 : 11013/반기보고서 : 11012/3분기보고서 : 11014/사업보고서 : 11011]
        corp_code ([Int]): [고유기업번호]]
        file_name ([String]): [결과물로 저장하고 싶은 파일 이름]

    Returns:
        [Dict]: [finance_info]
    """

    result = {}
    corp_code = corp_code['data']

    for page in corp_code:
        page = page['list']

        for corp in page:
            corp_code = corp['corp_code']
            corp_name = corp['corp_name']
            if '스팩' in corp_name:
                continue
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
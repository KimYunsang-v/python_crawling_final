#-*- coding:utf-8 -*-
import urllib.request
import random
import webbrowser
import sys
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from konlpy.tag import Okt
from collections import Counter
import pytagcloud
from datetime import date

# 랜덤한 색을 지정하기 위한 함수
r = lambda: random.randint(0, 255)
color = lambda: (r(), r(), r())

# argv로 받은 섹션값을 코드로 변환하기 위한 딕셔너리
# 정치, 경제,  사회,  문화,  세계,  IT
section_dic = {'politics': 100, 'economy': 101, 'society': 102, 'culture': 103, 'world': 104, 'it': 105}

# 섹션 코드 지정
if len(sys.argv) > 1:
    section_string = sys.argv[1]
else:
    section_string = 'it'
section = section_dic[section_string]

# 날짜 지정
today = date.today()
if len(sys.argv) > 2:
    date = sys.argv[2]
else:
    date = today.strftime("%Y%m%d")

# URL에 접근해서 태그들 가져오는 함수
def get_request_url(url, enc='euc-kr'):
    # 리퀘스트 객체 생성
    req = urllib.request.Request(url)
    try:
        # url 접근
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            try:
                # 데이터 가져와서 디코딩
                rcv = response.read()
                ret = rcv.decode(enc)
            except UnicodeDecodeError:
                ret = rcv.decode(enc, 'replace')
            return ret

    # 에러 발생 시 로그 생성
    except Exception as e:
        print(e)
        print("[%s] Error for URL : %s" % (datetime.datetime.now(), url))
        return None

# 크롤링 한 뉴스 데이터에서 명사를 추출하고
# 나온 횟수 구하는 함수
def get_tags(text, ntags=50):
    # Okt 객체 생성
    spliter = Okt()
    # 명사 추출
    nouns = spliter.nouns(text)
    # 명사 빈도수 구하기
    count = Counter(nouns)

    # 명사와 빈도수, 색을 딕셔너리 객체에 저장
    return_list = []
    for n, c in count.most_common(ntags):
        temp = {'color': color(), 'tag': n, 'size': c}
        return_list.append(temp)

    return return_list

# 데이터 시각화
def draw_cloud(tags, filename, fontname='Noto Sans CJK', size=(800, 600)):
    # 데이터 시각화
    pytagcloud.create_tag_image(tags, filename, fontname=fontname, size=size)
    # 시각화 파일 오픈
    webbrowser.open(filename)

# 명사 추출 데이터에서 불용어 삭제하기
def remove_stopword(tags):
    # 불용어 데이터 가져오기
    ko_stopwords = pd.read_csv('./ko_stopwords.csv', encoding='cp949', engine='python')
    # 불용어 데이터 리스트 변환
    ko_stopwords = ko_stopwords.STOPWORDS.tolist()
    # print(str(ko_stopwords))

    # 태그들 리스트에서 불용어 제거
    for w in ko_stopwords:
        for item in tags:
            if item['tag'] == w:
                tags.remove(item)

    return tags

# 데이터 크롤링
def getNews():
    # 네이버 뉴스 url
    naver_url = 'https://news.naver.com/main/ranking/popularDay.nhn?rankingType=popular_day&sectionId=%s&date=%s' \
                % (section, date)

    print(naver_url)

    # 뉴스 페이지 데이터 가져오기
    rcv_data = get_request_url(naver_url)
    # html 파서로 데이터 변환
    soup_data = BeautifulSoup(rcv_data, 'html.parser')
    # 뉴스 리스트 가져오기
    news_list = soup_data.find('ol', attrs={'class': 'ranking_list'})
    # print(len(news_list))

    body_text = ''
    # 각 뉴스 접근
    for news in news_list.findAll('li'):
        # 뉴스의 헤드라인 정보 가져오기
        news_data = news.find('div', attrs={'class': 'ranking_headline'})
        # 해당 뉴스 링크 가져오기
        href_data = news_data.find('a')['href']
        # 해당 링크 접근
        article_data = get_request_url('https://news.naver.com/' + href_data)
        # html 파서로 데이터 변환
        soup_data = BeautifulSoup(article_data, 'html.parser')

        body = []
        # 뉴스 본문의 내용 모두 가져오기
        for item in soup_data.findAll('div', attrs={'class': '_article_body_contents'}):
            body.append(item.findAll(text=True, recursive=False))

        # 모든 뉴스 본문 내용 하나로 합치기
        for item in body[0]:
            if item == "\n":
                continue
            body_text = body_text + ' ' + item

    # print(body_text)
    # 본문 내용 명사 & 빈도수 추출
    result_list = get_tags(body_text)

    return result_list

# 메인 함수
def naver_crawler():
    print('NAVER CRAWLING START')

    # 뉴스의 명사 & 빈도수 추출
    result_list = getNews()
    # print('getNews() finished')
    # print(str(result_list))

    # 불용어 제거
    result_list = remove_stopword(result_list)
    print(str(result_list))
    # 데이터 시각화
    draw_cloud(result_list, 'naver_' + section_string + '_' + date + '.png')
    print('FINISHED')

if __name__ == '__main__':
    naver_crawler()
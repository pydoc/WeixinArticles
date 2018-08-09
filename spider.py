from urllib.parse import urlencode
from pymongo import MongoClient
import requests
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from config import *

client = MongoClient(MONGOURL)
db = client[MONGO_DB]

headers = {
    'Cookie': 'CXID=DC1DFE2FB85F647AC393949B435A7A9E; ad=kyllllllll2bghgdlllllVHKJK1lllllNYku0kllll9lllll4Oxlw@@@@@@@@@@@; SUID=8E2688753965860A5B5F25FD000C19DB; IPLOC=CN1100; SUV=1533711442729412; ABTEST=5|1533711445|v1; weixinIndexVisited=1; sct=1; JSESSIONID=aaanU5lCf8v0A_r9Sa7tw; ppinf=5|1533723276|1534932876|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToxODolRTglOTElQTMlRTglQjYlODV8Y3J0OjEwOjE1MzM3MjMyNzZ8cmVmbmljazoxODolRTglOTElQTMlRTglQjYlODV8dXNlcmlkOjQ0Om85dDJsdUFZNDRlTko3TVo0Q201UWRuWHd5NjRAd2VpeGluLnNvaHUuY29tfA; pprdig=Y6UYgIWm-BgyvUpbQDTApRgqrYIfKcdReW3UhnRrJhMBpLUSmW6qbZrtrWHObj-7vIO6Zqmh2mz01qO_CdAkx78jj1Oh7FORcqRlQSTIDqBSqRKOLHrkhJWB2VtuadheaKAPYCrNzbShGVHsb5OCm1izttDg63KrlCfV6nCt4s4; sgid=30-34538441-AVtqwozLkP9eucwRAITwiats; PHPSESSID=j4f8ndre6heqhcqvjaecr7ahs1; SUIR=C36AC5384C483EAB48A13A554DD8B4D8; SNUID=5FF658A4D0D5A23AE5861EE8D1C4903A; ppmdig=1533726837000000984b352fd5e8f3b8570a1ab8c122a67d',
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
}
base_url = 'http://weixin.sogou.com/weixin?'


#如果在方法里设置代理，可能会一直连续不断传代理，当一个参数来回的传会很繁琐，
#如果设置成全局变量的话，只需要更改一次代理，就可以全局生效， 一开始不使用代理，使用本机爬取
proxy = None

#第五步
def get_proxy():
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

#第二步
def get_html(url, count=1):
    print('Crawling', url) #打印一些调试信息
    print('Trying Count', count)
    global proxy
    if count >= MAX_COUNT:
        print('Tried To Many Counts')
        return None
    try:
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            response = requests.get(url, headers=headers, proxies=proxies, allow_redirects=False) #不准许自动跳转
        else:
            response = requests.get(url, headers=headers, allow_redirects=False)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            #需要代理
            print('302')
            proxy = get_proxy()
            if proxy:
                print('Using Proxy:', proxy)
                return get_html(url)
            else:
                print('Get Proxy Failed')
                return None #整个爬取失败
    except ConnectionError as e:
        print('Error Occurred', e.args)
        proxy = get_proxy()
        count += 1
        return get_html(url, count)

#第一步
def get_index(keyword, page):
    data = {
        'type': 2,
        'query': keyword,
        'page': page,
    }
    url = base_url + urlencode(data)
    html = get_html(url)
    return html

#第六步
def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')

#第七步
def get_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

#第八步
def parse_detail(html):
    try:
        doc = pq(html)
        title = doc('.rich_media_title').text()
        content = doc('.rich_media_content ').text()
        #date = doc('.rich_media_meta_list em' ).text()
        nickname = doc('.rich_media_meta_list .profile_inner .profile_nickname').text()
        wechat = doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        return {
            'title': title,
            'content': content,
            #'date': date,
            'nickname': nickname,
            'wechat': wechat,
        }
    except XMLSyntaxError:
        return None

#第九步
def save_to_mongo(data):
    if db['articals'].update({'title': data['title']}, {'$set': data}, True): #True：如果当前查询结果是没有查询到的，就执行插入；如果执行查询到的结果，进行更新
        print('Saved to Mongo', data['title'])
    else:
        print('Saved to Mongo Failed', data['title'])

#第四步
def main():
    for page in range(1, 101):
        html = get_index(KEYWORD, page)
        #print(html)
        if html:
            artical_urls = parse_index(html)
            for artical_url in artical_urls:
                artical_html = get_detail(artical_url)
                if artical_html:
                    artical_data = parse_detail(artical_html)
                    print(artical_data)
                    if artical_data:
                        save_to_mongo(artical_data)

#第三步
if __name__ == '__main__':
    main()

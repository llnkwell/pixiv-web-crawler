import re
from concurrent.futures import ThreadPoolExecutor, wait

import requests
from requests.exceptions import ProxyError

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/97.0.4692.71 Safari/537.36", 'referer': "https://www.pixiv.net/"}
rule = re.compile(r'''</script><link.*?content='.*?"original":"(?P<LINK>.*?)"}''', re.S)
pid_url_list = []
download_url_list = set()
# 得到所有插画的pid
uid = 8103614  #input('Please enter the uid')
url = f"https://www.pixiv.net/ajax/user/{uid}/profile/all?lang=zh"
resp = requests.get(url=url, headers=headers)
resp.encoding = resp.apparent_encoding
content = resp.json()
resp.close()
ill_list = content["body"]['illusts']
for i in ill_list:
    pid_url_list.append(f"https://www.pixiv.net/artworks/{i}")
length = len(pid_url_list)


# 提取单条直链方法
def get_ill_url(pid_url):
    try:
        rec = requests.get(url=pid_url, headers=headers)
        d_url = re.findall(rule, rec.text)
        rec.close()
        for ill in d_url:
            download_url_list.add(ill)
            pid_url_list.remove(pid_url)
            print('.', end='')
    except ProxyError:
        print('!', end='')


# 多线程获取直链
executor_url = ThreadPoolExecutor(max_workers=17)
while len(pid_url_list) != 0:
    url_task = [executor_url.submit(get_ill_url, i_url) for i_url in pid_url_list]
    wait(url_task, timeout=length / 15)
print('\n All Down!')


# 下载单幅插画方法
def down_ill(direct_url):
    file_name = direct_url.split('/')[-1].replace('_p0', '')
    try:
        ill_rec = requests.get(direct_url, headers=headers)
        ill_file = ill_rec.content
        ill_rec.close()
        with open("D:\\Desktop\\image\\" + file_name, "wb") as image:
            image.write(ill_file)
            image.close()
            download_url_list.remove(direct_url)
            print('.', end='')
    except ProxyError:
        print('\n%s failed!' % file_name)


# 多线程实现所有插画的下载
executor_download = ThreadPoolExecutor(max_workers=12)
while len(download_url_list) != 0:
    download_task = [executor_download.submit(down_ill, d_url) for d_url in download_url_list]
    wait(download_task, timeout=length)
print('\n All Downloaded!')

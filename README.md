
这个帖子主要分享 基于python 环境的 pixiv 图片爬取经验分享，主要实现的是给出画师uid，爬取画师的所有插画，下载到本地。

测试环境：PyCharm + Python 3.8.8 @Windows11

```
import re
from concurrent.futures import ThreadPoolExecutor, wait

import requests
from requests.exceptions import ProxyError
```

首先导入的是正则表达式模块、requests模块，另外导入的是多线程库中的ThreadPoolExecutor, wait 方法以 ProxyError 便于后文接收异常并进行处理。

```
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/97.0.4692.71 Safari/537.36", 'referer': "https://www.pixiv.net/"}
rule = re.compile(r'''</script><link.*?content='.*?"original":"(?P<LINK>.*?)"}''', re.S)
pid_url_list = []
download_url_list = set()
uid = 8103614
url = f"https://www.pixiv.net/ajax/user/{uid}/profile/all?lang=zh"
```

接下定义了 headers 参数，其中也带有 referer 防盗链信息；

rule 变量是用于后文在页面html代码中正则匹配原图网址的规则；

pid_url_list 列表用于接收插画网址；download_url_list 为集合，用于接收原图网址，设置成集合可以保证网址不重复。

uid便于测试这边仍然是一个固定的画师，url 则为包含画师所有插画信息的文件，后续用json接收筛选（详细见前文）

```
resp = requests.get(url=url, headers=headers)
resp.encoding = resp.apparent_encoding
content = resp.json()
resp.close()
ill_list = content["body"]['illusts']
for i in ill_list:
    pid_url_list.append(f"https://www.pixiv.net/artworks/{i}")
length = len(pid_url_list)
```

这一步就时对于画师的所有插画信息进行接受，其结果与网址组合后放在列表 pid_url_list 中，需要指出的是，这里用 length 变量保存了画师插画的总数，便于后续的多线程控制。

```
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
```

接下来就是从插画网页页面中获取原图地址的方法实现了，这次针对单个 url 编写了方法，这样逻辑更清晰，后续实现也比较方便。这次对于输出呈现也做了一定优化，对于获取成功的连接，输出不换行的“   .   ”，然后在原列表中删去这条链接，失败的连接则输出“    ！  ”号，这样运行情况也就一目了然了。

```
# 多线程获取直链
executor_url = ThreadPoolExecutor(max_workers=17)
while len(pid_url_list) != 0:
    url_task = [executor_url.submit(get_ill_url, i_url) for i_url in pid_url_list]
    wait(url_task, timeout=length / 15)
print('\n All Down!')
```

对于这个多线程任务，这里设置了线程池最大存活时间为 总插画数/15 实测这个数据其实是足够抓取所有网址了。对于其中每一个插画地址，若是出现失败则会调用上文的方法输出“  ！”，整个多线程函数在插画链接列表长度不为0时持续运行，也就是说，该多线程函数在找到所有插画对应的原图地址、或是超时才停止运行。停止运行后输出提示语句。

```****
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
```

此处下载单幅插画的方法与上文也大同小异，这里也同样和上文抓取原链接一样进行了针对单个链接的变化，也一样有成功就删去、相关输出呈现的操作，此处略去不提。

```
# 多线程实现所有插画的下载
executor_download = ThreadPoolExecutor(max_workers=12)
while len(download_url_list) != 0:
    download_task = [executor_download.submit(down_ill, d_url) for d_url in download_url_list]
    wait(download_task, timeout=length)
print('\n All Downloaded!')
```

最后就是下载部分了，大致多线程的实现思路也大同小异。这里设置线程池大小为12，若是家里带宽很大或是想尝试更快的速度的话大家可以自行调整。楼主这里测试的是100Mbps带宽下载133张图片，总大小为100M左右，大概40s就可以完成。


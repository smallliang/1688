import re
import time
import json
import multiprocessing as mp
import csv
import codecs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import requests
from lxml import etree
import configparser
import os

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
}

id = '865221706'

buy = ['item quality', 'item shipment', 'item exchange', 'item dc', 'item auth']

now = time.time()
url = 'https://m.1688.com/offer/%s.html' % id
page = requests.get(url, headers=headers)
html = page.text
json_str = re.findall('(?<=0]=)(.*?)(?=</script>)', html)
json_str = json_str[-1] if json_str else ''
json_obj = json.loads(json_str)
# 商品名称
subjectName = json_obj['subject']
# 公司名称
companyName = json_obj["companyName"]
# 公司位置
location = json_obj["freightInfo"]["location"]
# 买家保障
guaranteeLogoList = [i['serviceName'] for i in json_obj['guaranteeLogoList']] if 'guaranteeLogoList' in json_obj else []
# 图片链接
imageList = [i['originalImageURI'] for i in json_obj['imageList']]
# 价格、起批数量
price = ''
begin = ''
hasPromotionDiscount = json_obj['hasPromotionDiscount']
if hasPromotionDiscount == 'true':
    priceRanges = json_obj['priceRanges']
    for i in priceRanges:
        if i['convertPrice']:
            price += i['convertPrice'] + '\n'
        if i['begin']:
            begin += i['begin'] + '\n'
else:
    priceRanges = json_obj['priceRanges']
    for i in priceRanges:
        if 'price' in i:
            price += i['convertPrice'] + '\n'
        if 'Price' in i:
            price += i['convertPrice'] + '\n'
        if i['begin']:
            begin += i['begin'] + '\n'
# 规格、价格、起批数量
guige = ''
canBookCount = ''
if json_obj['skuMap'] != None:
    skuMap = json_obj['skuMap']
    for key, value in skuMap.items():
        guige += key + '\n'
        # if 'discountPrice' in value:
        #     dic['价格'] = value['discountPrice']
        canBookCount += value['canBookCount'] + '\n'
# 星级
rateAverageStarLevel = json_obj['rateAverageStarLevel']
# 评论数量、分布
# rateTotals = json_obj['rateTotals']
# rateStarLevelMap = json_obj['rateStarLevelMap']
# 30天销售数量
saledCount = json_obj['saledCount']
# 是否分销
# fenxiao = []
# if 'isConsignOffer' in json_obj:
#     url = 'https://m.1688.com/offer/%s.html?sk=consign' % id
#     page = requests.get(url, headers=headers)
#     html = page.text
#     json_str = re.findall('(?<=0]=)(.*?)(?=</script>)', html)
#     json_str = json_str[-1] if json_str else ''
#     json_obj = json.loads(json_str)
#     hasPromotionDiscount = json_obj['hasPromotionDiscount']
#     if hasPromotionDiscount == 'true':
#         priceRanges = json_obj['priceRanges']
#         for i in priceRanges:
#             dic = {}
#             dic['价格'] = i['price']
#             dic['起批数量'] = i['begin']
#             fenxiao.append(dic)
#     else:
#         priceRanges = json_obj['priceRanges']
#         for i in priceRanges:
#             dic = {}
#             dic['价格'] = i['convertPrice']
#             dic['起批数量'] = i['begin']
#             fenxiao.append(dic)
# 商家信息
url = 'https://detail.1688.com/offer/%s.html' % id
page = requests.get(url, headers=headers)
html = page.text
response = etree.HTML(html)
seller_info = {}
sellinfo = response.xpath('//div[@class="supplierinfo-common"]/div[@class="content"]')
if sellinfo:
    sellinfo = sellinfo[0]
    sell_verify = sellinfo.xpath('div[1]/div[@class="certify-info"]')[
        0].xpath('string(.)').split()
    trade_medal = sellinfo.xpath('div[@class="detail"]/div[@class="item trade-medal fd-clr  trade-medal-container "]/div')
    if trade_medal != []:
        trade_medal = trade_medal[0].xpath('string(.)').split()[0]
    else:
        trade_medal = ''
    supply_mode = sellinfo.xpath('div[@class="detail"]/div[@class="item biz-type fd-clr"]/span/text()')
    if supply_mode != []:
        supply_mode = supply_mode[0]
    else:
        supply_mode = ''
    percent = sellinfo.xpath('div[@class="detail"]/div[@class="common_supplier_bsr"]/div/a/div/div[4]/div/span[2]/text()')
    if percent != []:
        percent = percent[0]
    else:
        percent = '0'
elif response.xpath('//div[@class="smt-info"]/div[@class="content"]'):
    sellinfo = response.xpath('//div[@class="smt-info"]/div[@class="content"]')[0]
    sell_verify = sellinfo.xpath('div[@class="abstract"]/div[@class="certify-info"]')[
        0].xpath('string(.)').split()
    trade_medal = sellinfo.xpath('div[@class="detail"]/div[@class="detail-trade"]/div/dl/dd/a/@title')
    if trade_medal != []:
        trade_medal = trade_medal[0]
    else:
        trade_medal = ''
    supply_mode = sellinfo.xpath('div[@class="detail"]/div[@class="smt-biz-type"]/span/text()')
    if supply_mode != []:
        supply_mode = supply_mode[0].split()[0]
    else:
        supply_mode = ''
    percent = sellinfo.xpath('div[@class="detail"]/div[@class="smt_supplier_bsr"]/div/a/div/div[4]/div/span[2]/text()')
    if percent != []:
        percent = percent[0]
    else:
        percent = '0'
else:
    sellinfo = response.xpath('//div[@class="info"]/div[@class="content"]')[0]
    sell_verify = sellinfo.xpath('div[@class="abstract"]/div[@class="certify-info"]')[
        0].xpath('string(.)').split()
    trade_medal = sellinfo.xpath('div[@class="detail"]/div[@class="detail-trade"]/div/dl/dd/a/@title')
    if trade_medal != []:
        trade_medal = trade_medal[0]
    else:
        trade_medal = ''
    supply_mode = sellinfo.xpath('div[@class="detail"]/div[@class="smt-biz-type"]/span/text()')
    if supply_mode != []:
        supply_mode = supply_mode[0].split()[0]
    else:
        supply_mode = ''
    percent = sellinfo.xpath('div[@class="detail"]/div[@class="smt_supplier_bsr"]/div/a/div/div[4]/div/span[2]/text()')
    if percent != []:
        percent = percent[0]
    else:
        percent = '0'
if int(percent.strip('%')) > 10:
    print(percent)
trade_medal_num = re.findall(r"(?<=勋章-)(.*?)(?=级)", trade_medal)
if trade_medal_num != []:
    trade_medal_num = len(trade_medal_num[0])
else:
    trade_medal_num = 0
seller_info['卖家名称'] = companyName
seller_info['卖家资质'] = sell_verify
if re.findall(r"\d", sell_verify[0]) != []:
    print(re.findall(r"\d", sell_verify[0])[0])
print(sell_verify[1:])
seller_info['交易勋章'] = trade_medal
if re.findall(r"(?<=勋章-)(.*?)(?=级)", trade_medal) != []:
    print(re.findall(r"(?<=勋章-)(.*?)(?=级)", trade_medal))
seller_info['经营模式'] = supply_mode
seller_info['所在地区'] = location
seller_info['回头率'] = percent
# 详细信息、克重
detail_info = ''
kezhong = ''
detail = json_obj['productFeatureList']
for i in detail:
    if i['name'] == '克重':
        kezhong = i['value']
detail_list = [''.join(detail1['name']+':'+detail1['value']) for detail1 in detail]
detail_info += ','.join(detail_list)
print(detail_info)
# 图文
tuwen = ''
if json_obj['detailUrl'].startswith('https:'):
    tuwen_url = json_obj['detailUrl']
    page = requests.get(tuwen_url, headers=headers)
    html = re.findall("(?<=desc=')(.*?)(?=';)", page.text)[0]
    response = etree.HTML(html)
    lis = [i.xpath('string(.)').split()[0] for i in response.xpath('//p') if i.xpath('string(.)').split() != []]
    tuwen += ','.join(lis)
    tuwen_image_list = [i.strip('\\"') for i in response.xpath('//img/@src') if
                        i.strip('\\"').startswith('https://cbu01.alicdn.com')]
    tuwen += ' '.join(tuwen_image_list)
else:
    tuwen_url = 'https:' + json_obj['detailUrl']
    page = requests.get(tuwen_url, headers=headers)
    html = re.findall('(?<="content":")(.*?)(?="};)', page.text)[0]
    response = etree.HTML(html)
    lis = [i.xpath('string(.)').split()[0] for i in response.xpath('//p') if i.xpath('string(.)').split() != []]
    tuwen += ','.join(lis)
    tuwen_image_list = [i.strip('\\"') for i in response.xpath('//img/@src') if i.strip('\\"').startswith('https://cbu01.alicdn.com')]
    tuwen += ' '.join(tuwen_image_list)
print(tuwen_url)
print(tuwen)
# i = 0
# for image_url in imageList+tuwen_image_list:
#     image = requests.get(image_url, headers=headers)
#     path = os.path.join(os.path.dirname(__file__), id)
#     if not os.path.isdir(path):
#         os.makedirs(path)
#     fp = open(path + '/' + str(i) + '.jpg', 'wb')
#     fp.write(image.content)
#     # print position+each
#     fp.close()
#     i += 1
# 计算分数
if saledCount == 0 or int(trade_medal_num)<2 or int(percent.strip('%'))<10:
    score = 0
else:
    score = (int(trade_medal_num)/5) * (100*0.5) + (int(percent.strip('%'))/100) * (100*0.5)
print(score)

print([id, subjectName, price, begin, guige, canBookCount, saledCount, rateAverageStarLevel, guaranteeLogoList, seller_info])
print(time.time()-now)
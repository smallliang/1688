# -*- coding:utf-8 -*-
import re
import time
import json
import multiprocessing as mp
from multiprocessing import Pool
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
import configparser
import os
from lxml import etree

shop_id = {}
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
    }
chrome_path = os.path.join(os.path.dirname(__file__), 'chromedriver')
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
# 读取配置文件
cf = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'spider.cfg')
cf.read(config_path, encoding="utf-8-sig")
class_name = cf.get("class", "class_name")
trade_num = int(cf.get("class", "trade_num"))
percent_limit = int(cf.get("class", "percent_limit"))
A1 = float(cf.get("class", "A1"))
A2 = float(cf.get("class", "A2"))
score_limit = int(cf.get("class", "score_limit"))


def isElementExist(driver, element):
    flag = True
    browser = driver
    try:
        browser.find_element_by_class_name(element)
        return flag

    except:
        flag = False
        return flag

def get_detail_urls(title, q):
    driver = webdriver.Chrome(executable_path=chrome_path, chrome_options=chrome_options)
    start = 'https://m.1688.com/offer_search/-20B7F0C9BDCAD0C5B7B8F3CBB9BCD2BEDFD3D0CFDEB9ABCBBE.html?' \
            'sortType=pop&keywords=' + title
    try:
        driver.get(start)
        time.sleep(3)
        divs_len = 0
        close_ele_name = 'call-app-colse'
        if isElementExist(driver, close_ele_name):
            driver.find_element_by_class_name(close_ele_name).find_element_by_xpath('img').click()
        new_divs = driver.find_elements_by_xpath('//div[@id="list-main"]/div')
        if len(new_divs) > divs_len:
            for div in new_divs[divs_len:]:
                id = div.get_attribute('data-offer-id')
                if id not in shop_id:
                    shop_id[id] = 1
                    q.put((id, title))
                    print(q.qsize())
        for i in range(8):
            js = "var q=document.documentElement.scrollTop=50000"
            driver.execute_script(js)
            time.sleep(1)
            new_divs = driver.find_elements_by_xpath('//div[@id="list-main"]/div')
            if len(new_divs) > divs_len:
                for div in new_divs[divs_len:]:
                    try:
                        id = div.get_attribute('data-offer-id')
                        if id not in shop_id:
                            shop_id[id] = 1
                            q.put((id, title))
                            print(q.qsize())
                    except:
                        pass
            divs_len = len(new_divs)
        for i in range(95):
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//div[@class="list-loadmore"]'))
            )
            ele = driver.find_element_by_xpath('//div[@class="list-loadmore"]')
            webdriver.ActionChains(driver).move_to_element(ele).click().perform()
            time.sleep(1)
            new_divs = driver.find_elements_by_xpath('//div[@id="list-main"]/div')
            if len(new_divs) > divs_len:
                for div in new_divs[divs_len:]:
                    try:
                        id = div.get_attribute('data-offer-id')
                        if id not in shop_id:
                            shop_id[id] = 1
                            q.put((id, title))
                            print(q.qsize())
                    except:
                        pass
            divs_len = len(new_divs)

        # print(divs_len)
        driver.quit()
    except Exception as e:
        print(e)

def crawl(queue_get):

    (id, title) = queue_get
    try:
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
        guaranteeLogoList = [i['serviceName'] for i in
                             json_obj['guaranteeLogoList']] if 'guaranteeLogoList' in json_obj else []
        if '48小时发货' in guaranteeLogoList:
            fahuo = '是'
        else:
            fahuo = '否'
        if '15天包换' in guaranteeLogoList:
            baohuan = '是'
        else:
            baohuan = '否'
        if '8天无理由包退（仅向淘货源买家提供）' in guaranteeLogoList:
            baotui = '是'
        else:
            baotui = '否'
        if '材质保障' in guaranteeLogoList:
            caizhi = '是'
        else:
            caizhi = '否'
        if '交期保障' in guaranteeLogoList:
            jiaoqi = '是'
        else:
            jiaoqi = '否'
        if '破损补寄' in guaranteeLogoList:
            posun = '是'
        else:
            posun = '否'
        if '免费赊账' in guaranteeLogoList:
            shezhang = '是'
        else:
            shezhang = '否'
        maijia = '是'

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
        # rateAverageStarLevel = json_obj['rateAverageStarLevel']
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
        sellinfo = response.xpath('//div[@class="supplierinfo-common"]/div[@class="content"]')
        if sellinfo:
            sellinfo = sellinfo[0]
            sell_verify = sellinfo.xpath('div[1]/div[@class="certify-info"]')[
                0].xpath('string(.)').split()
            trade_medal = sellinfo.xpath(
                'div[@class="detail"]/div[@class="item trade-medal fd-clr  trade-medal-container "]/div')
            if trade_medal != []:
                trade_medal = trade_medal[0].xpath('string(.)').split()[0]
            else:
                trade_medal = ''
            supply_mode = sellinfo.xpath('div[@class="detail"]/div[@class="item biz-type fd-clr"]/span/text()')
            if supply_mode != []:
                supply_mode = supply_mode[0]
            else:
                supply_mode = ''
            percent = sellinfo.xpath(
                'div[@class="detail"]/div[@class="common_supplier_bsr"]/div/a/div/div[4]/div/span[2]/text()')
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
            percent = sellinfo.xpath(
                'div[@class="detail"]/div[@class="smt_supplier_bsr"]/div/a/div/div[4]/div/span[2]/text()')
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
            percent = sellinfo.xpath(
                'div[@class="detail"]/div[@class="smt_supplier_bsr"]/div/a/div/div[4]/div/span[2]/text()')
            if percent != []:
                percent = percent[0]
            else:
                percent = '0'
        trade_medal_num = re.findall(r"(?<=勋章-)(.*?)(?=级)", trade_medal)
        if trade_medal_num != []:
            trade_medal_num = len(trade_medal_num[0])
        else:
            trade_medal_num = 0
        # if int(percent.strip('%')) > 10:
        #     isPercent = '是'
        # else:
        #     isPercent = '否'
        # 联系方式
        contact = response.xpath('//div[@class="mod mod-contactSmall app-contactSmall        "]')
        if contact != []:
            contact = [' '.join(i.xpath('string(.)').split()) for i in
                       contact[0].xpath('div[@class="m-body"]/div[@class="m-content"]/dl')]
            contact = ','.join(contact)
        else:
            contact = ''
        if '质量保障' in sell_verify or '质量保证' in sell_verify:
            zhiliang = '是'
        else:
            zhiliang = '否'
        if '发货保障' in sell_verify:
            fahuobaozhang = '是'
        else:
            fahuobaozhang = '否'
        if '换货保障' in sell_verify:
            huanhuo = '是'
        else:
            huanhuo = '否'
        if '深度验厂' in sell_verify:
            shendu = '是'
        else:
            shendu = '否'
        if '企业身份认证' in sell_verify:
            qiye = '是'
        else:
            qiye = '否'
        chengxin = sell_verify[0]
        # seller_info['卖家资质'] = sell_verify
        # seller_info['供应等级'] = trade_medal
        # seller_info['经营模式'] = supply_mode
        # seller_info['所在地区'] = location
        # seller_info['回头率'] = percent
        # 详细信息、克重
        detail_info = ''
        kezhong = ''
        detail = json_obj['productFeatureList']
        for i in detail:
            if i['name'] == '克重' or i['name'] == '重量':
                kezhong = i['value']
        detail_list = [''.join(detail1['name'] + ':' + detail1['value']) for detail1 in detail]
        detail_info += ','.join(detail_list)
        # 图文
        tuwen = ''
        if json_obj['detailUrl'].startswith('https:'):
            tuwen_url = json_obj['detailUrl']
            page = requests.get(tuwen_url, headers=headers)
            html = re.findall("(?<=desc=')(.*?)(?=';)", page.text)[0]
            response = etree.HTML(html)
            lis = [i.xpath('string(.)').split()[0] for i in response.xpath('//span') if i.xpath('string(.)').split() != []]
            tuwen += ','.join(lis)
            tuwen_image_list = [i.strip('\\"') for i in response.xpath('//img/@src') if
                                i.strip('\\"').startswith('https://cbu01.alicdn.com')]
            tuwen += ' '.join(tuwen_image_list)
        else:
            tuwen_url = 'https:' + json_obj['detailUrl']
            page = requests.get(tuwen_url, headers=headers)
            html = re.findall('(?<="content":")(.*?)(?="};)', page.text)[0]
            response = etree.HTML(html)
            lis = [i.xpath('string(.)').split()[0] for i in response.xpath('//span') if i.xpath('string(.)').split() != []]
            tuwen += ','.join(lis)
            tuwen_image_list = [i.strip('\\"') for i in response.xpath('//img/@src') if
                                i.strip('\\"').startswith('https://cbu01.alicdn.com')]
            tuwen += ' '.join(tuwen_image_list)
        # for image_url in imageList + tuwen_image_list:
        #     image = requests.get(image_url, headers=headers)
        #     path = os.path.join(os.path.dirname(__file__), id)
        #     if not os.path.isdir(path):
        #         os.makedirs(path)
        #     fp = open(path + '/' + str(i) + '.jpg', 'wb')
        #     fp.write(image.content)
        #     # print position+each
        #     fp.close()
        # 计算分数
        if saledCount == 0 or trade_medal_num < 2 or int(percent.strip('%')) < percent_limit:
            score = 0
        else:
            score = (trade_medal_num/5) * (100*A1) + (int(percent.strip('%'))/100) * (100*A2)
        if score > score_limit:
            print('正在下载%s图片' % id)
            i = 0
            for image_url in imageList + tuwen_image_list:
                image = requests.get(image_url, headers=headers)
                dir_path = os.path.join(os.path.dirname(__file__), title)
                if not os.path.isdir(dir_path):
                    os.makedirs(dir_path)
                file_path = subjectName + '/' + id
                file_path = os.path.join(os.path.dirname(__file__), file_path)
                if not os.path.isdir(file_path):
                    os.makedirs(file_path)
                fp = open(file_path + '/' + str(i) + '.jpg', 'wb')
                fp.write(image.content)
                # print position+each
                fp.close()
                i += 1
        # 商品序号
        shopNum = class_name + '.' + title + '.' + id
                  # ("00000%s" % str(count))[-6:]
        return [title, shopNum, subjectName, url, detail_info, tuwen, kezhong, price, begin, guige, canBookCount,
                saledCount, fahuo, baohuan, maijia, baotui, caizhi, jiaoqi, posun, shezhang, companyName,
                str(trade_medal_num), percent, zhiliang, fahuobaozhang, huanhuo, shendu, qiye, chengxin, supply_mode,
                location, contact, str(score)]


    except Exception as e:
        print(id, e)



def mycallback(x):
    # print(x)
    if x != None:
        csv_write.writerow(x)


if __name__=='__main__':
    mp.freeze_support()
    manager = mp.Manager()
    q = manager.Queue()
    # 创建多进程公用队列






    driver = webdriver.Chrome(executable_path=chrome_path, chrome_options=chrome_options)
    now = time.time()
    driver.get("https://www.1688.com")
    element = WebDriverWait(driver, 10).until(
          EC.presence_of_element_located((By.ID, 'j-identity'))
          )
    element.find_element_by_xpath('div/div[2]/div[3]').click()

    # 搜索大类
    driver.find_element_by_xpath('//*[@id="alisearch-keywords"]').send_keys(class_name)
    driver.find_element_by_xpath('//*[@id="alisearch-submit"]').click()
    # 按小类继续搜索
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@class="s-widget-flatcat sm-widget-row sm-sn-items-control sm-sn-items-count-d fd-clr"]/div'))
    )
    classes = driver.find_elements_by_xpath('//div[@class="s-widget-flatcat sm-widget-row sm-sn-items-control sm-sn-items-count-d fd-clr"]/div')
    lis = classes[-1].find_elements_by_xpath('ul/li')
    class_list = []
    for li in lis:
        title = li.find_element_by_xpath('a').get_attribute('title').split('/')[0]
        class_list.append(title)
    related_classes = driver.find_elements_by_xpath('//div[@class="s-widget-related"]/div')
    lis = related_classes[-1].find_elements_by_xpath('ul/li')
    for li in lis:
        title = li.find_element_by_xpath('a').get_attribute('title').split('/')[0]
        class_list.append(title)
    print(len(class_list), '个小类')
    driver.quit()

    # test()
    cpu_count = mp.cpu_count()
    print(class_list)
    for i in range(0, len(class_list), cpu_count):
        # 开启多进程
        # 先爬小类中的链接
        # 创建csv文件
        file_name = '%s.csv' % (class_name+'-'+','.join(class_list[i:i+cpu_count]))
        csv_file = codecs.open(file_name, 'w+', 'utf_8_sig')
        csv_write = csv.writer(csv_file)
        csv_write.writerow(['小类名称', '序号', '商品名称', '商品链接', '详细信息', '商品描述', '克重', '现货价格',
                            '最小起批量', '规格/型号', '可售数量(>5)', '30天成交数量', '48小时发货', '15天包换', '买家保障',
                            '8天无理由包退（仅向淘货源买家提供）', '材质保障', '交期保障', '破损补寄', '免费赊账', '商家名称',
                            '交易勋章', '回头率', '质量保障', '发货保障', '换货保障', '深度验厂', '企业身份认证',
                            '诚信', '经营模式', '所在地区', '联系方式', '分数'])
        pool1 = Pool(processes=cpu_count)
        for j in class_list[i:i+cpu_count]:
            pool1.apply_async(get_detail_urls, args=(j, q,))
        # pool1.map_async(func=get_detail_urls, iterable=class_list[i:i + cpu_count])
        pool1.close()
        pool1.join()
        #     get_detail_urls(class_list[i])
        # 再爬具体信息
        print('正在爬取：%s' % ','.join(class_list[i:i + cpu_count]))
        pool2 = Pool(processes=cpu_count)
        while not q.empty():
            pool2.apply_async(crawl, args=(q.get(),), callback=mycallback)
        pool2.close()
        pool2.join()

        csv_file.close()
    print(time.time()-now)


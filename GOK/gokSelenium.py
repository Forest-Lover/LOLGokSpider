from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

import socket
import urllib.error
import datetime
import ast
import sys
sys.path.append('../')
from Config import gok_config

import time
import requests
from GOK.gokClass import GokClass
from GOK.gokMongoClient import gok_save_to_mongo

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_experimental_option('excludeSwitches',
                                       ['enable-automation'])
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)
browser = webdriver.Chrome('/home/sunny/wx/LOLGokEnv/chromedriver', chrome_options=chrome_options)

hero_list = []
hero_url_list = []
wait = WebDriverWait(browser, 10)
gok_version = ''


def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").text


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


def get_all_url():
    try_num = 3

    proxy = get_proxy()
    chrome_options.add_argument('--proxy-server=http://' + proxy)

    browser.get("https://pvp.qq.com/web201605/herolist.shtml")

    while try_num > 0:
        try:
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                'body > div.wrapper > div > div > div.herolist-box > div.herolist-content > ul > li:nth-child(1) > a')))
            all_hero_items = browser.find_elements_by_css_selector(
                'body > div.wrapper > div > div > div.herolist-box > div.herolist-content > ul > li')
            for hero_item in all_hero_items:
                hero_url = hero_item.find_element_by_tag_name('a').get_attribute('href')
                hero_url_list.append(hero_url)
                print(hero_url)

            browser.get("https://pvp.qq.com/cp/a20170829bbgxsm/index.html")
            gok_version = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                'body > div.wrapper > div.container > ul > li:nth-child(1) > div > p'))).text.split(
                '：')[1].replace('.', '-')

            return hero_url_list, gok_version
        except TimeoutException as e:
            print(str(e))
            try_num -= 1
            delete_proxy(proxy)
            proxy = get_proxy()
            chrome_options.add_argument('--proxy-server=http://' + proxy)
            browser.get("https://pvp.qq.com/web201605/herolist.shtml")
    return hero_url_list


def get_one_hero_detail(hero_url, gok_hero):
    proxy = get_proxy()
    chrome_options.add_argument('--proxy-server=http://' + proxy)
    browser.get(hero_url)

    tmp1 = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[3]/div[2]/div/div[2]/div[1]/div[2]/p[1]/span'))).text
    tmp2 = browser.find_element_by_xpath('/html/body/div[3]/div[2]/div/div[2]/div[1]/div[2]/p[3]/span').text
    gok_hero.skill = ['主：' + tmp1, '副：' + tmp2]

    zh_skill = browser.find_element_by_xpath('/html/body/div[3]/div[2]/div/div[2]/div[1]/div[2]/p[5]/span').text
    gok_hero.zh_skill = zh_skill

    mingwen1 = browser.find_element_by_xpath('/html/body/div[3]/div[2]/div/div[1]/div[3]/div[2]/ul/li[1]/p[1]/em').text
    mingwen2 = browser.find_element_by_xpath('/html/body/div[3]/div[2]/div/div[1]/div[3]/div[2]/ul/li[2]/p[1]/em').text
    mingwen3 = browser.find_element_by_xpath('/html/body/div[3]/div[2]/div/div[1]/div[3]/div[2]/ul/li[3]/p[1]/em').text
    gok_hero.mingwen = [mingwen1, mingwen2, mingwen3]

    browser.implicitly_wait(5)
    builds = browser.find_elements_by_xpath('//*[@id="Jname"]')
    list_tmp = []
    for item in builds:
        list_tmp.append(item.get_attribute("innerHTML"))
    gok_hero.first_build = list_tmp[:6]
    gok_hero.second_build = list_tmp[6:12]

    print(gok_hero.convert_to_dict())
    time.sleep(1)
    return gok_hero


""" --------------------------------------------------------"""

all_hero_msg = []


def get_hero_rank():
    retry_count = 3
    proxy = get_proxy()
    while retry_count > 0:
        try:
            # 获取英雄列表
            proxies = {
                "http": "http://" + proxy
            }
            herohtml = requests.get(
                url=gok_config['HERO_RANK_URL'],
                proxies=proxies).text
            return herohtml
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.timeout):
                print(proxy + ' timeout')
                retry_count -= 1
                if retry_count == 1:
                    # 出错3次, 删除代理池中代理
                    delete_proxy(proxy)
                    proxy = get_proxy()
        except Exception as e:
            print(str(e))
            retry_count -= 1
    return None


def parse_hero_rank(rank_data, version):
    rank_data = ast.literal_eval(rank_data)
    hero_rank_list = str(rank_data.get('Data').get('data'))[1:-1]
    hero_items = ast.literal_eval(hero_rank_list)
    for item in hero_items:
        gok = GokClass()
        # gok.version = gok_config['GOK_VERSION']
        gok.version = version
        gok.day = datetime.datetime.now().strftime('%Y-%m-%d')
        gok.heroid = item['heroid']
        gok.heroname = item['heroname']
        gok.herotype = item['herotype']
        gok.herotypename = item['herotypename']
        gok.winpercent = item['winpercent']
        gok.gameactpercnt = item['gameactpercnt']
        gok.mvppercnt = item['mvppercnt']
        gok.kda = item['kda']
        all_hero_msg.append(gok)


def get_hero_smobahelper(hero_id):
    retry_count = 3
    proxy = get_proxy()
    while retry_count > 0:
        try:
            url = gok_config['HERO_Smobahelper'] + 'heroId=' + hero_id + '&version=' + gok_config['GOK_VERSION']
            # 获取英雄列表
            proxies = {
                "http": "http://" + proxy
            }
            hero_smobahelper = requests.get(
                url=url,
                proxies=proxies).text
            return hero_smobahelper
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.timeout):
                print(proxy + ' timeout')
                retry_count -= 1
                if retry_count == 1:
                    # 出错3次, 删除代理池中代理
                    delete_proxy(proxy)
                    proxy = get_proxy()
        except Exception as e:
            print(str(e))
            retry_count -= 1
    return None


def parse_hero_rank_smobahelper(hero_smobahelper, hero_tmp):
    rank_smobahelper = ast.literal_eval(hero_smobahelper)
    hero_smobahelper_list = rank_smobahelper.get('Data')
    items = hero_smobahelper_list.get('strongEnemy')
    list_tmp = []
    for item in items:
        list_tmp.append(item)
    hero_tmp.strongEnemy = list_tmp

    list_tmp = []
    items = hero_smobahelper_list.get('defeat')
    for item in items:
        list_tmp.append(item)
    hero_tmp.defeat = list_tmp

    list_tmp = []
    items = hero_smobahelper_list.get('victory')
    for item in items:
        list_tmp.append(item)
    hero_tmp.victory = list_tmp
    return hero_tmp


def main():
    hero_url_list, version = get_all_url()
    hero_rank = get_hero_rank()
    parse_hero_rank(hero_rank, version)
    i = 0
    for item in all_hero_msg:
        hero_smobahelper = get_hero_smobahelper(item.heroid)
        hero_smobahelper_new = parse_hero_rank_smobahelper(hero_smobahelper, item)
        new_hero = get_one_hero_detail(hero_url_list[i], hero_smobahelper_new)
        gok_save_to_mongo(new_hero)
        i += 1

    browser.close()


if __name__ == '__main__':
    main()
    browser.close()
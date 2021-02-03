#!/usr/bin/env python

# -*- coding:utf-8 -*-
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 确保无头
options.add_argument('--disable-gpu')  # 无需要gpu加速
options.add_argument('--no-sandbox')  # 无沙箱
driver = webdriver.Chrome(executable_path="./chromedriver", chrome_options=options)  # 添加软链接后是不需要写路径的

driver.get("https://www.baidu.com")
print(driver.page_source)
driver.quit()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/19 22:39
# @Author  : caoxiang
# @File    : search_tools.py
# @Description  : 爬虫和搜索相关的函数
import requests
from lxml import etree
import tiktoken
import openai
from util.chat_tools import cut_by_token


def get_search_content(url, model="gpt-4o", token_limit=4096):
    # TODO 改为动态获取cookie方式，如cookiejar
    cookie = 'SESSIONID=mocjbJY9RHsFgHmfv7sQddCCbWgVGGjrMv969aag8Ec; JOID=UFEVBkumDH5NkVRTeqHlJjAuDj9gjiZYa7B8eVyHJFRrt3V7ULoKNCyYVl96u72gch2wUuHyIduR1TVgDb8UpvQ=; osd=V1EcBEKhDHdPmFNTc6PsITAnDDZnji9aYrd8cF6OI1RitXx8ULMIPSuYX11zvL2pcBS3UujwKNyR3DdpCr8dpP0=; _zap=dde3224e-3fcd-47f3-a08a-68b2672d52bf; d_c0=AHDWbSa6FhiPTqvFbznrTe8i6KF1km5uaog=|1706622053; __snaker__id=zzngQdqP5NmL3apK; q_c1=baee8a8673824034b31038dd2d53e353|1708433550000|1708433550000; z_c0=2|1:0|10:1715782986|4:z_c0|80:MS4xXzFTY0F3QUFBQUFtQUFBQVlBSlZUWDZiSkdkdTVvWjJEWlJCTzZqcXc2dF9kYm9qVk5MSnhnPT0=|f97dcac3a25a79f90f6644cc34097523ec462e920eaba9d2717283c2b8039f7e; _xsrf=abf80057-592d-43b5-9057-2c1f5b91c6b1; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1715325516,1715782084,1715782985,1716128284; Hm_lpvt_98beee57fd2ef70ccdd5ca52b9740c49=1716128284; BEC=5b38c4d5f0c2e09ceae9a4f725f48e8f; KLBRSID=37f2e85292ebb2c2ef70f1d8e39c2b34|1716128286|1716128283'
    headers = {
        'authority': 'www.zhihu.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'cookie': cookie,  # 需要手动获取cookie
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        # 手动编写或者选择之后给出的user-agent选项选择其一填写
    }

    code_ = False
    text_d = None
    # 普通问答地址
    if 'zhihu.com/question' in url:
        res = requests.get(url, headers=headers).text
        res_xpath = etree.HTML(res)
        title = res_xpath.xpath('//div/div[1]/div/h1/text()')[0]
        text_d = res_xpath.xpath('//div/div/div/div[2]/div/div[2]/div/div/div[2]/span[1]/div/div/span/p/text()')

    # 专栏地址
    elif 'zhuanlan' in url:
        headers['authority'] = 'zhaunlan.zhihu.com'
        res = requests.get(url, headers=headers).text
        res_xpath = etree.HTML(res)
        title = res_xpath.xpath('//div[1]/div/main/div/article/header/h1/text()')[0]
        text_d = res_xpath.xpath('//div/main/div/article/div[1]/div/div/div/p/text()')
        code_ = res_xpath.xpath('//div/main/div/article/div[1]/div/div/div//pre/code/text()')

        # 特定回答的问答网址
    elif 'answer' in url:
        res = requests.get(url, headers=headers).text
        res_xpath = etree.HTML(res)
        title = res_xpath.xpath('//div/div[1]/div/h1/text()')[0]
        text_d = res_xpath.xpath('//div[1]/div/div[3]/div/div/div/div[2]/span[1]/div/div/span/p/text()')

    # 创建问题答案正文
    text = ''
    for t in text_d:
        txt = str(t).replace('\n', ' ')
        text += txt
    text = cut_by_token(text, model, token_limit=token_limit)
    # 如果有code，则将code追加到正文的追后面
    if code_:
        for c in code_:
            co = str(c).replace('\n', ' ')
            text += co

    return text




#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/5 13:08
# @Author  : 作者名
# @File    : test.py
# @Description  :
from brain.base_func import *
from brain.outer_func import *
from openai import OpenAI
import os
from config.conf_loader import YamlConfigLoader
from util.chat_tools import auto_functions, run_conversation
from brain import outer_func as func
import inspect
from lxml import etree

def chat_with_model(
        client=None,
        functions_list=None,
        prompt="你好呀",
        model="gpt-4-turbo-preview",
        system_message=[{"role": "system", "content": get_base_info()}]):
    messages = system_message
    messages.append({"role": "user", "content": prompt})

    while True:
        #print(messages)
        answer = run_conversation(client=client,
                                  messages=messages,
                                  functions_list=functions_list,
                                  model=model)

        print(f"牛牛精灵: {answer}")
        messages.append({"role": "assistant", "content": answer})

        # 询问用户是否还有其他问题
        user_input = input("您还有其他问题吗？(输入退出以结束对话): ")
        if user_input == "退出":
            break

        # 记录用户回答
        messages.append({"role": "user", "content": user_input})


if __name__ == '__main__':
    conf_loader = YamlConfigLoader(yaml_path="config/config.yaml")
    os.environ["OPENAI_API_KEY"] = conf_loader.attempt_load_param("api-key")
    os.environ["OPEN_WEATHER_API_KEY"] = conf_loader.attempt_load_param("open-weather-api-key")
    # 初始化openai大脑
    client = OpenAI()
    function_list = [globals()[i[0]] for i in inspect.getmembers(func, inspect.isfunction)]
    chat_with_model(client=client, functions_list=function_list, prompt="你好呀", model="gpt-4o")


    #import requests

    # Step 1.构建请求
    # url = "https://www.googleapis.com/customsearch/v1"
    # google_search_key = conf_loader.attempt_load_param("google-search-api-key")
    # cse_id = conf_loader.attempt_load_param("google-search-cse-id")
    # # Step 2.设置查询参数
    # params = {
    #     'q': "OpenAI",           # 搜索关键词
    #     'key': google_search_key,   # 谷歌搜索API Key
    #     'cx': cse_id                # CSE ID
    # }
    #
    # # Step 3.发送GET请求
    # response = requests.get(url, params=params)
    #
    # # Step 4.解析响应
    # data = response.json()
    # print(data)
    from duckduckgo_search import DDGS

    # with DDGS(proxies="http://localhost:7890", timeout=20) as ddgs:
    #     results = [r for r in ddgs.text("python site:www.zhihu.com", max_results=5)]
    #     print(results[-1])
    # headers = {
    #     'authority': 'www.zhihu.com',
    #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    #     'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    #     'cache-control': 'max-age=0',
    #     'cookie': "Your cookie",  # 需要手动获取cookie
    #     'upgrade-insecure-requests': '1',
    #     'user-agent': 'Your user-agent',  # 手动编写或者选择之后给出的user-agent选项选择其一填写
    # }
    # url = 'https://www.zhihu.com/question/589955237'
    # res = requests.get(url, headers=headers).text
    # print(res)
    # res_xpath = etree.HTML(res)




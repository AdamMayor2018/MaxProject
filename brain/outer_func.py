#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/4 21:26
# @Author  : CaoXiang
# @File    : outer_func.py
# @Description  : AI精灵的基本function calling实现
import json
import requests
import os
from lxml import etree
from duckduckgo_search import DDGS
from util.search_tools import get_search_content
def get_weather(loc):
    """
    查询即时天气的函数
    :param loc: 必要参数，字符串类型，用于表示查询天气的具体城市名称， \
    注意，中国的城市需要用对应城市的英文名称代替，例如如果需要查询北京市天气，则loc参数需要输入'Beijing'；
    :return: OpenWeather API查询即时天气的结果，具体URL请求地址为：https://api.openweathermap.org/data/2.5/weather\
    返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部重要的天气信息。
    """
    # Step 1.构建请求
    url = "https://api.openweathermap.org/data/2.5/weather"

    # Step 2.设置查询参数
    params = {
        "q": loc,
        "appid": os.environ["OPEN_WEATHER_API_KEY"],  # 输入API key
        "units": "metric",  # 使用摄氏度而不是华氏度
        "lang": "zh_cn"  # 输出语言为简体中文
    }

    # Step 3.发送GET请求
    response = requests.get(url, params=params)

    # Step 4.解析响应
    data = response.json()
    return json.dumps(data)


def get_latest_news():
    """
    获取微博热搜榜的函数
    @return: 返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部的微博热榜信息。
    """
    url = "https://api.zlinblog.cn/single/rank"
    params = {
        "platform": "微博",
        "rank_name": "热搜"
    }
    headers = {
        "User-Agent": "PostmanRuntime/7.29.0",
        "X-Licence": "ROJ8tVE1sTRIj0BB1702183754479cd3118c1197ecNhLQleSe6004dd4bc9a386"
    }
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    return json.dumps(data)

def search_internet(query):
    """
    搜索互联网的函数，当你无法回答某个问题时，调用该函数，能够获得答案。
    @param query: 必要参数，字符串类型，用于表示搜索的查询的搜索词，注意，该语句需要符合互联网搜索的语法规则。
    @return: 返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了搜索结果。
    """
    print(f"牛牛精灵: 还没学过这个，稍等我去查查...")
    with DDGS(proxy="http://localhost:7890", timeout=20) as ddgs:
        results = [r for r in ddgs.text(f"{query}:www.zhihu.com", max_results=5)]
        for r in results:
            url = r["href"]
            r['content'] = get_search_content(url)
        #print("query:", results)
        return json.dumps(results)




if __name__ == '__main__':
    #print(get_latest_news())
    print(search_internet("2024歌手比赛"))
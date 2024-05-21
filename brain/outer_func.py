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
from util.chat_tools import cut_by_token, convert_keyword
import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email
from email.header import decode_header
import re
import quopri
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


def search_internet(query, model="gpt-4o", token_limit=4096):
    """
    搜索互联网的函数，当你无法回答某个问题时，调用该函数，能够获得答案。
    @param query: 必要参数，字符串类型，用于表示搜索的查询的搜索词，注意，该语句需要符合互联网搜索的语法规则。
    @param model: 可选参数，字符串类型，用于表示使用的模型名称，默认为"gpt-4o"。
    @param token_limit: 可选参数，整数类型，用于表示互联网搜索结果限制返回的最大token数，默认为4096。
    @return: 返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了搜索结果。
    """

    print(f"牛牛精灵: 还没学过这个，稍等我去查查...")
    with DDGS(proxy="http://localhost:7890", timeout=20) as ddgs:
        results = [r for r in ddgs.text(f"{query}:www.zhihu.com", max_results=5)]
        for r in results:
            url = r["href"]
            content = get_search_content(url, model, token_limit=token_limit)
            r['content'] = content
        # print("query:", results)
        return json.dumps(results)


def send_email(subject, content, receiver_email):
    """
    需要发送邮件的时候调用该函数
    @param subject: 必要参数，字符串类型，用于表示邮件主题，注意，该语句需要符合邮件主题的语法规则。
    @param content: 必要参数，字符串类型，用于表示邮件正文，注意，该语句需要符合邮件正文的语法规则。
    @param receiver_email: 必要参数，字符串类型，用于表示邮件接收者的邮箱地址，注意，该语句需要符合邮件接收者的邮箱地址的语法规则。
    @return: 返回字符串，表明了邮件是否发送成功。
    """
    # 邮件发送者和接收者
    sender_email = "1224325287@qq.com"
    #receiver_email = "caoxiang@yangshipin.cn"
    password = os.environ["QQ_MAIL_KEY"]  # 此处输入你的授权码
    print(password)

    # 创建邮件对象和设置邮件内容
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    # 创建邮件正文
    # 添加文本和HTML的部分
    part1 = MIMEText(content, "plain")

    # 添加正文到邮件对象中
    message.attach(part1)

    # 发送邮件
    try:
        # QQ邮箱的SMTP服务器地址
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        info ="邮件发送成功"
    except Exception as e:
        print(f"邮件发送失败: {e}")
        info = f"邮件发送失败： 错误的原因是： {e}"
    finally:
        server.quit()
        return info

def get_email(num=1, type="All"):
    """
    @param num: 必要参数，整数类型，用于表示查询邮件的个数，注意，该语句需要符合邮件主题的语法规则。如果没有明确表示的话，默认查询最新的1封邮件。
    需要查询邮件信息的时候调用该函数
    @param type: 必要参数，字符串类型，用于表示查询邮件的类型，默认为All,代表全部的邮件。如果指定是未读邮件，则为UnSeen。
    需要查询邮件信息的时候调用该函数
    @return: 返回json字符串，表明了查询到的若干封邮件信息。
    """
    # 创建 IMAP4 对象并连接到邮件服务器
    mail = imaplib.IMAP4_SSL("smtp.qq.com")
    email_address = "1224325287@qq.com"
    password = os.environ["QQ_MAIL_KEY"]
    # 登录到邮件服务器
    mail.login(email_address, password)
    # 选择邮件目录
    mail.select('inbox')
    # 搜索邮件
    print("type:", type)
    status, messages = mail.search(None, type)
    # 获取邮件列表
    ids = messages[0]
    id_list = ids.split()
    # 获取最新的邮件
    wanted_ids = id_list[-num:]
    messages = []
    for email_id in wanted_ids:
        # 获取邮件的详细信息
        status, email_data = mail.fetch(email_id, '(RFC822)')
        # 解码邮件
        raw_message = email_data[0][1]
        # 解析邮件数据
        email_message = email.message_from_bytes(raw_message)
        # 获取主题
        msgCharset = email.header.decode_header(email_message.get('Subject'))[0][1]  # 获取邮件标题并进行进行解码，通过返回的元组的第一个元素我们得知消息的编码
        subject = decode_header(email_message["Subject"])[0][0].decode(msgCharset)
        #获取日期
        date = decode_header(email_message["Date"])[0][0]
        # 获取发件人
        from_address = decode_header(email_message["From"])[0][0].decode(msgCharset)
        # 获取收件人
        to_address = decode_header(email_message["To"])[0][0]
        # 获取邮件正文
        for part in email_message.walk():
            if not part.is_multipart():
                name = part.get_param("name")
                if not name:  # 如果邮件内容不是附件可以打印输出
                    content = part.get_payload(decode=True).decode(msgCharset)
        message = {"subject": subject, "date": date, "from": from_address, "to": to_address, "content": content}
        messages.append(message)
    # 关闭连接
    mail.close()
    mail.logout()

    return json.dumps(messages)

if __name__ == '__main__':
    #send_email("测试邮件", "测试邮件内容")
    #print(get_latest_news())
    # print(search_internet("2024歌手比赛"))
    print(get_email(2))


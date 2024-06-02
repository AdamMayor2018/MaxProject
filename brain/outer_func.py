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
from docx import Document
from pathlib import Path


def get_weather(loc):
    """
    查询即时天气的函数
    @param loc: 必要参数，字符串类型，用于表示查询天气的具体城市名称， \
    注意，中国的城市需要用对应城市的英文名称代替，例如如果需要查询北京市天气，则loc参数需要输入'Beijing'；
    @return: OpenWeather API查询即时天气的结果，具体URL请求地址为：https://api.openweathermap.org/data/2.5/weather\
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
    需要发送邮件的时候调用该函数，该函数使用QQ邮箱的SMTP服务进行邮件处理。
    @param subject: 必要参数，字符串类型，用于表示邮件主题，注意，该语句需要符合邮件主题的语法规则。
    @param content: 必要参数，字符串类型，用于表示邮件正文，注意，该语句需要符合邮件正文的语法规则。
    @param receiver_email: 必要参数，字符串类型，用于表示邮件接收者的邮箱地址，注意，该语句需要符合邮件接收者的邮箱地址的语法规则。
    @return: 返回字符串，表明了邮件是否发送成功。
    """
    # 邮件发送者和接收者
    sender_email = os.environ["QQ_EMAIL_ADDRESS"]
    # receiver_email = "caoxiang@yangshipin.cn"
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
        info = "邮件发送成功"
    except Exception as e:
        print(f"邮件发送失败: {e}")
        info = f"邮件发送失败： 错误的原因是： {e}"
    finally:
        server.quit()
        return info


def get_latest_mail(from_address, type='Unseen'):
    """
    该函数用于查询邮箱中是否有来自指定发件人的未读邮件，并解读最近一封未读邮件的内容。
    @param from_address: 必要参数，字符串类型，发件方的邮箱地址。
    @param type: 字符串类型，查询的类型，包含All或者Unseen两类，默认为All代表全部的邮件，Unseen代表的是未读邮件。
    @return: json格式对象，包含查询邮件的状态和最近一封未读邮件的内容。
    """

    # 从环境变量中获取邮箱地址和授权码
    email_address = os.getenv('QQ_EMAIL_ADDRESS')
    email_password = os.getenv('QQ_MAIL_KEY')

    # 连接到QQ邮箱的IMAP服务器
    imap_host = 'imap.qq.com'
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(email_address, email_password)

    # 选择收件箱
    mail.select('inbox')

    # 根据查询类型设置搜索条件
    search_criteria = 'ALL'
    if type == 'Unseen':
        search_criteria = 'UNSEEN'

    # 搜索符合条件的邮件
    status, messages = mail.search(None, f'(FROM "{from_address}" {search_criteria})')

    # 获取邮件ID列表
    mail_ids = messages[0].split()

    result = {
        'status': 'No new emails',
        'recent_email': None
    }

    if mail_ids:
        # 取出最新的一封邮件ID
        recent_mail_id = mail_ids[-1]

        # 获取邮件数据
        status, data = mail.fetch(recent_mail_id, '(RFC822)')

        # 解析邮件内容
        msg = email.message_from_bytes(data[0][1])
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding)

        from_ = msg.get('From')

        # 如果邮件是multipart类型
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                try:
                    body = part.get_payload(decode=True).decode()
                except:
                    pass
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    result['status'] = 'Unread email found'
                    result['recent_email'] = {
                        'from': from_,
                        'subject': subject,
                        'body': body
                    }
                    break
        else:
            content_type = msg.get_content_type()
            body = msg.get_payload(decode=True).decode()
            if content_type == "text/plain":
                result['status'] = 'Unread email found'
                result['recent_email'] = {
                    'from': from_,
                    'subject': subject,
                    'body': body
                }

    mail.logout()

    return json.dumps(result, ensure_ascii=False)


def read_docx(file_path: str):
    """
    需要读取外部文档信息的时候调用该函数
    @param file_path: 必要参数，字符串类型，用于表示本地文档的路径
    @return: 返回字符串，表示提取到的文档信息，如果顺利读取则返回文档信息，如果发生错误，则返回错误提示。
    """
    # 加载Word文档
    try:
        print(f"牛牛精灵: 正在尝试读取本地文档：{file_path}...")
        doc = Document(str(Path(file_path)))
    except:
        text = "提供的本地地址错误，请检查！"
        return text
    # 提取文档文本内容
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return '\n'.join(text)

def tarot_predict():
    """
    使用塔罗牌进行每日占卜的函数
    @return: 返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部的占卜信息。
    """
    url = "https://api.yuanfenju.com/index.php/v1/Zhanbu/meiri"
    params = {
        "api_key": os.environ["TAROT_API_KEY"],
    }
    headers = {
        "User-Agent": "PostmanRuntime/7.29.0",
        "Content-Type": "String"
    }
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    return json.dumps(data)


if __name__ == '__main__':
    # send_email("测试邮件", "测试邮件内容")
    # print(get_latest_news())
    # print(search_internet("2024歌手比赛"))
    # print(get_email(2))
    print(read_docx(r"E:\adamcx\央视频项目\2024年\党员学习\纪律处分条例学习心得\个人学习心得-曹翔.docx"))

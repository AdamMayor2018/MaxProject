#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/6/2 17:45
# @Author  : 作者名
# @File    : send_mail_module.py
# @Description  :
import os
import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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

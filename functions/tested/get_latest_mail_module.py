#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/6/2 17:25
# @Author  : 作者名
# @File    : get_latest_mail_module.py
# @Description  :
import os
import imaplib
import email
from email.header import decode_header
import json


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

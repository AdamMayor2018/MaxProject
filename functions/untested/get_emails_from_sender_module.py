import os
import imaplib
import email
from email.header import decode_header
import json

def get_emails_from_sender(sender_email, type='Unseen'):
    """
    查找并解读发件方邮箱为指定邮箱的邮件

    @param sender_email: 发件方的邮箱
    @param type: 查询邮件的类型，包括All表示全部邮件，Unseen表示未读邮件，默认值为Unseen
    @return: 解析最新的一封邮件内容，返回值是一个包含查询邮件信息的json格式对象
    """
    try:
        # 从环境变量中获取邮箱授权码和邮箱地址
        password = os.getenv('qq-mail-key')
        email_address = os.getenv('qq-email-address')
        
        # 连接到IMAP服务器
        imap = imaplib.IMAP4_SSL("imap.qq.com")
        imap.login(email_address, password)
        
        # 选择邮箱中的收件箱
        if type == 'Unseen':
            status, messages = imap.select("INBOX")
            status, response = imap.search(None, '(UNSEEN FROM "{}")'.format(sender_email))
        else:
            status, messages = imap.select("INBOX")
            status, response = imap.search(None, 'FROM "{}"'.format(sender_email))

        # 获取邮件ID列表并选择最新一封邮件
        messages = response[0].split()
        if not messages:
            return json.dumps({"status": "No new emails from {}".format(sender_email)})

        latest_email_id = messages[-1]
        res, msg = imap.fetch(latest_email_id, "(RFC822)")

        # 解析邮件内容
        for response1 in msg:
            if isinstance(response1, tuple):
                msg = email.message_from_bytes(response1[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')
                from_ = msg.get("From")

                # 如果邮件内容是多部分
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if "attachment" not in content_disposition:
                            # 获取邮件正文
                            email_content = part.get_payload(decode=True).decode()
                else:
                    email_content = msg.get_payload(decode=True).decode()
                
                # 返回解析后的邮件内容
                email_data = {
                    "subject": subject,
                    "from": from_,
                    "content": email_content
                }

                return json.dumps(email_data)

        imap.close()
        imap.logout()

    except Exception as e:
        return json.dumps({"status": "Error", "error": str(e)})

# 示例调用
print(get_emails_from_sender("example@aliyun.com"))

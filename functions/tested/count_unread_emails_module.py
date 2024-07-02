import os
import imaplib
import json


def count_unread_emails(status='UNSEEN'):
    """
    该函数用于统计QQ邮箱中的邮件数量。
    @param status: 必要参数，字符串类型，用于指定统计邮件的类型，‘UNSEEN’表示未读邮件， 'ALL'代表全部邮件；
    @return: json格式对象，包含未读邮件统计信息。
    """
    try:
        # 从环境变量中获取邮箱地址和授权码
        email_address = os.getenv('QQ_EMAIL_ADDRESS')
        email_password = os.getenv('QQ_MAIL_KEY')

        # 连接到QQ邮箱的IMAP服务器
        imap_host = 'imap.qq.com'
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(email_address, email_password)

        # 选择收件箱
        mail.select('inbox')

        # 设置搜索条件，默认为未读邮件
        search_criteria = 'UNSEEN' if status.upper() == 'UNSEEN' else 'ALL'

        # 搜索符合条件的邮件
        status, messages = mail.search(None, f'({search_criteria})')

        # 获取邮件ID列表
        mail_ids = messages[0].split()
        unread_count = len(mail_ids)

        # 登出邮箱
        mail.logout()

        result = {
            'status': 'success',
            'unread_email_count': unread_count
        }
    except Exception as e:
        result = {
            'status': 'fail',
            'error_message': str(e)
        }

    # 返回包含统计信息的json对象
    return json.dumps(result, ensure_ascii=False)


if __name__ == '__main__':
    from config.conf_loader import YamlConfigLoader

    conf_loader = YamlConfigLoader(yaml_path="../../config/config.yaml")
    os.environ["OPENAI_API_KEY"] = conf_loader.attempt_load_param("api-key")
    os.environ["QQ_MAIL_KEY"] = conf_loader.attempt_load_param("qq-mail-key")
    os.environ["QQ_EMAIL_ADDRESS"] = conf_loader.attempt_load_param("qq-email-address")
    print(count_unread_emails(status="Unseen"))

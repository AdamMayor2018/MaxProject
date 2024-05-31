# -- coding: utf-8 --
# @Time : 2024/5/31 11:16
# @Author : caoxiang
# @File : develop_tool.py
# @Software: PyCharm
# @Description: 大模型参与开发工具
import re
from openai import OpenAI
import os
from config.conf_loader import YamlConfigLoader
import imaplib

def extract_function_code(s, detail=0, tested=False):
    """
    函数提取函数，同时执行函数内容，可以选择打印函数信息，并选择代码保存的地址
    """

    def extract_code(s):
        """
        如果输入的字符串s是一个包含Python代码的Markdown格式字符串，提取出代码部分。
        否则，返回原字符串。

        参数:
        s: 输入的字符串。

        返回:
        提取出的代码部分，或原字符串。
        """
        # 判断字符串是否是Markdown格式
        if '```python' in s or 'Python' in s or 'PYTHON' in s:
            # 找到代码块的开始和结束位置
            if 'import' in s:
                code_start = s.find('import')
            elif 'def' in s:
                code_start = s.find('def')
            elif 'class' in s:
                code_start = s.find('class')
            else:
                code_start = s.find("```") + 3
            code_end = s.find('```\n', code_start)
            # 提取代码部分
            code = s[code_start:code_end]
        else:
            # 如果字符串不是Markdown格式，返回原字符串
            code = s

        return code

    # 提取代码字符串
    code = extract_code(s)

    # 提取函数名称
    match = re.search(r'def (\w+)', code)
    function_name = match.group(1)

    # 将函数写入本地
    if tested == False:
        with open('../functions/untested/%s_module.py' % function_name, 'w', encoding='utf-8') as f:
            f.write(code)
    else:
        with open('../functions/tested/%s_module.py' % function_name, 'w', encoding='utf-8') as f:
            f.write(code)

    # 执行该函数
    try:
        exec(code, globals())
    except Exception as e:
        print("An error occurred while executing the code:")
        print(e)

    # 打印函数名称
    if detail == 0:
        print("The function name is:%s" % function_name)
    if detail == 1:
        with open('../functions/untested/%s_module.py' % function_name, encoding='utf-8') as f:
            content = f.read()
        print(content)


if __name__ == '__main__':
    conf_loader = YamlConfigLoader(yaml_path="../config/config.yaml")
    os.environ["OPENAI_API_KEY"] = conf_loader.attempt_load_param("api-key")

    client = OpenAI()
    # LTM-CD
    system_content1 = "为了更好编写满足用户需求的python函数，我们需要先识别用户需求中的变量，以作为python函数的参数，需要注意的是，当前编写的函数中" \
                      "涉及到的邮件收发和查阅等功能，都是调用QQ邮箱的SMTP服务进行邮件处理。"
    input1 = "请帮我查询qq邮箱里的邮件内容"
    pi1 = "当前需求中可以作为参数的是：1.查询多少封邮件；2.查询的是未读邮件还是全部的邮件"
    input2 = "请帮我给caoxiang@yangshipin.cn发送一封QQ邮件，请他明天早上9点半来我办公室开会，商量下半年技术开发计划。"
    pi2 = "当前需求中可以作为函数的参数：1.收件方的地址；2.邮件的主题；3.邮件的具体内容"
    input3 = "请查下我的邮箱里是否有来自aliyun.com的未读邮件，并解读最近一封未读邮件的内容。"
    messages_CD = [
        {"role": "system", "content": system_content1},
        {"role": "user", "name": "example1_user", "content": input1},
        {"role": "assistant", "name": "example1_assistant", "content": pi1},
        {"role": "user", "name": "example2_user", "content": input2},
        {"role": "assistant", "name": "example2_assistant", "content": pi2},
        {"role": "user", "name": "example_user", "content": input3}

    ]
    pi3 = "当前需求中可以作为函数的参数：1.发件方的邮箱；2.函数参数type，表示查询的类型，包含All或者Unseen两类，默认为All代表全部的邮件，Unseen代表的是未读邮件；"
    # LTM_CM
    system_content2 = "我现在已拿到QQ SMTP服务授权，授权码保存在环境变量'qq-mail-key'中。我的邮箱地址保存在环境变量'qq-email-address'中，所编写的函数要求参数类型必须是字符串类型"
    get_email_input = "请帮我查下邮箱里的邮件内容。" + pi1
    get_email_output = "请帮我编写一个python函数，用于查看我的QQ邮箱中最后一封邮件信息，函数要求如下：\
                 1.函数参数request_num，request_num是字符串参数，表示查询最近的多少封邮件，默认情况下取值为'1'，表示查看最近的1封的邮件；\
                 2.函数参数type，表示查询的类型，包含All或者Unseen两类，默认为All代表全部的邮件，Unseen代表的是未读邮件；\
                 3.函数返回结果是一个包含查询邮件信息的对象，返回结果本身必须是一个json格式对象；\
                 4.请将全部功能封装在一个函数内；\
                 5.请在函数编写过程中，在函数内部加入中文编写的详细的函数说明文档，用于说明函数功能、函数参数情况以及函数返回结果等信息；"
    send_email_input = "请帮我给陈明发送一封邮件，请他明天早上9点半来我办公室开会，商量下半年技术开发计划。" + pi2
    send_email_output = "请帮我编写一个python函数，用于给陈明发送邮件，请他明天早上9点半来我办公室开会，商量下半年技术开发计划，函数要求如下：\
                      1.函数参数to、subject和message_text，三个参数都是字符串类型，其中to表示发送邮件对象，subject表示邮件主题，message_text表示邮件具体内容；\
                      2.函数返回结果是当前邮件发送状态，返回结果本身必须是一个json格式对象；\
                      3.请将全部功能封装在一个函数内；\
                      4.请在函数编写过程中，在函数内部加入中文编写的详细的函数说明文档，用于说明函数功能、函数参数情况以及函数返回结果等信息；"
    user_content = input3 + pi3
    messages_CM = [{"role": "system", "content": system_content2},
                   {"role": "user", "name": "example1_user", "content": get_email_input},
                   {"role": "assistant", "name": "example1_assistant", "content": get_email_output},
                   {"role": "user", "name": "example2_user", "content": send_email_input},
                   {"role": "assistant", "name": "example2_assistant", "content": send_email_output},
                   {"role": "user", "name": "example_user", "content": user_content}]


    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages_CM,
    )
    response_message = response.choices[0].message
    print(response_message.content)
    print(extract_function_code(response_message.content, detail=1, tested=False))

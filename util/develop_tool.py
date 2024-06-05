# -- coding: utf-8 --
# @Time : 2024/5/31 11:16
# @Author : caoxiang
# @File : develop_tool.py
# @Software: PyCharm
# @Description: 大模型参与开发工具
import json
import re
from openai import OpenAI
import os
from config.conf_loader import YamlConfigLoader
import imaplib
import inspect
from brain.outer_func import *
import shutil


def remove_to_tested(function_name):
    """
    将函数同名文件夹由untested文件夹转移至tested文件夹内。\
    完成转移则说明函数通过测试，可以使用。此时需要将该函数的源码写入gptLearning.py中方便下次调用。
    """

    # 将函数代码写入gptLearning.py文件中
    # with open('./functions/untested/%s_module.py' % function_name, encoding='utf-8') as f:
    #     function_code = f.read()

    # with open('gptLearning.py', 'a', encoding='utf-8') as f:
    #     f.write(function_code)

    # 源文件夹路径
    src_dir = '../functions/untested/%s' % function_name

    # 目标文件夹路径
    dst_dir = '../functions/tested/%s' % function_name

    # 移动文件夹
    shutil.move(src_dir, dst_dir)


def extract_function_code(s, detail=0, tested=False, g=globals()):
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
            code_start = s.find('def')
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
        with open('../functions/untested/%s_module.py' % function_name, 'w',
                  encoding='utf-8') as f:
            f.write(code)
    else:
        # 调用remove_to_test函数将函数文件夹转移至tested文件夹内
        remove_to_tested(function_name)
        with open('../functions/tested/%s_module.py' % function_name, 'w',
                  encoding='utf-8') as f:
            f.write(code)

    # 执行该函数
    try:
        exec(code, g)
    except Exception as e:
        print("An error occurred while executing the code:")
        print(e)

    # 打印函数名称
    if detail == 0:
        print("The function name is:%s" % function_name)

    if detail == 1:
        if tested == False:
            with open('../functions/untested/%s_module.py' % function_name, 'r',
                      encoding='utf-8') as f:
                content = f.read()
        else:
            with open('../functions/tested/%s_module.py' % function_name, 'r',
                      encoding='utf-8') as f:
                content = f.read()

        print(content)

    return function_name


def show_functions(tested=False, if_print=False):
    """
    打印tested或untested文件夹内全部函数
    """
    current_directory = os.getcwd()
    if tested == False:
        directory = current_directory + '\\functions\\untested functions'
    else:
        directory = current_directory + '\\functions\\tested functions'
    files_and_directories = os.listdir(directory)
    # 过滤结果，只保留.py文件和非__pycache__文件夹
    files_and_directories = files_and_directories = [name for name in files_and_directories if (
            os.path.splitext(name)[1] == '.py' or os.path.isdir(
        os.path.join(directory, name))) and name != "__pycache__"]

    if if_print != False:
        for name in files_and_directories:
            print(name)

    return files_and_directories


def prompt_modified(function_name, system_content='推理链修改.md', model="gpt-4o", g=globals()):
    """
    智能邮件项目的外部函数审查函数，用于审查外部函数创建流程提示是否正确以及最终创建的代码是否正确
    :param function_name: 必要参数，字符串类型，表示审查对象名称；
    :param system_content: 可选参数，默认取值为字符串推理链修改.md，表示此时审查函数外部挂载文档名称，需要是markdwon格式文档；
    :param model: 可选参数，表示调用的Chat模型，默认选取gpt-4-0613；
    :param g: 可选参数，表示extract_function_code函数作用域，默认为globals()，即在当前操作空间全域内生效；
    :return：审查结束后新创建的函数名称
    """
    print("正在执行审查函数，审查对象：%s" % function_name)
    with open(system_content, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 读取原函数全部提示内容
    with open('./functions/untested functions/%s/%s_prompt.json' % (function_name, function_name), 'r') as f:
        msg = json.load(f)

    # 将其保存为字符串
    msg_str = json.dumps(msg)

    # 进行审查
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": md_content},
            {"role": "user", "content": '以下是一个错误的智能邮件项目的推理链，请你按照要求对其进行修改：%s' % msg_str}
        ]
    )

    modified_result = response.choices[0].message['content']

    def extract_json(s):
        pattern = r'```[jJ][sS][oO][nN]\s*({.*?})\s*```'
        match = re.search(pattern, s, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return s

    modified_json = extract_json(modified_result)

    # 提取函数源码
    code = json.loads(modified_json)['stage2'][1]['content']

    # 提取函数名
    match = re.search(r'def (\w+)', code)
    function_name = match.group(1)

    print("审查结束，新的函数名称为：%s。\n正在运行该函数定义过程，并保存函数源码与prompt" % function_name)

    exec(code, g)

    # 在untested文件夹内创建函数同名文件夹
    directory = './functions/untested functions/%s' % function_name
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 写入函数
    with open('./functions/untested functions/%s/%s_module.py' % (function_name, function_name), 'w',
              encoding='utf-8') as f:
        f.write(code)

    # 写入提示
    with open('./functions/untested functions/%s/%s_prompt.json' % (function_name, function_name), 'w') as f:
        json.dump(json.loads(modified_json), f)

    print('新函数提示示例保存在./functions/untested functions/%s/%s_prompt.json文件中' % (function_name, function_name))
    print("%s函数已在当前操作空间定义，可以进行效果测试" % function_name)

    return function_name

if __name__ == '__main__':
    conf_loader = YamlConfigLoader(yaml_path="../config/config.yaml")
    os.environ["OPENAI_API_KEY"] = conf_loader.attempt_load_param("api-key")

    client = OpenAI()
    # LTM-CD
    # system_content1 = "为了更好编写满足用户需求的python函数，我们需要先识别用户需求中的变量，以作为python函数的参数，需要注意的是，当前编写的函数中" \
    #                   "涉及到的邮件收发和查阅等功能，都是调用QQ邮箱的SMTP服务进行邮件处理。"
    # input1 = "请帮我查询qq邮箱里的邮件内容"
    # pi1 = "当前需求中可以作为参数的是：1.查询多少封邮件；2.查询的是未读邮件还是全部的邮件"
    # input2 = "请帮我给caoxiang@yangshipin.cn发送一封QQ邮件，请他明天早上9点半来我办公室开会，商量下半年技术开发计划。"
    # pi2 = "当前需求中可以作为函数的参数：1.收件方的地址；2.邮件的主题；3.邮件的具体内容"
    # input3 = "请查下我的邮箱里是否有来自aliyun.com的未读邮件，并解读最近一封未读邮件的内容。"
    # messages_CD = [
    #     {"role": "system", "content": system_content1},
    #     {"role": "user", "name": "example1_user", "content": input1},
    #     {"role": "assistant", "name": "example1_assistant", "content": pi1},
    #     {"role": "user", "name": "example2_user", "content": input2},
    #     {"role": "assistant", "name": "example2_assistant", "content": pi2},
    #     {"role": "user", "name": "example_user", "content": input3}
    #
    # ]
    # pi3 = "当前需求中可以作为函数的参数：1.发件方的邮箱；2.函数参数type，表示查询的类型，包含All或者Unseen两类，默认为All代表全部的邮件，Unseen代表的是未读邮件；"
    # # LTM_CM
    # system_content2 = "我现在已拿到QQ SMTP服务授权，授权码保存在环境变量'qq-mail-key'中。我的邮箱地址保存在环境变量'qq-email-address'中，所编写的函数要求参数类型必须是字符串类型"
    # get_email_input = "请帮我查下邮箱里的邮件内容。" + pi1
    # get_email_output = "请帮我编写一个python函数，用于查看我的QQ邮箱中最后一封邮件信息，函数要求如下：\
    #              1.函数参数request_num，request_num是字符串参数，表示查询最近的多少封邮件，默认情况下取值为'1'，表示查看最近的1封的邮件；\
    #              2.函数参数type，表示查询的类型，包含All或者Unseen两类，默认为All代表全部的邮件，Unseen代表的是未读邮件；\
    #              3.函数返回结果是一个包含查询邮件信息的对象，返回结果本身必须是一个json格式对象；\
    #              4.请将全部功能封装在一个函数内；\
    #              5.请在函数编写过程中，在函数内部加入中文编写的详细的函数说明文档，用于说明函数功能、函数参数情况以及函数返回结果等信息；"
    # send_email_input = "请帮我给陈明发送一封邮件，请他明天早上9点半来我办公室开会，商量下半年技术开发计划。" + pi2
    # send_email_output = "请帮我编写一个python函数，用于给陈明发送邮件，请他明天早上9点半来我办公室开会，商量下半年技术开发计划，函数要求如下：\
    #                   1.函数参数to、subject和message_text，三个参数都是字符串类型，其中to表示发送邮件对象，subject表示邮件主题，message_text表示邮件具体内容；\
    #                   2.函数返回结果是当前邮件发送状态，返回结果本身必须是一个json格式对象；\
    #                   3.请将全部功能封装在一个函数内；\
    #                   4.请在函数编写过程中，在函数内部加入中文编写的详细的函数说明文档，用于说明函数功能、函数参数情况以及函数返回结果等信息；其中参数需要遵循@param:，返回值需要遵循@return:开始"
    # user_content = input3 + pi3
    # messages_CM = [{"role": "system", "content": system_content2},
    #                {"role": "user", "name": "example1_user", "content": get_email_input},
    #                {"role": "assistant", "name": "example1_assistant", "content": get_email_output},
    #                {"role": "user", "name": "example2_user", "content": send_email_input},
    #                {"role": "assistant", "name": "example2_assistant", "content": send_email_output},
    #                {"role": "user", "name": "example_user", "content": user_content}]
    #
    #
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=messages_CM,
    # )
    # response_message = response.choices[0].message
    # print(response_message.content)
    # print(extract_function_code(response_message.content, detail=1, tested=False))
    # 第一阶段LtM_CD阶段提示词及输出结果
    with open("../prompts/推理链修改.md", "r", encoding="utf-8") as f:
        md_content = f.read()
        #print(md_content)

    function_name = "get_latest_mail"
    with open('../prompts/%s_prompt.json' % function_name, 'r') as f:
        msg = json.load(f)

    #chain_of_prompt = "以下是一个智能邮件项目的推理链，请你按照要求对其进行分析，提出修改意见：%s" % msg
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "以下是一个智能邮件项目的推理链，请你按照要求对其进行分析，提出修改意见：%s" % msg}]
    )
    print(response.choices[0].message.content)

    # wrong_code = msg['stage2'][1]['content']
    # exec(wrong_code)

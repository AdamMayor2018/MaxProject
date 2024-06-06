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
from test import run_conversation

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
    src_dir = '../functions/untested/%s_module.py' % function_name

    # 目标文件夹路径
    dst_dir = '../functions/tested/%s_module.py' % function_name

    # 移动文件夹
    print(src_dir, dst_dir)
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
            if 'import' in s:
                code_start = s.find('import')
            elif 'from' in s and 'import' in s:
                code_start = s.find('from')
            else:
                code_start = s.find('def')
            code_end = s.find('`', code_start)
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
    if not tested:
        directory = os.path.join(current_directory, "..", "functions/untested")
    else:
        directory = os.path.join(current_directory, "..", "functions/tested")
    files_and_directories = os.listdir(directory)
    # 过滤结果，只保留.py文件和非__pycache__文件夹
    files_and_directories = [name.replace("_module.py", "") for name in files_and_directories if (
            os.path.splitext(name)[1] == '.py'  and name != "__pycache__") and name != "__init__.py"]

    if if_print:
        for name in files_and_directories:
            print(name)

    return files_and_directories


def code_generate(client, req, few_shot='all', model='gpt-4o', g=globals(), detail=0):
    """
    Function calling外部函数自动创建函数，可以根据用户的需求，直接将其翻译为Chat模型可以直接调用的外部函数代码。
    :param client: 必要参数， OpenAI客户端对象
    :param req: 必要参数，字符串类型，表示输入的用户需求；
    :param few_shot: 可选参数，默认取值为字符串all，用于描述Few-shot提示示例的选取方案，当输入字符串all时，则代表提取当前外部函数库中全部测试过的函数作为Few-shot；\
    而如果输入的是一个包含了多个函数名称的list，则表示使用这些函数作为Few-shot。
    :param model: 可选参数，表示调用的Chat模型，默认选取gpt-4o；
    :param g: 可选参数，表示extract_function_code函数作用域，默认为globals()，即在当前操作空间全域内生效；
    :param detail: 可选参数，默认取值为0，还可以取值为1，表示extract_function_code函数打印新创建的外部函数细节；
    :return：新创建的函数名称。需要注意的是，在函数创建时，该函数也会在当前操作空间被定义，后续可以直接调用；
    """

    # 提取提示示例的函数名称
    if few_shot == 'all':
        few_shot_functions_name = show_functions(tested=True)
    elif type(few_shot) == list:
        few_shot_functions_name = few_shot
    # few_shot_functions = [globals()[name] for name in few_shot_functions_name]

    # 读取各阶段系统提示
    with open('../prompts/system_messages.json', 'r') as f:
        system_messages = json.load(f)

    # 各阶段提示message对象
    few_shot_messages_CM = []
    few_shot_messages_CD = []
    few_shot_messages = []

    # 先保存第一条消息，也就是system message
    few_shot_messages_CD += system_messages["system_message_CD"]
    few_shot_messages_CM += system_messages["system_message_CM"]
    few_shot_messages += system_messages["system_message"]

    # 创建不同阶段提示message
    for function_name in few_shot_functions_name:
        with open('../prompts/tested/%s_prompt.json' % function_name, 'r') as f:
            msg = json.load(f)
        few_shot_messages_CD += msg["stage1_CD"]
        few_shot_messages_CM += msg["stage1_CM"]
        few_shot_messages += msg['stage2']

    # 读取用户需求，作为第一阶段CD环节User content
    new_req_CD_input = req
    few_shot_messages_CD.append({"role": "user", "content": new_req_CD_input})

    print('第一阶段CD环节提示创建完毕，正在进行CD提示...')

    # 第一阶段CD环节Chat模型调用过程
    response = client.chat.completions.create(
        model=model,
        messages=few_shot_messages_CD
    )
    new_req_pi = response.choices[0].message.content

    print('第一阶段CD环节提示完毕')

    # 第一阶段CM环节Messages创建
    new_req_CM_input = new_req_CD_input + new_req_pi
    few_shot_messages_CM.append({"role": "user", "content": new_req_CM_input})

    print('第一阶段CM环节提示创建完毕，正在进行第一阶段CM提示...')
    # 第一阶段CM环节Chat模型调用过程
    response = client.chat.completions.create(
        model=model,
        messages=few_shot_messages_CM
    )
    new_req_description = response.choices[0].message.content

    print('第一阶段CM环节提示完毕')

    # 第二阶段Messages创建过程
    few_shot_messages.append({"role": "user", "content": new_req_description})

    print('第二阶段提示创建完毕，正在进行第二阶段提示...')

    # 第二阶段Chat模型调用过程
    response = client.chat.completions.create(
        model=model,
        messages=few_shot_messages
    )
    new_req_function = response.choices[0].message.content

    print('第二阶段提示完毕，准备运行函数并编写提示示例')

    # 提取函数并运行，创建函数名称对象，统一都写入untested文件夹内
    function_name = extract_function_code(s=new_req_function, detail=detail, g=g)

    print('新函数保存在../functions/untested/%s_module.py文件中' % function_name)

    # 创建该函数提示示例
    new_req_messages_CD = [
        {"role": "user", "content": new_req_CD_input},
        {"role": "assistant", "content": new_req_pi}
    ]
    new_req_messages_CM = [
        {"role": "user", "content": new_req_CM_input},
        {"role": "assistant", "content": new_req_description}
    ]

    with open('../functions/untested/%s_module.py' % function_name, encoding='utf-8') as f:
        new_req_function = f.read()

    new_req_messages = [
        {"role": "user", "content": new_req_description},
        {"role": "assistant", "content": new_req_function}
    ]

    new_req_prompt = {
        "stage1_CD": new_req_messages_CD,
        "stage1_CM": new_req_messages_CM,
        "stage2": new_req_messages
    }

    with open('../prompts/untested/%s_prompt.json' % function_name, 'w') as f:
        json.dump(new_req_prompt, f)

    print('新函数提示示例保存在../prompts/untested/%s_prompt.json文件中' % function_name)
    print('done')
    return function_name


def prompt_modified(client, function_name, system_content='推理链修改.md', model="gpt-4o", g=globals()):
    """
    智能邮件项目的外部函数审查函数，用于审查外部函数创建流程提示是否正确以及最终创建的代码是否正确
    :param client: 必要参数，表示openAI client客户端对象。
    :param function_name: 必要参数，字符串类型，表示审查对象名称；
    :param system_content: 可选参数，默认取值为字符串推理链修改.md，表示此时审查函数外部挂载文档名称，需要是markdwon格式文档；
    :param model: 可选参数，表示调用的Chat模型，默认选取gpt-4o；
    :param g: 可选参数，表示extract_function_code函数作用域，默认为globals()，即在当前操作空间全域内生效；
    :return：审查结束后新创建的函数名称
    """
    print("正在执行审查函数，审查对象：%s" % function_name)
    with open(os.path.join("../prompts", system_content), 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 读取原函数全部提示内容
    with open('../prompts/untested/%s_prompt.json' % function_name, 'r') as f:
        msg = json.load(f)

    # 将其保存为字符串
    msg_str = json.dumps(msg)

    # 进行审查
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": md_content},
            {"role": "user", "content": '以下是一个错误的智能邮件项目的推理链，请你按照要求对其进行修改：%s' % msg_str}
        ]
    )

    modified_result = response.choices[0].message.content

    def extract_json(s):
        pattern = r'```[jJ][sS][oO][nN]\s*({.*?})\s*```'
        match = re.search(pattern, s, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return s

    modified_json = extract_json(modified_result)

    # 提取函数源码
    code = json.loads(modified_json)['stage2'][1].content

    # 提取函数名
    match = re.search(r'def (\w+)', code)
    function_name = match.group(1)

    print("审查结束，新的函数名称为：%s。\n正在运行该函数定义过程，并保存函数源码与prompt" % function_name)

    exec(code, g)

    # 在untested文件夹内创建函数同名文件夹
    # directory = '../functions/untested functions/%s' % function_name
    # if not os.path.exists(directory):
    #     os.makedirs(directory)

    # 写入函数
    with open('../functions/untested/%s_module.py' % function_name, 'w',
              encoding='utf-8') as f:
        f.write(code)

    # 写入提示
    with open('../prompts/untested/%s_prompt.json' % function_name, 'w', encoding='utf-8') as f:
        json.dump(json.loads(modified_json), f)

    print('新函数提示示例保存在../functions/untested/%s_prompt.json文件中' % function_name)
    print("%s函数已在当前操作空间定义，可以进行效果测试" % function_name)

    return function_name


def function_test(client, function_name, req, few_shot, model="gpt-4o", g=globals()):
    def test_messages(user_content):
        # messages = [{"role": "system", "content": "端木天的邮箱地址是:2323365771@qq.com"},
        #             {"role": "system", "content": "我的邮箱地址是:adamcx@foxmail.com"},
        #             {"role": "user", "content": user_content}]
        messages = [{"role": "system", "content": "我现在已拿到QQ SMTP服务授权，授权码保存在python环境变量'QQ_MAIL_KEY'中。我的邮箱地址保存在python环境变量'QQ_EMAIL_ADDRESS'中"},
                    {"role": "user", "content": user_content}]
        return messages

    messages = test_messages(req)

    new_function = globals()[function_name]
    functions_list = [new_function]

    print("根据既定用户需求req进行%s函数功能测试，请确保当该函数已经在当前操作空间定义..." % function_name)

    # 有可能在run_conversation环节报错
    # 若没报错，则运行：
    try:
        final_response = run_conversation(client, messages=messages, functions_list=functions_list, model=model)
        print("当前函数运行结果：'%s'" % final_response)

        feedback = input("函数功能是否满足要求 (yes/no)? ")
        if feedback.lower() == 'yes':
            print("函数功能通过测试，正在将函数写入tested文件夹")
            remove_to_tested(function_name)
            print('done')
        else:
            next_step = input("函数功能未通过测试，是1.需要再次进行测试，还是2.进入debug流程？")
            if next_step == '1':
                print("准备再次测试...")
                function_test(client, function_name, req, few_shot)
            else:
                solution = input("请选择debug方案：\n1.再次执行函数创建流程，并测试结果；\n2.执行审查函数\
                \n3.重新输入用户需求；\n4.退出程序，进行手动尝试")
                if solution == '1':
                    # 再次运行函数创建过程
                    print("好的，正在尝试再次创建函数，请稍等...")
                    few_shot_str = input("准备再次测试，请问是1.采用此前Few-shot方案，还是2.带入全部函数示例进行Few-shot？")
                    if few_shot_str == '1':
                        function_name = code_generate(client, req=req, few_shot=few_shot, model=model, g=g)
                    else:
                        function_name = code_generate(client, req=req, few_shot='all', model=model, g=g)
                    function_test(client=client, function_name=function_name, req=req, few_shot=few_shot, g=g)
                elif solution == '2':
                    # 执行审查函数
                    print("好的，执行审查函数，请稍等...")
                    function_name = prompt_modified(client, function_name=function_name, model="gpt-4o", g=g)
                    # 接下来带入进行测试
                    print("新函数已创建，接下来带入进行测试...")
                    function_test(client=client, function_name=function_name, req=req, few_shot=few_shot, g=g)
                elif solution == '3':
                    new_req = input("好的，请再次输入用户需求，请注意，用户需求描述方法将极大程度影响最终函数创建结果。")
                    few_shot_str = input("接下来如何运行代码创建函数？1.采用此前Few-shot方案；\n2.使用全部外部函数作为Few-shot")
                    if few_shot_str == '1':
                        function_name = code_generate(client=client, req=new_req, few_shot=few_shot, model=model, g=g)
                    else:
                        function_name = code_generate(client=client, req=new_req, few_shot='all', model=model, g=g)
                    function_test(client=client, function_name=function_name, req=new_req, few_shot=few_shot, g=g)
                elif solution == '4':
                    print("好的，预祝debug顺利~")

    # run_conversation报错时则运行：
    except Exception as e:
        next_step = input(f"run_conversation无法正常运行，提示报错为：{e}  接下来是1.再次运行运行run_conversation，还是2.进入debug流程？")
        if next_step == '1':
            function_test(client, function_name, req, few_shot)
        else:
            solution = input("请选择debug方案：\n1.再次执行函数创建流程，并测试结果；\n2.执行审查函数\
            \n3.重新输入用户需求；\n4.退出程序，进行手动尝试")
            if solution == '1':
                # 再次运行函数创建过程
                print("好的，正在尝试再次创建函数，请稍等...")
                few_shot_str = input("准备再次测试，请问是1.采用此前Few-shot方案，还是2.带入全部函数示例进行Few-shot？")
                if few_shot_str == '1':
                    function_name = code_generate(client=client, req=req, few_shot=few_shot, model=model, g=g)
                else:
                    function_name = code_generate(client=client, req=req, few_shot='all', model=model, g=g)
                function_test(client=client, function_name=function_name, req=req, few_shot=few_shot, g=g)
            elif solution == '2':
                # 执行审查函数
                print("好的，执行审查函数，请稍等...")
                max_attempts = 3
                attempts = 0

                while attempts < max_attempts:
                    try:
                        function_name = prompt_modified(client=client, function_name=function_name, model="gpt-4o",
                                                        g=g)
                        break  # 如果代码成功执行，跳出循环
                    except Exception as e:
                        attempts += 1  # 增加尝试次数
                        print("发生错误：", e)
                        if attempts == max_attempts:
                            print("已达到最大尝试次数，程序终止。")
                            raise  # 重新引发最后一个异常
                        else:
                            print("正在重新运行审查程序...")
                # 接下来带入进行测试
                print("新函数已创建，接下来带入进行测试...")
                function_test(client=client, function_name=function_name, req=req, few_shot=few_shot, g=g)
            elif solution == '3':
                new_req = input("好的，请再次输入用户需求，请注意，用户需求描述方法将极大程度影响最终函数创建结果。")
                few_shot_str = input("接下来如何运行代码创建函数？1.采用此前Few-shot方案；\n2.使用全部外部函数作为Few-shot")
                if few_shot_str == '1':
                    function_name = code_generate(client=client, req=new_req, few_shot=few_shot, model=model, g=g)
                else:
                    function_name = code_generate(client=client, req=new_req, few_shot='all', model=model, g=g)
                function_test(client=client, function_name=function_name, req=new_req, few_shot=few_shot, g=g)
            elif solution == '4':
                print("好的，预祝debug顺利~")


def mail_auto_func(client, req, few_shot='all', model='gpt-4o', g=globals(), detail=0):
    function_name = code_generate(client=client, req=req, few_shot=few_shot, model=model, g=g, detail=detail)
    function_test(client=client, function_name=function_name, req=req, few_shot=few_shot, model=model, g=g)


if __name__ == '__main__':
    conf_loader = YamlConfigLoader(yaml_path="../config/config.yaml")
    os.environ["OPENAI_API_KEY"] = conf_loader.attempt_load_param("api-key")
    os.environ["QQ_MAIL_KEY"] = conf_loader.attempt_load_param("qq-mail-key")
    os.environ["QQ_EMAIL_ADDRESS"] = conf_loader.attempt_load_param("qq-email-address")
    client = OpenAI()
    req = "我现在已拿到QQ SMTP服务授权，授权码保存在python环境变量'QQ_MAIL_KEY'中。我的邮箱地址保存在python环境变量'QQ_EMAIL_ADDRESS'中, 请帮我统计下我的邮箱里面总共有几封未读邮件"
    mail_auto_func(client, req)
    #
    # system_messages = {"system_message_CD": [{"role": "system",
    #                                           "content": "我现在已拿到QQ SMTP服务授权。授权码保存在环境变量'QQ_MAIL_KEY'中。我的邮箱地址保存在环境变量'QQ_EMAIL_ADDRESS'中。为了更好编写满足用户需求的python函数，我们需要先识别用户需求中的变量，以作为python函数的参数。在这阶段只需要按照样例返回需求的变量，而不需要撰写代码"}],
    #                    "system_message_CM": [{"role": "system",
    #                                           "content": "我现在已拿到QQ SMTP服务授权。授权码保存在环境变量'QQ_MAIL_KEY'中。我的邮箱地址保存在环境变量'QQ_EMAIL_ADDRESS'中。为了更好编写满足用户需求的python函数，我们需要将前面识别到的变量转换为函数的描述，注意在这个阶段只需要按照样例返回函数编写的描述要求，而不需要撰写实际的代码"}],
    #                    "system_message": [{"role": "system",
    #                                        "content": "我现在已拿到QQ SMTP服务授权。授权码保存在环境变量'QQ_MAIL_KEY'中。我的邮箱地址保存在环境变量'QQ_EMAIL_ADDRESS'中。函数参数必须是字符串类型对象，函数返回结果必须是json表示的字符串对象。现在我们需要逐步完成函数的需求分析和撰写。注意函数不要编写main函数,且符合utf-8编码。"}]}
    #
    # with open('../prompts/%s.json' % 'system_messages', 'w') as f:
    #     json.dump(system_messages, f)


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
    # def extract_json(s):
    #     pattern = r'```[jJ][sS][oO][nN]\s*({.*?})\s*```'
    #     match = re.search(pattern, s, re.DOTALL)
    #     if match:
    #         return match.group(1)
    #     else:
    #         return s
    #
    #
    # with open("../prompts/推理链修改.md", "r", encoding="utf-8") as f:
    #     md_content = f.read()
    #     # print(md_content)
    #
    # function_name = "get_latest_mail"
    # with open('../prompts/%s_prompt.json' % function_name, 'r') as f:
    #     msg = json.load(f)
    #
    # # chain_of_prompt = "以下是一个智能邮件项目的推理链，请你按照要求对其进行分析，提出修改意见：%s" % msg
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[{"role": "user",
    #                "content": "以下是一个智能邮件项目的推理链，请你按照要求对其进行分析修改，注意，请勿返回其他解释说明的文字，只返回一个json格式的修改之后的推理链即可：%s" % msg}]
    # )
    # modified_result = response.choices[0].message.content
    # code = json.loads(extract_json(modified_result))["stage2"][1]["content"]
    # print(code)
    # # wrong_code = msg['stage2'][1].content
    # # exec(wrong_code)
    # exec(code)

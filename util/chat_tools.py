#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/10 11:12
# @Author  : Caoxiang
# @File    : chat_tools.py
# @Description  :
import inspect
import pandas as pd
import numpy as np
import json
import openai
import tiktoken


def auto_functions(client, functions_list):
    """
    Chat模型的functions参数编写函数
    :param functions_list: 包含一个或者多个函数对象的列表；
    :return：满足Chat模型functions参数要求的functions对象
    """

    def functions_generate(functions_list):
        # 创建空列表，用于保存每个函数的描述字典
        functions = []

        def chen_ming_algorithm(data):
            """
            陈明算法函数，该函数定义了一种特殊的数据集计算过程
            :param data: 必要参数，表示带入计算的数据表，用字符串进行表示
            :return：陈明函数计算后的结果，返回结果为表示为JSON格式的Dataframe类型对象
            """
            df_new = pd.read_json(data)
            res = np.sum(df_new, axis=1) - 1
            return res.to_json(orient='records')

        chen_ming_function_description = inspect.getdoc(chen_ming_algorithm)

        chen_ming_function_name = chen_ming_algorithm.__name__

        chen_ming_function = {"name": "chen_ming_algorithm",
                              "description": "用于执行陈明算法的函数，定义了一种特殊的数据集计算过程",
                              "parameters": {"type": "object",
                                             "properties": {"data": {"type": "string",
                                                                     "description": "执行陈明算法的数据集"},
                                                            },
                                             "required": ["data"],
                                             },
                              }

        # 对每个外部函数进行循环
        for function in functions_list:
            # 读取函数对象的函数说明
            function_description = inspect.getdoc(function)
            # 读取函数的函数名字符串
            function_name = function.__name__

            user_message1 = '以下是某的函数说明：%s。' % chen_ming_function_description + \
                            '根据这个函数的函数说明，请帮我创建一个function对象，用于描述这个函数的基本情况。这个function对象是一个JSON格式的字典，\
                            这个字典有如下5点要求：\
                            1.字典总共有三个键值对；\
                            2.第一个键值对的Key是字符串name，value是该函数的名字：%s，也是字符串；\
                            3.第二个键值对的Key是字符串description，value是该函数的函数的功能说明，也是字符串；\
                            4.第三个键值对的Key是字符串parameters，value是一个JSON Schema对象，用于说明该函数的参数输入规范。\
                            5.输出结果必须是一个JSON格式的字典，只输出这个字典即可，前后不需要任何前后修饰或说明的语句' % chen_ming_function_name

            assistant_message1 = json.dumps(chen_ming_function)

            user_prompt = '现在有另一个函数，函数名为：%s；函数说明为：%s；\
                          请帮我仿造类似的格式为当前函数创建一个function对象。' % (function_name, function_description)

            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "user", "name": "example_user", "content": user_message1},
                    {"role": "assistant", "name": "example_assistant", "content": assistant_message1},
                    {"role": "user", "name": "example_user", "content": user_prompt}]
            )
            functions.append(json.loads(response.choices[0].message.content))
        return functions

    max_attempts = 3
    attempts = 0

    while attempts < max_attempts:
        try:
            functions = functions_generate(functions_list)
            break  # 如果代码成功执行，跳出循环
        except Exception as e:
            attempts += 1  # 增加尝试次数
            print("发生错误：", e)
            if attempts == max_attempts:
                print("已达到最大尝试次数，程序终止。")
                raise  # 重新引发最后一个异常
            else:
                print("正在重新运行...")
    return functions


def run_conversation(client, messages, functions_list=None, model="gpt-4o"):
    """
    能够自动执行外部函数调用的Chat对话模型
    :param messages: 必要参数，字典类型，输入到Chat模型的messages参数对象
    :param functions_list: 可选参数，默认为None，可以设置为包含全部外部函数的列表对象
    :param model: Chat模型，可选参数，默认模型为gpt-4
    :return：Chat模型输出结果
    """
    # 如果没有外部函数库，则执行普通的对话任务
    if functions_list == None:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        response_message = response.choices[0].message
        final_response = response_message.content

    # 若存在外部函数库，则需要灵活选取外部函数并进行回答
    else:
        # 创建functions对象
        functions = auto_functions(client, functions_list)
        # 创建外部函数库字典
        available_functions = {func.__name__: func for func in functions_list}

        # first response
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call="auto")
        response_message = response.choices[0].message

        # 判断返回结果是否存在function_call，即判断是否需要调用外部函数来回答问题
        if response_message.function_call:
            # 需要调用外部函数
            # 获取函数名
            function_name = response_message.function_call.name
            # 获取函数对象
            fuction_to_call = available_functions[function_name]
            # 获取函数参数
            function_args = json.loads(response_message.function_call.arguments)
            # 将函数参数输入到函数中，获取函数计算结果
            function_response = fuction_to_call(**function_args)

            # messages中拼接first response消息
            messages.append(response_message)
            # messages中拼接函数输出结果
            messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }
            )
            # 第二次调用模型
            second_response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            # 获取最终结果
            final_response = second_response.choices[0].message.content
        else:
            final_response = response_message.content

    return final_response


def cut_by_token(message, model="gpt-4o", token_limit=4096):
    encoding = tiktoken.encoding_for_model(model)
    token_size = len(encoding.encode(message))
    if token_size > token_limit:
        message = message[:token_limit]
    return message


def convert_keyword(client, model, q):
    """
    将用户输入的问题转化为适合在知乎上进行搜索的关键词
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "你专门负责将用户的问题转化为知乎网站搜索关键词，只返回一个你认为最合适的搜索关键词即可"},
            {"role": "user", "content": "请问，gpt-4o微调总共分为几步？"},
            {"role": "assistant", "content": "gpt-4o微调流程"},
            {"role": "user", "content": q}
        ]
    )
    q = response.choices[0].message.content
    return q

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/5 13:08
# @Author  : 作者名
# @File    : test.py
# @Description  :
from brain.base_func import *
from brain.outer_func import *
from openai import OpenAI
import os
from config.conf_loader import YamlConfigLoader
from util.chat_tools import auto_functions, run_conversation
from brain import outer_func as func
import inspect
from lxml import etree

def chat_with_model(
        client=None,
        functions_list=None,
        prompt="你好呀",
        model="gpt-4o",
        system_message=[{"role": "system", "content": get_base_info()}]):
    messages = system_message
    messages.append({"role": "user", "content": prompt})

    while True:
        #print(messages)
        answer = run_conversation(client=client,
                                  messages=messages,
                                  functions_list=functions_list,
                                  model=model)

        print(f"牛牛精灵: {answer}")
        messages.append({"role": "assistant", "content": answer})

        # 询问用户是否还有其他问题
        user_input = input("您还有其他问题吗？(输入退出以结束对话): ")
        if user_input == "退出":
            break

        # 记录用户回答
        messages.append({"role": "user", "content": user_input})


if __name__ == '__main__':
    conf_loader = YamlConfigLoader(yaml_path="config/config.yaml")
    os.environ["OPENAI_API_KEY"] = conf_loader.attempt_load_param("api-key")
    os.environ["OPEN_WEATHER_API_KEY"] = conf_loader.attempt_load_param("open-weather-api-key")
    os.environ["QQ_MAIL_KEY"] = conf_loader.attempt_load_param("qq-mail-key")
    os.environ["TAROT_API_KEY"] = conf_loader.attempt_load_param("tarot-api-key")
    # 初始化openai大脑
    client = OpenAI()
    function_list = [globals()[i[0]] for i in inspect.getmembers(func, inspect.isfunction)]
    chat_with_model(client=client, functions_list=function_list, prompt="你好呀", model="gpt-4o")
    print("xx")



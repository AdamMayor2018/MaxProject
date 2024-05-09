#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/5 13:08
# @Author  : 作者名
# @File    : test.py
# @Description  :
from brain.base_func import *
from openai import OpenAI
import os
from config.conf_loader import YamlConfigLoader
if __name__ == '__main__':
    conf_loader = YamlConfigLoader(yaml_path="config/config.yaml")
    os.environ["OPENAI_API_KEY"] = conf_loader.attempt_load_param("api-key")
    # 初始化openai大脑
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": get_base_info()},
            {"role": "user", "content": "你好"}
        ],
        timeout=10

    )

    print(completion.choices[0].message.content)
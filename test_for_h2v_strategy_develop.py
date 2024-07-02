#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/6/18 23:15
# @Author  : 作者名
# @File    : test_for_h2v_strategy_develop.py
# @Description  :
from brain.base_func import *
from brain.outer_func import *
from openai import OpenAI
import os
from config.conf_loader import YamlConfigLoader
from util.chat_tools import auto_functions, run_conversation
from brain import outer_func as func
import inspect
from test import chat_with_model

if __name__ == '__main__':
    conf_loader = YamlConfigLoader(yaml_path="config/config.yaml")
    os.environ["OPENAI_API_KEY"] = conf_loader.attempt_load_param("api-key")
    os.environ["OPEN_WEATHER_API_KEY"] = conf_loader.attempt_load_param("open-weather-api-key")
    os.environ["QQ_MAIL_KEY"] = conf_loader.attempt_load_param("qq-mail-key")
    os.environ["TAROT_API_KEY"] = conf_loader.attempt_load_param("tarot-api-key")
    os.environ["QQ_EMAIL_ADDRESS"] = conf_loader.attempt_load_param("qq-email-address")
    # 初始化openai大脑
    client = OpenAI()

    base_code = """
    class MainScorer:
        def __init__(self, conf_loader: YamlConfigLoader):
            self.conf_loader = conf_loader
            self.reid_map = defaultdict(dict)
    
        def clean(self):
            self.reid_map = defaultdict(dict)
    
        def steady_score(self, all_sequence: typing.Sequence[BaseDetResults]):
            for num, targets in enumerate(all_sequence):
                for target in targets:
                    # 非第一次出现
                    if target.reid in self.reid_map:
                        self.reid_map[target.reid]['end'] = num
                        self.reid_map[target.reid]['count'] += 1
                        self.reid_map[target.reid]['prior'] = 0
                    # 第一次出现
                    else:
                        self.reid_map[target.reid]['square'] = target.area
                        self.reid_map[target.reid]['start'] = num
                        self.reid_map[target.reid]['end'] = num
                        self.reid_map[target.reid]['count'] = 1
                        self.reid_map[target.reid]['prior'] = 0
    
        def rank_score(self, all_sequence: typing.Sequence[BaseDetResults]) -> defaultdict:
            raise NotImplementedError
            
    class BaseDetResults(metaclass=ABCMeta):
        max_num = 0
        def __init__(self, targets: Union[Sequence[Target], None], frame_data:np.ndarray=None):
            self._frame_num = None
            self._targets = list(sorted(targets, key=lambda target: target.bbox[0])) if targets is not None else None
            self._frame_data = frame_data
            self.has_target = True if self._targets else False
            self.start_num = 0
    
        def mark_value(self):
            self.current_num = BaseDetResults.max_num
            BaseDetResults.max_num += 1
    
        @property
        def targets(self) -> Union[Sequence[Target], None]:
            return self._targets
    
        @targets.setter
        def targets(self, new_targets):
            self._targets = new_targets
    
        @property
        def frame_data(self) -> np.ndarray:
            return self._frame_data
    
        @frame_data.setter
        def frame_data(self, new_data):
            self._frame_data = new_data
    
        @property
        def frame_num(self) -> int:
            return self._frame_num
    
        @frame_num.setter
        def frame_num(self, new_data):
            self._frame_num = new_data
    
        def __len__(self):
            return len(self._targets) if self._targets is not None else 0
    
        def __bool__(self):
            return bool(len(self._targets) if self._targets is not None else 0)
    
        def __iter__(self):
            return self
    
        def __next__(self):
            if self.start_num >= len(self):
                self.start_num = 0
                raise StopIteration()
            target = self._targets[self.start_num]
            self.start_num += 1
            return target
    
        def __getitem__(self, index):
            return self._targets[index]
    
        def get_embeddings(self):
            emb = np.stack([t._embedding for t in self._targets])
            return emb     
            
    class Target(metaclass=ABCMeta):
        def __init__(self, box: typing.Sequence[int], conf: float):
            self._bbox = copy.copy(box)
            self._conf = conf
            self._embedding = None  # 目标对应的embedding特征
            self._reid = -1  # 目标的reid编号
            self._classid = None  # 目标库召回后的编号
            self._maxsim = None  # 与库内目标召回的最大相似度
            self._classname = None  # 类别名称 一般直接以人名
            self._data = None  # 该目标对应的原始数据
            self._virtual = False  # 这个参数是控制是否是虚拟目标，虚拟目标指代的窗口滑动算法进行填充的目标。
            self._hit = False  # 是否是注册库内的命中目标
            self._prior = 1.0  # 目标的优先级
            self._frame_num = 0 # 目标属于的帧数
    
        @property
        def height(self) -> float:
            return self._bbox[3] - self._bbox[1]
    
        @property
        def width(self) -> float:
            return self._bbox[2] - self._bbox[0]
    
        @property
        def bbox(self) -> Sequence[int]:
            return self._bbox
    
        @bbox.setter
        def bbox(self, new_bbox):
            self._bbox = new_bbox
    
        @property
        def conf(self) -> float:
            return self._conf
    
        @property
        def center(self) -> typing.Tuple[float, float]:
            return (self._bbox[0] + self._bbox[2]) / 2, (self._bbox[1] + self._bbox[3]) / 2
    
        def get_shape(self) -> typing.Tuple[float, float]:
            return self.width, self.height
    
        @property
        def area(self):
            return self.width * self.height
    
        @property
        def feature(self):
            return self._embedding
    
        @feature.setter
        def feature(self, embedding):
            self._embedding = embedding
    
        @property
        def reid(self):
            return self._reid
    
        @reid.setter
        def reid(self, reid):
            self._reid = reid
    
        @property
        def classid(self):
            return self._classid
    
        @classid.setter
        def classid(self, classid):
            self._classid = classid
    
        @property
        def maxsim(self):
            return self._maxsim
    
        @maxsim.setter
        def maxsim(self, maxsim):
            self._maxsim = maxsim
    
        @property
        def classname(self):
            return self._classname
    
        @classname.setter
        def classname(self, classname):
            self._classname = classname
    
        @property
        def hit(self):
            return self._hit
    
        @hit.setter
        def hit(self, new_hit):
            self._hit = new_hit
    
        @property
        def data(self):
            return self._data
    
        @data.setter
        def data(self, new_data):
            self._data = new_data
    
        @property
        def virtual(self):
            return self._virtual
    
        @virtual.setter
        def virtual(self, value):
            self._virtual = value
    
        def __eq__(self, other):
            return self.reid == other.reid
    
        @property
        def prior(self):
            return self._prior
    
        @prior.setter
        def prior(self, new_prior):
            self._prior = new_prior           
    """

    system_content = (f"请帮我参考案例编写新代码。这里我提供一个抽象类的编程范式，现在你需要根据我的需求实现我的抽象类。下面是参考的代码：{base_code};其中实现的需求是"
                      f"输入一个BaseDetResults列表，BaseDetResults是Target对象的列表。Target是从视频帧中通过目标检测得到的目标对象，并且得到了对象的各种基础和图像信息。"
                      f"现在需要综合为这批Target进行打分。其中steady_score是计算每个目标Target的出现次数等信息，rank_score是按照自定义规则实现的打分规则。"
                      f"要求输出的只有代码，包含一个完整的实现类")
    request1 = "现在帮我实现一个新的策略类，要求rank_score根据帧序列中每个reid平均最大面积和稳定性进行打分。"
    answer1 = """
        class BaseScorer(MainScorer):
    
            def __init__(self, conf_loader: YamlConfigLoader):
                super().__init__(conf_loader)
            def rank_score(self, all_sequence: typing.Sequence[BaseDetResults]) -> defaultdict:
                # 根据前序、中序和后序三批数据 统计每个ReID的起始点
                for num, targets in enumerate(all_sequence):
                    for target in targets:
                        # 非第一次出现
                        if target.reid in self.reid_map:
                            self.reid_map[target.reid]['end'] = num
                            self.reid_map[target.reid]['count'] += 1
                            self.reid_map[target.reid]['square'] += target.area
                            self.reid_map[target.reid]['prior'] = 0
                # 统计一下三批内的reid平均最大面积
                max_avg_area = max(
                    [value["square"] / value["count"] for value in self.reid_map.values()]) if self.reid_map else 1e-6
                # 统计reid出现频率 既考虑每个reid的首尾间隔差值 也考虑批内这个reid出现的次数 也就是出现多且首尾间隔大的优先出
                for key, value in list(self.reid_map.items()):
                    area_ratio = value["square"] / (value["count"] * max_avg_area)
                    self.reid_map[key]['freq'] = (value['end'] - value['start']) * value['count'] / math.pow(
                        len(all_sequence), 2) * area_ratio
                return self.reid_map
    """
    request2 = "现在帮我实现一个新的规则，要求rank_score根据目标距离右边的距离来打分，越靠右的分越高。"
    messages_CM = [{"role": "system", "content": system_content},
                   {"role": "user", "name": "example1_user", "content": request1},
                   {"role": "assistant", "name": "example1_assistant", "content": answer1},
                   {"role": "user", "name": "example_user", "content": request2}]


    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages_CM,
    )

    response_message = response.choices[0].message
    print(response_message.content)


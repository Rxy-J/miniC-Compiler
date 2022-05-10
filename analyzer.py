#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：analyzer.py
@Author ：OrangeJ
@Date ：2022/5/9 14:30
"""

import re
import sys
import os
import hashlib

from enum import Enum
from json import JSONEncoder
from typing import Union, Any
from graphviz import Digraph

from yacc import Node, NodeType


class Sentence_Type(Enum):
    DEFINE = 0
    DECLARE = 1
    JMP = 2
    IJMP = 3


class CustomJsonEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Sentence):
            return o.__json__()


class Sentence:
    def __init__(self, sentence_type: Sentence_Type, value: str, lineno: int, label: str = None, info: dict = None):
        if info is None:
            info = {}
        self.sentence_type = sentence_type
        self.value = value
        self.lineno = lineno
        self.label = label
        self.info = info

    def __repr__(self) -> str:
        return f"sentence_type->{self.sentence_type.value}, " \
               f"value->{self.value}, " \
               f"lineno->{self.lineno}, " \
               f"label->{self.label}, " \
               f"info->{self.info}"

    def __json__(self) -> dict:
        return {
            "sentence_type": self.sentence_type.value,
            "value": self.value,
            "lineno": self.lineno,
            "label": self.label,
            "info": self.info
        }


class Analyzer:

    def __init__(self, ast: Union[Node, dict]):
        """
        Excepted get a Node of yacc.Yacc.ast or a dict which is transformed from yacc.Yacc.ast

        :param ast: Node or dict
        """
        self.__ast = ast
        if not isinstance(self.__ast, (Node, dict)):
            raise TypeError(f"Excepted Node or dict, get {type(ast)}")
        if isinstance(self.__ast, Node):
            self.__ast_type = 0
        else:
            self.__ast_type = 1
        # each element is a dict that contains block_id and variable_definition
        self.__variable_stack = []
        # key is function name and value is a dict that contains return type, parameters and entry label
        self.__function_table = {}
        # this two stack is used to storage jump label for logical calculation
        self.__true_stack = []
        self.__false_stack = []
        # this two stack is used to storage jump label for loop, mainly for break and continue
        self.__loop_stack = []
        self.__leave_stack = []
        #
        self.__result = []

    def __error(self, msg: str, lineno: int):
        print(f"[ERROR] [{lineno}]: {msg}\n")

    def __warn(self, msg: str, lineno: int):
        print(f"[WARN ] [{lineno}]: {msg}\n")

    def __info(self, msg: str, lineno: int):
        print(f"[INFO ] [{lineno}]: {msg}\n")


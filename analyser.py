#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：miniCC 
@File ：analyser.py
@Author ：OrangeJ
@Date ：2022/5/9 14:30 
'''

import json
import re
import sys
import os

import hashlib

from typing import Union
from graphviz import Digraph
from yacc import Node, NodeType, CustomEncoder


class AST_Parser:
    """
    An AST parser for yacc.Yacc
    """

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
        self.__symbol_table = []
        self.__result = []

if __name__ == "__main__":
    AST_Parser(1)

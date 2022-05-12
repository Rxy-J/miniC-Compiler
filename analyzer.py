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

GLOBAL_VAR = "@"
LOCAL_VAR = "%"


class Sentence_Type(Enum):
    DEFINE_VAR = 0
    DEFINE_ARRAY = 1
    DEFINE_FUNC = 2
    DECLARE_FUNC = 3
    JMP = 2
    IJMP = 3


class CustomJsonEncoder(JSONEncoder):
    """
    For Class Sentence
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, Sentence):
            return o.__json__()


class Sentence:
    """
    To Storage Analyze Result
    The format of result closes to IR
    """

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


class Symbol:
    def __init__(self, value: str, symbol_type: str, reg: str, size: int = None, dimension: list = None,
                 lineno: int = 0, init_value: str = None, func_paras: list=None):
        self.value = value
        self.symbol_type = symbol_type
        self.reg = reg
        self.size = size
        self.dimension = dimension
        self.lineno = lineno
        self.init_value = init_value
        self.func_paras = func_paras

    def __json__(self):
        return {
            "value": self.value,
            "symbol_type": self.symbol_type,
            "reg": self.reg,
            "size": self.size,
            "dimension": self.dimension,
            "init_value": self.init_value
        }


class Analyzer:

    def __init__(self, ast: Node):
        """
        Excepted get a Node of yacc.Yacc.ast

        :param ast: An AST
        """
        self.__ast = ast
        # each element is a dict that contains block_id and variable_definition
        self.__variable_stack: list[dict[str:Symbol]] = []
        self.__curr_var_table = {}
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
        self.counter = 0

    def __accept(self, i: Node, node_type: NodeType) -> bool:
        """

        :param i:
        :param node_type:
        :return:
        """
        if i.node_type is node_type:
            return True
        return False

    def __error(self, msg: str, lineno: int):
        """

        :param msg:
        :param lineno:
        :return:
        """
        print(f"[ERROR] [{lineno}]: {msg}\n")

    def __warn(self, msg: str, lineno: int):
        """

        :param msg:
        :param lineno:
        :return:
        """
        print(f"[WARN ] [{lineno}]: {msg}\n")

    def __info(self, msg: str, lineno: int):
        """

        :param msg:
        :param lineno:
        :return:
        """
        print(f"[INFO ] [{lineno}]: {msg}\n")

    def __check_name(self, name: str) -> int:
        """
        check if this name has already appeared in variable definition stack.

        :param name: target name
        :return: if it's defined at first time will return -1, else will return a number that can avoid redefinition.
        """
        check = -1
        for i in self.__variable_stack:
            if name in i.keys():
                check = self.counter
                self.counter += 1
                return check
        return check

    def __check_var_redefinition(self, i: Union[Node, Symbol]) -> bool:
        """
        check if this variable has been already defined

        :param i:
        :return:
        """
        if i.value in self.__curr_var_table.keys():
            last = self.__curr_var_table.get(i.value)
            self.__error(f"Redefinition of {i.value}, it was defined in line {last.lineno}", i.lineno)
            return False
        return True

    def __check_func_redefinition(self, i: Union[Node, Symbol]) -> bool:
        """
        check if this function has been already defined (only check name, does not contain parameters)

        :param i:
        :return:
        """
        return i.value in self.__function_table.keys()

    def __set_reg(self, i: str, global_var: bool = False) -> str:
        """
        get a reg name, follow the format definition of LLVM

        :param i: reg base name
        :param global_var: is a global variable
        :return: return a reg
        """
        check = self.__check_name(i)
        if global_var:
            if check < 0:
                return f"{GLOBAL_VAR}{i}"
            else:
                return f"{GLOBAL_VAR}{i}{check}"
        else:
            if check < 0:
                return f"{LOCAL_VAR}{i}"
            else:
                return f"{LOCAL_VAR}{i}{check}"

    def __insert_var_table(self, i: Symbol) -> bool:
        """
        insert variable definition to current variable table, check redefinition

        :param i:
        :return:
        """
        self.__curr_var_table[i.value] = i
        return self.__check_var_redefinition(i)

    def __insert_func_table(self, i: Symbol) -> bool:
        """
        insert function definition, check function overload and redefinition

        :param i:
        :return:
        """
        if self.__check_func_redefinition(i):
            if isinstance(self.__function_table[i.value], list):
                for j in self.__function_table[i.value]:
                    j: Symbol
                    if i.symbol_type == j.symbol_type and len(j.func_paras) == len(i.func_paras):
                        flag = True
                        for k in range(len(j.func_paras)):
                            if j.func_paras[k]['type'] != i.func_paras[k]['type']:
                                flag = False
                                break
                        if flag:
                            self.__error(f"Redefine of function {i.value}, already defined in {j.lineno}", i.lineno)
                            return False
            else:
                j: Symbol = self.__function_table[i.value]
                if i.symbol_type == j.symbol_type and len(j.func_paras) == len(i.func_paras):
                    flag = True
                    for k in range(len(j.func_paras)):
                        if j.func_paras[k]['type'] != i.func_paras[k]['type']:
                            flag = False
                            break
                    if flag:
                        self.__error(f"Redefine of function {i.value}, already defined in {j.lineno}", i.lineno)
                        return False
        return True

    def __push_var_table(self):
        """
        storage last block's variable table

        :return: None
        """
        self.__variable_stack.append(self.__curr_var_table)
        self.__curr_var_table = {}

    def __pop_var_table(self):
        """
        pop useless variable table

        :return: None
        """
        if self.__variable_stack:
            self.__curr_var_table = self.__variable_stack[-1]
            self.__variable_stack.pop()

    def analysis(self):
        """
        main entry for analysis

        :return:
        """
        if self.__ast.node_type != NodeType.ROOT:
            self.__error(f"Excepted AST start with ROOT, Found {self.__ast.node_type.value}", 0)
            sys.exit(9009)
        program: list[Node] = self.__ast.info['program']
        self.__curr_var_table = {}
        self.__curr_var_table.__hash__()
        for i in program:
            if i.node_type is NodeType.INT_VAR:
                sent, symb = self.__a_define_var(i, True)
                self.__check_var_redefinition(symb)
                self.__insert_var_table(symb)
                self.__result.append(sent)
            elif i.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(i, True)
                self.__insert_var_table(symb)
                self.__result.append(sent)
            elif i.node_type is (NodeType.INT_FUNC, NodeType.VOID_FUNC):
                sent, symb = self.__a_define_function(i)

    def __a_define_var(self, i: Node, global_var: bool = False) -> tuple[Sentence, Symbol]:
        """


        :param i:
        :param global_var:
        :return:
        """
        var = Sentence(sentence_type=Sentence_Type.DEFINE_VAR, value=i.value, lineno=i.lineno, label=i.node_id)
        var.info = {
            "type": "int",
            "size": 32
        }
        reg = self.__set_reg(i.value, global_var)
        symbol = Symbol(value=i.value, symbol_type="int var", reg=reg, lineno=i.lineno)
        return var, symbol

    def __a_define_array(self, i: Node, global_var: bool = False) -> tuple[Sentence, Symbol]:
        """


        :param i:
        :param global_var:
        :return:
        """
        array = Sentence(sentence_type=Sentence_Type.DEFINE_ARRAY, value=i.value, lineno=i.lineno, label=i.node_id)
        array.info = {
            "type": "int",
            "size": 32,
            "dimension": i.info['size'],
            "dimension_info": []
        }
        for j in range(i.info['size']):
            array.info['dimension_info'].append(i.info(str(j)).value)
        reg = self.__set_reg(i.value, global_var)
        symbol = Symbol(value=i.value, symbol_type="int array", reg=reg, size=array.info['dimension'],
                        dimension=array.info['dimension_info'], lineno=i.lineno)
        return array, symbol

    def __a_define_function(self, i: Node) -> tuple[Sentence, Symbol]:
        """
        Process definition of function. Be careful, this function will auto insert sentence and symbol to
        result and table. If this function can be defined, it will process function body automatically(If it has).

        The return value of this function only for tracking.

        DO NOT INSERT TO RESULT AND TABLE.

        :param i: A function Node
        :return:
        """
        if i.node_type is NodeType.INT_FUNC:
            func_type = "int"
        else:
            func_type = "void"
        func = Sentence(sentence_type=Sentence_Type.DEFINE_FUNC, value=i.value, lineno=i.lineno)
        func.info = {
            "type": func_type,
            "paras": []
        }
        func_paras = []
        # process parameters of function
        for i in i.info['paras']:
            if i.node_type is NodeType.INT_VAR:
                sent, symb = self.__a_define_var(i, True)
                self.__check_var_redefinition(symb)
                self.__curr_var_table[symb.value] = symb
                func.info['paras'].append(sent)
                func_paras.append({
                    "type": "int var",
                    "value": i.value
                })
            elif i.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(i, True)
                self.__check_var_redefinition(symb)
                self.__curr_var_table[symb.value] = symb
                func.info['paras'].append(sent)
                func_paras.append({
                    "type": "int array",
                    "value": i.value
                })
        # insert to result
        self.__result.append(func)
        symb = Symbol(i.value, symbol_type="int func", reg="", lineno=i.lineno, func_paras=func_paras)
        if self.__insert_func_table(symb):  # if function has been defined successfully (include Overload)
            self.__a_get_function_body(i.info['funcbody'])
        return func, symb

    def __a_get_function_body(self, i: Node) -> list[tuple[Sentence, Symbol]]:
        pass

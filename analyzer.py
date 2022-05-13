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
    For Class Sentence and Class Symbol
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, Sentence):
            return o.__json__()
        elif isinstance(o, Symbol):
            return o.__json__()


class Sentence:
    """
    To Storage Analyze Result
    The format of result closes to IR
    """

    def __init__(self,
                 sentence_type: Sentence_Type,
                 value: str,
                 lineno: int,
                 label: str = None,
                 reg: str = None,
                 info: dict = None):
        if info is None:
            info = {}
        self.sentence_type = sentence_type
        self.value = value
        self.lineno = lineno
        self.label = label
        self.reg = reg
        self.info = info

    def __repr__(self) -> str:
        return f"sentence_type->{self.sentence_type.name}, " \
               f"value->{self.value}, " \
               f"lineno->{self.lineno}, " \
               f"label->{self.label}, " \
               f"reg->{self.reg}, " \
               f"info->{self.info}"

    def __json__(self) -> dict:
        return {
            "sentence_type": self.sentence_type.name,
            "value": self.value,
            "lineno": self.lineno,
            "label": self.label,
            "reg": self.reg,
            "info": self.info
        }


class Symbol:
    def __init__(self,
                 value: str,
                 symbol_type: str,
                 reg: str = None,
                 size: int = None,
                 dimension: list = None,
                 lineno: int = 0,
                 init_value: str = None,
                 func_paras: list = None,
                 func_entry: str = None,
                 func_leave: str = None):
        self.value = value
        self.symbol_type = symbol_type
        self.reg = reg
        self.size = size
        self.dimension = dimension
        self.lineno = lineno
        self.init_value = init_value
        self.func_paras = func_paras
        self.func_entry = func_entry
        self.func_leave = func_leave

    def __repr__(self):
        return f"value->{self.value}, " \
               f"symbol_type->{self.symbol_type}"

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
        self.__ast: Node = ast
        # each element is a dict that contains block_id and variable_definition
        self.__variable_stack: list[dict[str:Symbol]] = []
        self.__curr_var_table: dict[str:Symbol] = {}
        # key is function name and value is a dict that contains return type, parameters and entry label
        self.__function_table: dict[str:list[Symbol]] = {}
        #
        self.__last_label: str = None
        self.__true_leave = []
        self.__false_leave = []
        self.__condition_entry = []
        self.__block_leave = []
        #
        self.__result: list[Sentence] = []
        self.__reg_counter: int = 0
        self.__label_counter: int = 0

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
        # self.__curr_var_table.__hash__()
        for i in program:
            if i.node_type is NodeType.INT_VAR:
                sent, symb = self.__a_define_var(i, True)
                self.__insert_var_table(symb)
                self.__result.append(sent)
            elif i.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(i, True)
                self.__insert_var_table(symb)
                self.__result.append(sent)
            elif i.node_type in (NodeType.INT_FUNC, NodeType.VOID_FUNC):
                sent, symb = self.__a_define_function(i)
        print(self.__variable_stack)
        print(self.__curr_var_table)
        print(self.__function_table)
        for i in self.__result:
            print(i)

    def __error(self, msg: str, lineno: int):
        """

        :param msg:
        :param lineno:
        :return:
        """
        print(f"[ERROR] [{lineno}]: {msg}")

    def __warn(self, msg: str, lineno: int):
        """

        :param msg:
        :param lineno:
        :return:
        """
        print(f"[WARN ] [{lineno}]: {msg}")

    def __info(self, msg: str, lineno: int):
        """

        :param msg:
        :param lineno:
        :return:
        """
        print(f"[INFO ] [{lineno}]: {msg}")

    def __set_label(self, label_prefix: str = "L"):
        """
        

        :param label_prefix:
        :return:
        """
        self.__label_counter += 1
        return f"{label_prefix}{self.__label_counter}"

    def __set_reg(self, target_name: str, global_var: bool = False) -> str:
        """
        get a reg name, follow the format definition of LLVM

        :param target_name: reg base name
        :param global_var: is a global variable
        :return: return a reg
        """
        check = self.__check_name(target_name)
        if global_var:
            if check < 0:
                return f"{GLOBAL_VAR}{target_name}"
            else:
                return f"{GLOBAL_VAR}{target_name}{check}"
        else:
            if check < 0:
                return f"{LOCAL_VAR}{target_name}"
            else:
                return f"{LOCAL_VAR}{target_name}{check}"

    def __check_name(self, name: str) -> int:
        """
        check if this name has already appeared in variable definition stack.

        :param name: target name
        :return: if it's defined at first time will return -1, else will return a number that can avoid redefinition.
        """
        check = -1
        for i in self.__variable_stack:
            if name in i.keys():
                check = self.__reg_counter
                self.__reg_counter += 1
                return check
        return check

    def __check_var_redefinition(self, var: Union[Node, Symbol]) -> bool:
        """
        check if this variable has been already defined

        :param var:
        :return:
        """
        if var.value in self.__curr_var_table.keys():
            last = self.__curr_var_table.get(var.value)
            self.__error(f"Redefinition of {var.value}, it was defined in line {last.lineno}", var.lineno)
            return False
        return True

    def __check_func_redefinition(self, func: Union[Node, Symbol]) -> bool:
        """
        check if this function has been already defined (only check name, does not contain parameters)

        :param func:
        :return:
        """
        return func.value in self.__function_table.keys()

    def __insert_var_table(self, sym: Symbol) -> bool:
        """
        insert variable definition to current variable table, check redefinition

        :param sym:
        :return:
        """
        if self.__check_var_redefinition(sym):
            self.__curr_var_table[sym.value] = sym
            return False
        return True

    def __insert_func_table(self, sym: Symbol) -> bool:
        """
        insert function definition, check function overload and redefinition

        :param sym:
        :return:
        """
        if self.__check_func_redefinition(sym):
            # check is overload or total redefinition
            for j in self.__function_table[sym.value]:
                j: Symbol
                if sym.symbol_type == j.symbol_type and len(j.func_paras) == len(sym.func_paras):
                    flag = True
                    for k in range(len(j.func_paras)):
                        if j.func_paras[k]['type'] != sym.func_paras[k]['type']:
                            flag = False
                            break
                    if flag:
                        self.__error(f"Redefine of function {sym.value}, already defined in {j.lineno}", sym.lineno)
                        return False
        self.__function_table[sym.value].append(sym)
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

    def __a_define_var(self, var_node: Node, global_var: bool = False) -> tuple[Sentence, Symbol]:
        """


        :param var_node:
        :param global_var:
        :return:
        """
        reg = self.__set_reg(var_node.value, global_var)
        symbol = Symbol(value=var_node.value, symbol_type="int var", reg=reg, lineno=var_node.lineno)
        var = Sentence(sentence_type=Sentence_Type.DEFINE_VAR, value=var_node.value, lineno=var_node.lineno, reg=reg)
        var.info = {
            "type": "int",
            "size": 32
        }
        return var, symbol

    def __a_define_array(self, array_node: Node, global_var: bool = False) -> tuple[Sentence, Symbol]:
        """


        :param array_node:
        :param global_var:
        :return:
        """
        reg = self.__set_reg(array_node.value, global_var)
        symbol = Symbol(value=array_node.value, symbol_type="int array", reg=reg, lineno=array_node.lineno)
        array = Sentence(sentence_type=Sentence_Type.DEFINE_ARRAY, value=array_node.value, lineno=array_node.lineno,
                         reg=reg)
        array.info = {
            "type": "int",
            "size": 32,
            "dimension": array_node.info['size'],
            "dimension_info": []
        }
        for j in range(array_node.info['size']):
            if array_node.info[str(j)] is None:
                array.info['dimension_info'].append(None)
            else:
                array.info['dimension_info'].append(array_node.info[str(j)].value)
        symbol.size = array.info['dimension']
        symbol.dimension = array.info['dimension_info']
        return array, symbol

    def __a_define_function(self, function: Node) -> tuple[Sentence, Symbol]:
        """
        Process definition of function. Be careful, this function will auto insert sentence and symbol to
        result and table. If this function can be defined, it will process function body automatically(If it has).

        The return value of this function only for tracking.

        DO NOT INSERT TO RESULT AND TABLE.

        :param function: A function Node
        :return:
        """
        if function.node_type is NodeType.INT_FUNC:
            func_type = "int"
        else:
            func_type = "void"
        func = Sentence(sentence_type=Sentence_Type.DEFINE_FUNC, value=function.value, lineno=function.lineno)
        func.info = {
            "type": func_type,
            "paras": []
        }
        func_paras = []
        self.__push_var_table()
        # process parameters of function
        for para in function.info['paras']:
            if para.node_type is NodeType.INT_VAR:
                sent, symb = self.__a_define_var(para, True)
                self.__check_var_redefinition(symb)
                self.__curr_var_table[symb.value] = symb
                func.info['paras'].append(sent)
                func_paras.append({
                    "type": "int var",
                    "value": para.value
                })
            elif para.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(para, True)
                self.__check_var_redefinition(symb)
                self.__curr_var_table[symb.value] = symb
                func.info['paras'].append(sent)
                func_paras.append({
                    "type": "int array",
                    "value": para.value
                })
        self.__result.append(func)

        # generate symbol info
        func_entry = self.__set_label()
        func_leave = self.__set_label()
        symb = Symbol(function.value, symbol_type="int func", lineno=function.lineno,
                      func_paras=func_paras, func_entry=func_entry, func_leave=func_leave)
        func.label = symb.func_entry
        if self.__insert_func_table(symb):  # if function has been defined successfully (include Overload)
            func_sentences = self.__a_statement(function.info['funcbody'])
            if not len(func_sentences):
                self.__warn(f"Empty function {symb.value}", symb.lineno)
        return func, symb

    def __a_statement(self, statement: Node) -> list[Sentence]:
        if statement.node_type is not NodeType.BLOCK:
            self.__error(f"Excepted function body Node's type is Block, Found {statement.node_type.name}",
                         statement.lineno)
        func_sents = []
        for sub in statement.info['subprogram']:
            sub: Node  # to
            if sub.node_type is NodeType.INT_VAR:
                sent, symb = self.__a_define_var(sub)
                self.__insert_var_table(symb)
                func_sents.append(sent)
            elif sub.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(sub)
                self.__insert_var_table(symb)
                func_sents.append(sent)
            elif sub.node_type is NodeType.WHILE:
                pass

            elif sub.node_type is NodeType.IF:
                pass

            elif sub.node_type is NodeType.IF:
                pass

        return []

    def __a_while(self, while_node: Node):
        self.__condition_entry.append(self.__set_label() if self.__last_label is None else self.__last_label)
        self.__block_leave.append(self.__set_label())
        self.__last_label = self.__block_leave[-1]

        condition_sentences = self.__a_expr(while_node.info['condition'])
        self.__push_var_table()
        statement_sentences = self.__a_statement(while_node.info['statement'])
        self.__pop_var_table()

    def __a_expr(self, expr: Node) -> list[Sentence]:
        pass

    def __a_logic_expr(self, logic_expr: Node) -> list[Sentence]:
        pass

    # TODO: TRY!
    #       TO!
    #       FIGURE!
    #       OUT!
    #       HOW!
    #       TO!
    #       PASS!
    #       ALL!
    #       JUMP!
    #       LABEL!
    #       CORRECTLY!
    #       BEFORE!
    #       15th Mar

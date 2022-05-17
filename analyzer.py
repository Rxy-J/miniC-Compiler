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
    DEFINE_GLOBAL_VAR = 0
    DEFINE_LOCAL_VAR = 1
    DEFINE_GLOBAL_ARRAY = 1
    DEFINE_LOCAL_ARRAY = 2
    DEFINE_FUNC = 3
    DECLARE_FUNC = 4
    JMP = 5
    IF_JMP = 6
    ASSIGN = 7
    ADD = 8
    MINUS = 9
    TIMES = 10
    DIVIDE = 11
    MOD = 12
    EQ = 13
    NEQ = 14
    GT = 15
    GEQ = 16
    LT = 17
    LEQ = 18
    NOT = 19
    NEGATIVE = 20
    L_SELF_PLUS = 21
    R_SELF_PLUS = 22
    L_SELF_MINUS = 23
    R_SELF_MINUS = 24
    ZEXT = 25
    # DONT_PARSER = 25


class Reg_Type:
    INT_REG = "int"
    TMP_REG = "tmp_reg"


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
        # jump control label
        self.__last_label: str = None
        self.__true_leave: str = None
        self.__false_leave: str = None
        self.__condition_entry: str = None
        self.__block_leave: str = None
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
                sent, symb = self.__a_define_var(i)
                sent.sentence_type = Sentence_Type.DEFINE_GLOBAL_VAR
                self.__insert_var_table(symb)
                self.__result.append(sent)
            elif i.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(i)
                sent.sentence_type = Sentence_Type.DEFINE_GLOBAL_ARRAY
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

    def __set_reg(self, target_name: str) -> str:
        """
        get a reg name, follow the format definition of LLVM

        :param target_name: reg base name
        :return: return a reg
        """
        check = self.__check_name(target_name)
        if check < 0:
            return f"{target_name}"
        else:
            return f"{target_name}{check}"

    def __find_var_define(self, var_node: Node) -> Symbol:
        """


        :param var_node:
        :return:
        """
        var = self.__curr_var_table.get(var_node.value, None)
        if var is None:
            for i in self.__variable_stack:
                var = i.get(var_node.value, None)
                if var is not None:
                    break
        if var is None:
            self.__error(f"Undefined variable {var_node.value}", var_node.lineno)
        return var

    def __process_var_use(self, var_node: Node) -> dict:
        """

        :param var_node:
        :return:
        """
        error_var_dict = {
            "type": None,
            "reg": None,
        }
        if var_node.node_type is NodeType.NUM:
            return {
                "type": "num",
                "value": var_node.value,
                "size": 32
            }
        elif var_node.node_type is NodeType.IDENT:
            sym = self.__find_var_define(var_node)
            if sym is None:
                return error_var_dict
            else:
                return {
                    "type": "ident",
                    "reg": sym.reg,
                    "size": 32,
                    "dimension": None,
                }
        else:
            sym = self.__find_var_define(var_node)
            if sym is None:
                return error_var_dict
            elif sym.symbol_type != "int array":
                self.__error(f"{sym.symbol_type} is not subscriptable", var_node.lineno)
                return error_var_dict
            else:
                var_dimension = [var_node.info[str(i)] for i in range(var_node.info['size'])]
                define_dimension = sym.dimension
                if len(var_dimension) > len(define_dimension):
                    self.__error(
                        f"The dimension of {sym.value} is {len(define_dimension)}, but try to use {len(var_dimension)} dimensions",
                        var_node.lineno)
                    return error_var_dict
                else:
                    for i in range(len(var_dimension)):
                        if not (var_dimension[i] < define_dimension[i]):
                            self.__error(
                                f"The size of {sym.value} in dimension {i} is {define_dimension[i]}, but try to use {var_dimension[i]}",
                                var_node.lineno)
                            return error_var_dict
                return {
                    "type": "ident",
                    "reg": sym.reg,
                    "size": 32,
                    "dimension": var_dimension
                }

    def __process_left_val(self, expr: Node) -> dict:
        if expr.node_type in (NodeType.NUM, NodeType.IDENT, NodeType.ARRAY):
            return self.__process_var_use(expr)
        else:
            return self.__a_expr(expr)

    def __process_right_val(self, expr: Node) -> dict:
        if expr.node_type in (NodeType.NUM, NodeType.IDENT, NodeType.ARRAY):
            return self.__process_var_use(expr)
        else:
            return self.__a_expr(expr)

    def __convert_i32_i1(self, target_reg: dict, source_reg: dict, lineno: int = 0) -> Sentence:
        trans = Sentence(sentence_type=Sentence_Type.NEQ, value="", lineno=lineno)
        trans.info['lvar'] = source_reg
        trans.info['rvar'] = {
            "type": "num",
            "value": "0",
            "size": 32
        }
        trans.info['avar'] = target_reg
        return trans

    def __convert_i1_i32(self, target_reg: dict, source_reg: dict, lineno: int = 0) -> Sentence:
        trans = Sentence(sentence_type=Sentence_Type.ZEXT, value="", lineno=lineno)
        trans.info['lvar'] = source_reg
        trans.info['avar'] = target_reg
        return trans

    def __convert_to_target_length(self, source_reg: dict, target_length: int, lineno: int = 0) -> dict:
        if source_reg['size'] != target_length:
            tmp = {
                "type": Reg_Type.TMP_REG,
                "reg": self.__create_tmp_reg(),
                "size": target_length,
            }
            if target_length == 1:
                trans = self.__convert_i32_i1(tmp, source_reg, lineno)
            else:
                trans = self.__convert_i1_i32(tmp, source_reg, lineno)
            self.__result.append(trans)
            return tmp
        return source_reg

    def __create_jump_sentences(self, reg: dict, true_label: str, false_label: str) -> None:
        pass

    def __create_tmp_reg(self) -> str:
        # FIXME: After finish learn LLVM Language Reference, Create Register
        reg = f"{self.__reg_counter}"
        self.__reg_counter += 1
        return reg

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
        else:
            self.__function_table[sym.value] = []
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

    def __a_define_var(self, var_node: Node) -> tuple[Sentence, Symbol]:
        """


        :param var_node:
        :return:
        """
        reg = self.__set_reg(var_node.value)
        symbol = Symbol(value=var_node.value, symbol_type="int var", reg=reg, lineno=var_node.lineno)
        var = Sentence(sentence_type=Sentence_Type.DEFINE_LOCAL_VAR, value=var_node.value, lineno=var_node.lineno, reg=reg)
        var.info = {
            "type": Reg_Type.INT_REG,
            "size": 32
        }
        return var, symbol

    def __a_define_array(self, array_node: Node) -> tuple[Sentence, Symbol]:
        """


        :param array_node:
        :param global_var:
        :return:
        """
        reg = self.__set_reg(array_node.value)
        symbol = Symbol(value=array_node.value, symbol_type="int array", reg=reg, lineno=array_node.lineno)
        array = Sentence(sentence_type=Sentence_Type.DEFINE_LOCAL_ARRAY, value=array_node.value, lineno=array_node.lineno,
                         reg=reg)
        array.info = {
            "type": Reg_Type.INT_REG,
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
        self.__push_var_table()

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

        # process parameters of function
        for para in function.info['paras']:
            if para.node_type is NodeType.INT_VAR:
                sent, symb = self.__a_define_var(para)
                self.__check_var_redefinition(symb)
                self.__curr_var_table[symb.value] = symb
                func.info['paras'].append(sent)
                func_paras.append({
                    "type": "int var",
                    "value": para.value
                })
            elif para.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(para)
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
            self.__last_label = func_entry
            self.__a_statement(function.info['funcbody'])
            # if not len(func_sentences):
            #     self.__warn(f"Empty function {symb.value}", symb.lineno)

        self.__pop_var_table()
        return func, symb

    def __a_statement(self, statement: Node) -> None:
        if statement.node_type is not NodeType.BLOCK:
            self.__error(f"Excepted function body Node's type is Block, Found {statement.node_type.name}",
                         statement.lineno)

        for sub in statement.info['subprogram']:
            sub: Node  # to
            if sub.node_type is NodeType.INT_VAR:
                sent, symb = self.__a_define_var(sub)
                self.__insert_var_table(symb)
                self.__result.append(sent)
            elif sub.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(sub)
                self.__insert_var_table(symb)
                self.__result.append(sent)
            elif sub.node_type is NodeType.WHILE:
                pass

            elif sub.node_type is NodeType.IF:
                pass

            else:
                self.__a_expr(sub)

    def __a_while(self, while_node: Node) -> list[Sentence]:
        # follow this sequence to storage jump label info
        old_label = (self.__condition_entry,
                     self.__block_leave,
                     self.__true_leave,
                     self.__false_leave)
        self.__condition_entry = self.__set_label() if self.__last_label is None else self.__last_label
        self.__block_leave = self.__set_label()
        self.__true_leave = self.__set_label()
        self.__false_leave = self.__block_leave

        while_sentences: list[Sentence] = []

        condition_sentences = self.__a_logic_expr(while_node.info['condition'])
        # given statement is a sub-block(node_type may not be BLOCK), we need to push stack
        self.__push_var_table()
        statement_sentences = self.__a_statement(while_node.info['statement'])
        # after we left statement process, we need to restore all stack info
        self.__pop_var_table()

        while_sentences.extend(condition_sentences)
        while_sentences.extend(statement_sentences)

        # before leave loop block, should pass loop leave label to next sentence correctly
        self.__last_label = self.__block_leave
        # and then restore all jump control label
        self.__condition_entry, self.__block_leave, self.__true_leave, self.__false_leave = old_label

        return while_sentences

    def __a_expr(self, expr: Node) -> dict:
        """
        use to translate expression to a couple of base calculation sentences

        :param expr:
        :return:
        """
        if expr.node_type is NodeType.ASSIGN:
            curr = Sentence(Sentence_Type.ASSIGN, value="", lineno=expr.lineno)
            # left value
            if expr.info['lvar'].node_type is NodeType.NUM:
                self.__error("Number can't be evaluated", expr.lineno)
                curr.info['lvar'] = {"type": None, "reg": None, "size": None}
            elif expr.info['lvar'].node_type in (NodeType.IDENT, NodeType.ARRAY):
                curr.info['lvar'] = self.__process_var_use(expr.info['lvar'])
            else:
                self.__error("Excepted left identifier of '='", expr.lineno)
                curr.info['lvar'] = {"type": None, "reg": None, "size": None}

            # right value
            curr.info['rvar'] = self.__process_right_val(expr.info['rvar'])
            if curr.info['rvar']['size'] != 32:
                tmp = {
                    "type": Reg_Type.TMP_REG,
                    "reg": self.__create_tmp_reg(),
                    "size": 32
                }
                trans = self.__convert_i1_i32(tmp, curr.info['rvar'])
                self.__result.append(trans)
                curr.info['rvar'] = tmp

            curr.info['avar'] = curr.info['lvar']  # for assignment, the left value is evaluated value
            if self.__last_label:
                curr.label = self.__last_label
                self.__last_label = None
            self.__result.append(curr)
            return curr.info['avar']
        elif expr.node_type is NodeType.UNARY_LEFT:  # ++, --, -, !
            target: Node = expr.info['target']
            lop: Node = expr.info['lop']
            value_pass_reg = self.__create_tmp_reg()
            value_pass = {
                "type": Reg_Type.TMP_REG,
                "reg": value_pass_reg,
                "size": 32
            }
            if target.node_type in (NodeType.IDENT, NodeType.ARRAY):
                rvar = self.__process_var_use(target)
            else:
                self.__error("lvalue required as decrement operand", expr.lineno)
                return {
                    "type": None,
                    "reg": None
                }
            if lop.node_type in (NodeType.SELF_PLUS, NodeType.SELF_MINUS):
                # t = a +/- 1
                if lop.node_type is NodeType.SELF_PLUS:
                    curr = Sentence(Sentence_Type.ADD, value="", lineno=expr.lineno)
                else:
                    curr = Sentence(Sentence_Type.MINUS, value="", lineno=expr.lineno)
                if self.__last_label:
                    curr.label = self.__last_label
                    self.__last_label = None
                curr.info['avar'] = value_pass
                curr.info['lvar'] = rvar
                curr.info['rvar'] = {
                    "type": "num",
                    "value": "1",
                    "size": 32
                }
                self.__result.append(curr)

                # a = t
                curr = Sentence(Sentence_Type.ASSIGN, value="", lineno=expr.lineno)
                curr.info['avar'] = rvar
                curr.info['lvar'] = rvar
                curr.info['rvar'] = value_pass
                self.__result.append(curr)
            else:
                if lop.node_type is NodeType.NEGATIVE:
                    # t = 0 - a
                    curr = Sentence(Sentence_Type.MINUS, value="", lineno=expr.lineno)
                    curr.info['avar'] = value_pass
                    curr.info['lvar'] = {
                        "type": "num",
                        "value": "0",
                        "size": 32
                    }
                    curr.info['rvar'] = rvar
                    self.__result.append(curr)
                else:
                    # t1 = a != 0
                    tmp_info = {
                        "type": Reg_Type.TMP_REG,
                        "reg": self.__create_tmp_reg(),
                        "size": 1
                    }
                    curr = Sentence(Sentence_Type.NEQ, value="", lineno=expr.lineno)
                    curr.info['avar'] = tmp_info
                    curr.info['lvar'] = rvar
                    curr.info['rvar'] = {
                        "type": "num",
                        "value": "0",
                        "size": 32
                    }
                    self.__result.append(curr)
                    # t2 = t1 xor true
                    curr = Sentence(Sentence_Type.XOR, value="", lineno=expr.lineno)
                    curr.info['avar'] = value_pass
                    curr.info['lvar'] = tmp_info
                    curr.info['rvar'] = {
                        "type": "num",
                        "value": "1",
                        "size": 1
                    }
                    value_pass['size'] = 1
                    self.__result.append(curr)
            return value_pass
        elif expr.node_type is NodeType.UNARY_RIGHT:  # ++, --
            target: Node = expr.info['target']
            rop: Node = expr.info['rop']
            value_pass_reg = self.__create_tmp_reg()
            value_pass = {
                "type": Reg_Type.TMP_REG,
                "reg": value_pass_reg,
                "size": 32
            }
            if target.node_type in (NodeType.IDENT, NodeType.ARRAY):
                rvar = self.__process_var_use(target)
            else:
                self.__error("lvalue required as decrement operand", expr.lineno)
                return {
                    "type": None,
                    "reg": None
                }

            # t1 = a
            curr = Sentence(Sentence_Type.ASSIGN, value="", lineno=expr.lineno)
            if self.__last_label:
                curr.label = self.__last_label
                self.__last_label = None
            curr.info['lvar'] = value_pass
            curr.info['avar'] = value_pass
            curr.info['rvar'] = rvar
            self.__result.append(curr)

            # t2 = a +/- 1 or t2 = -a or !a
            tmp_reg = self.__create_tmp_reg()
            tmp_info = {
                "type": Reg_Type.TMP_REG,
                "reg": tmp_reg,
                "size": 32
            }
            if rop.node_type is NodeType.SELF_PLUS:
                curr = Sentence(Sentence_Type.ADD, value="", lineno=expr.lineno)
            else:
                curr = Sentence(Sentence_Type.MINUS, value="", lineno=expr.lineno)
            curr.info['avar'] = tmp_info
            curr.info['lvar'] = rvar
            curr.info['rvar'] = {
                "type": "num",
                "value": "1",
                "size": 32
            }
            self.__result.append(curr)

            # a = t2
            curr = Sentence(Sentence_Type.ASSIGN, value="", lineno=expr.lineno)
            curr.info['avar'] = rvar
            curr.info['lvar'] = rvar
            curr.info['rvar'] = tmp_reg
            self.__result.append(curr)

            return value_pass
        elif expr.node_type is NodeType.LOGIC_AND:
            all_leave_label = self.__set_label()
            l_true_label = self.__set_label()
            and_res_reg = self.__create_tmp_reg()
            and_res = {
                "type": Reg_Type.TMP_REG,
                "reg": and_res_reg,
                "size": 1
            }

            l_reg = self.__process_left_val(expr.info['lvar'])
            if l_reg['size'] != 1:
                l_trans = self.__convert_i32_i1(and_res, l_reg, expr.lineno)
                self.__result.append(l_trans)
            else:
                and_res = l_reg
            self.__create_jump_sentences(and_res, l_true_label, all_leave_label)

            self.__last_label = l_true_label
            r_reg = self.__process_right_val(expr.info['rvar'])
            if r_reg['size'] != 1:
                r_trans = self.__convert_i32_i1(and_res, r_reg, expr.lineno)
                self.__result.append(r_trans)
            else:
                and_res = r_reg

            self.__last_label = all_leave_label
            return and_res
        elif expr.node_type is NodeType.LOGIC_OR:
            all_leave_label = self.__set_label()
            l_false_label = self.__set_label()
            or_res_reg = self.__create_tmp_reg()
            or_res = {
                "type": Reg_Type.TMP_REG,
                "reg": or_res_reg,
                "size": 1
            }

            l_reg = self.__process_left_val(expr.info['lvar'])
            if l_reg['size'] != 1:
                l_trans = self.__convert_i32_i1(or_res, l_reg, expr.lineno)
                self.__result.append(l_trans)
            else:
                or_res = l_reg
            self.__create_jump_sentences(or_res, all_leave_label, l_false_label)

            self.__last_label = l_false_label
            r_reg = self.__process_right_val(expr.info['rvar'])
            if r_reg['size'] != 1:
                r_trans = self.__convert_i32_i1(or_res, r_reg, expr.lineno)
                self.__result.append(r_trans)
            else:
                or_res = r_reg

            self.__last_label = all_leave_label
            return or_res
        else:
            aval_reg_size = 32
            if expr.node_type is NodeType.PLUS:
                curr = Sentence(Sentence_Type.ADD, value="", lineno=expr.lineno)
            elif expr.node_type is NodeType.MINUS:
                curr = Sentence(Sentence_Type.MINUS, value="", lineno=expr.lineno)
            elif expr.node_type is NodeType.TIMES:
                curr = Sentence(Sentence_Type.TIMES, value="", lineno=expr.lineno)
            elif expr.node_type is NodeType.DIVIDE:
                curr = Sentence(Sentence_Type.DIVIDE, value="", lineno=expr.lineno)
            elif expr.node_type is NodeType.MOD:
                curr = Sentence(Sentence_Type.MOD, value="", lineno=expr.lineno)
            elif expr.node_type is NodeType.EQ:
                curr = Sentence(Sentence_Type.EQ, value="", lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.NEQ:
                curr = Sentence(Sentence_Type.NEQ, value="", lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.GT:
                curr = Sentence(Sentence_Type.GT, value="", lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.GEQ:
                curr = Sentence(Sentence_Type.GEQ, value="", lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.LT:
                curr = Sentence(Sentence_Type.LT, value="", lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.LEQ:
                curr = Sentence(Sentence_Type.LEQ, value="", lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.NOT:
                curr = Sentence(Sentence_Type.NOT, value="", lineno=expr.lineno)
            else:  # NUM, IDENT, ARRAY
                return self.__process_var_use(expr)
            l_reg = self.__process_left_val(expr.info['lvar'])
            r_reg = self.__process_right_val(expr.info['rvar'])

            curr.info['lvar'] = self.__convert_to_target_length(l_reg, 32, expr.lineno)
            curr.info['rvar'] = self.__convert_to_target_length(r_reg, 32, expr.lineno)

            aval_reg = self.__create_tmp_reg()
            aval_reg_info = {
                "type": Reg_Type.TMP_REG,
                "reg": aval_reg,
                "size": aval_reg_size
            }
            curr.info['avar'] = aval_reg_info
            if self.__last_label:
                curr.label = self.__last_label
                self.__last_label = None
            self.__result.append(curr)
            return aval_reg_info

    def __a_logic_expr(self, expr: Node, true_leave: str, false_leave: str) -> list[Sentence]:
        """
        it will get a series of sentences from Node:expr which will be processed
        by __a_expr. it take the last sentence's result to make a logic judgement and jump action

        this function can't be used to assignment expression. only for condition process

        :param expr:
        :return:
        """

        logic_sentences: list[Sentence] = []

        main, before, after = self.__a_expr_t(expr)
        i = Sentence(sentence_type=Sentence_Type.IF_JMP, value=true_leave, lineno=0)
        j = Sentence(sentence_type=Sentence_Type.JMP, value=false_leave, lineno=0)

        logic_sentences.extend(main)
        logic_sentences.extend(before)
        logic_sentences.extend(after)
        logic_sentences.append(i)
        logic_sentences.append(j)

        return logic_sentences


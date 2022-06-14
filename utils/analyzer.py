#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：analyzer.py
@Author ：OrangeJ
@Date ：2022/5/9 14:30
"""

import sys
import copy

from enum import Enum
from json import JSONEncoder
from typing import Union, Any, Optional

from utils.yacc import Node, NodeType

GLOBAL = "@"
OTHER = "%"


class Sentence_Type(Enum):
    DEFINE_GLOBAL_VAR = -1
    DEFINE_LOCAL_VAR = 0
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
    ZEXT = 25
    FUNC_END = 26
    CALL = 27
    RETURN = 28
    XOR = 29
    GETPTR = 30
    LOAD = 31
    PHI = 32


class Reg_Type:
    INT_REG = "int"
    VOID_REG = "void"
    TMP_REG = "tmp_reg"


class CustomAnaEncoder(JSONEncoder):
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
                 lineno: int,
                 value: str = "",
                 label: str = None,
                 reg: str = None,
                 info: dict = None):
        if info is None:
            info = {}
        self.sentence_type = sentence_type
        self.lineno = lineno
        self.value = value
        self.label = label
        self.reg = reg
        self.info = info

    def __repr__(self) -> str:
        return f"sentence_type->{self.sentence_type.name}, " \
               f"lineno->{self.lineno}, " \
               f"value->{self.value}, " \
               f"label->{self.label}, " \
               f"reg->{self.reg}, " \
               f"info->{self.info}"

    def __json__(self) -> dict:
        return {
            "sentence_type": self.sentence_type.name,
            "lineno": self.lineno,
            "value": self.value,
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
                 def_from: str = "define",
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
        self.def_from = def_from
        self.func_paras = func_paras
        self.func_entry = func_entry
        self.func_leave = func_leave

    def __repr__(self):
        return f"value->{self.value}, " \
               f"symbol_type->{self.symbol_type}, " \
               f"reg -> {self.reg}, " \
               f"size -> {self.size}, " \
               f"func_paras -> {self.func_paras}, "

    def __json__(self):
        return {
            "value": self.value,
            "symbol_type": self.symbol_type,
            "reg": self.reg,
            "size": self.size,
            "dimension": self.dimension,
            "init_value": self.init_value
        }


PRE_DEFINE_FUNC = {
    "getint": [Symbol("getint", symbol_type='int func', func_paras=[])],
    "getch": [Symbol('getch', symbol_type='int func', func_paras=[])],
    "getarray": [Symbol('getarray', symbol_type='int func',
                       func_paras=[{'type': 'int array', 'value': 'a', 'size': 32, 'dimension': [None]}])],
    "putint": [Symbol('putint', symbol_type='void func',
                     func_paras=[{'type': 'int var', 'value': 'k', 'size': 32}])],
    "putch": [Symbol('putch', symbol_type='void func',
                    func_paras=[{'type': 'int var', 'value': 'c', 'size': 32}])],
    "putarray": [Symbol('putarray', symbol_type='void func',
                       func_paras=[{'type': 'int var', 'value': 'n', 'size': 32},
                                   {'type': 'int array', 'value': 'd', 'size': 32, 'dimension': [None]}])],
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
        self.__function_table.update(PRE_DEFINE_FUNC)
        # jump control label
        self.__last_label: str = None
        self.__condition_entry: str = None
        self.__block_leave: str = None
        self.__func_ret: str = None
        self.__return_reg: dict = None
        #
        self.__result: list[Sentence] = []
        self.__reg_counter: int = 0
        self.__label_counter: int = 0
        # create a stack change flow
        self.__var_stack_flow = []
        self.__fun_stack_flow = []
        self.error = False

    def analysis(self) -> list[Sentence]:
        """
        main entry for analysis

        :return:
        """
        if self.__ast.node_type != NodeType.ROOT:
            self.__error(f"Excepted AST start with ROOT, Found {self.__ast.node_type.value}", 0)
            sys.exit(9009)
        program: list[Node] = self.__ast.info['program']
        self.__variable_stack.append(self.__curr_var_table)
        for i in program:
            if i.node_type is NodeType.INT_VAR:
                sent, symb = self.__a_define_var(i)
                sent.info['reg'] = sent.info['reg'].replace("%", "@")
                symb.reg = sent.info['reg']
                sent.sentence_type = Sentence_Type.DEFINE_GLOBAL_VAR
                self.__insert_var_table(symb)
                self.__result.append(sent)
            elif i.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(i)
                sent.info['reg'] = sent.info['reg'].replace("%", "@")
                symb.reg = sent.info['reg']
                sent.sentence_type = Sentence_Type.DEFINE_GLOBAL_ARRAY
                self.__insert_var_table(symb)
                self.__result.append(sent)
            elif i.node_type in (NodeType.INT_FUNC, NodeType.VOID_FUNC):
                self.__a_define_function(i)
        return self.__result

    def get_stack_flow(self) -> tuple[list, list]:
        return self.__var_stack_flow, self.__fun_stack_flow

    def __error(self, msg: str, lineno: int):
        """

        :param msg:
        :param lineno:
        :return:
        """
        print(f"[ERROR] [ANALYZER] [{lineno}]: {msg}")
        self.error = True

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

    def __set_reg(self, target_name: str, is_global: bool = False) -> str:
        """
        get a reg name, follow the format definition of LLVM

        :param target_name: reg base name
        :return: return a reg
        """
        check = self.__check_name(target_name)
        prefix = OTHER if not is_global else GLOBAL
        prefix += "aa"
        if check < 0:
            return f"{prefix}{target_name}"
        else:
            return f"{prefix}{target_name}{check}"

    def __find_var_define(self, var_node: Node) -> Symbol:
        """


        :param var_node:
        :return:
        """
        var = self.__curr_var_table.get(var_node.value)
        if var is None:
            for i in self.__variable_stack:
                var = i.get(var_node.value, None)
                if var is not None:
                    break
        if var is None:
            self.__error(f"Undefined variable {var_node.value}", var_node.lineno)
        return var

    def __find_func_define(self, func_name: str, args: list[dict], lineno: int = 0, declare: bool = False) -> Optional[Symbol]:
        funcs: list[Symbol] = self.__function_table.get(func_name)
        if not funcs:
            if not declare:
                self.__error(f"Undefined function {func_name}", lineno)
        else:
            for i in funcs:
                paras = i.func_paras
                if len(paras) != len(args):
                    continue
                func_match = True
                for j in range(len(paras)):
                    if paras[j]['size'] != args[j]['size']:
                        func_match = False
                        break
                if func_match:
                    if declare and i.def_from != "declare":
                        self.__error(f"Function {func_name} has already been defined!", lineno)
                    return i
            if not declare:
                self.__error(f"Can't find proper function call of {func_name}", lineno)
        return None

    def __process_var_use(self, var_node: Node, just_value: bool = True) -> dict:
        """

        :param var_node:
        :return:
        """
        error_var_dict = {
            "type": None,
            "reg": None,
            "size": -1,
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
                if not just_value:
                    return {
                        "type": "ident",
                        "reg": sym.reg,
                        "size": 32,
                        "dimension": None,
                        "define_dime": sym.dimension
                    }
                pass_reg = {
                    "type": Reg_Type.TMP_REG,
                    "reg": self.__create_tmp_reg(),
                    "size": 32,
                    "dimension": None,
                    "define_dime": sym.dimension
                }
                curr = Sentence(Sentence_Type.LOAD, lineno=var_node.lineno)
                curr.info['avar'] = pass_reg
                curr.info['lvar'] = pass_reg
                curr.info['rvar'] = {
                    "type": "ident",
                    "reg": sym.reg,
                    "size": 32,
                    "dimension": None,
                    "define_dime": sym.dimension
                }
                if self.__last_label:
                    curr.label = self.__last_label
                    self.__last_label = None
                self.__result.append(curr)
                return pass_reg
        elif var_node.node_type is NodeType.ARRAY:
            sym = self.__find_var_define(var_node)
            if sym is None:
                return error_var_dict
            elif sym.symbol_type != "int array":
                self.__error(f"{sym.symbol_type} is not subscriptable", var_node.lineno)
                return error_var_dict
            else:
                var_dimension = [var_node.info[str(i)] for i in range(var_node.info['size'])]
                dimensions = []
                for i in var_dimension:
                    if i.node_type is NodeType.NUM:
                        dimensions.append({
                            "type": "num",
                            "value": int(i.value),
                            "size": 32
                        })
                    elif i.node_type is NodeType.IDENT:
                        dimensions.append(self.__process_var_use(i))
                    else:
                        dimensions.append(self.__a_expr(i))
                return {
                    "type": "ident",
                    "reg": sym.reg,
                    "size": 32,
                    "dimension": dimensions,
                    "define_dime": sym.dimension
                }
        elif var_node.node_type is NodeType.FUNC:
            args: list[Node] = var_node.info['args']
            arg_res = []
            for i in args:
                if i.node_type is NodeType.IDENT:
                    sym = self.__find_var_define(i)
                    if sym and sym.dimension:
                        arg_res.append({
                            "type": "ident",
                            "reg": sym.reg,
                            "size": 32,
                            "dimension": None,
                            "define_dime": sym.dimension
                        })
                        continue
                arg_res.append(self.__a_expr(i))
            func_sym = self.__find_func_define(var_node.value, arg_res, var_node.lineno)
            if func_sym is None:
                return error_var_dict
            curr = Sentence(Sentence_Type.CALL, value=func_sym.value, lineno=var_node.lineno)
            curr.info['func'] = func_sym.value
            curr.info['args'] = arg_res
            if "int" in func_sym.symbol_type:
                tmp_reg = {
                    "type": Reg_Type.TMP_REG,
                    "reg": self.__create_tmp_reg(),
                    "size": 32
                }
                curr.info['avar'] = tmp_reg
                curr.info['func_type'] = "int"
            else:
                tmp_reg = {
                    "type": Reg_Type.VOID_REG,
                    "reg": None,
                    "size": None
                }
                curr.info['func_type'] = "void"
            self.__set_label_and_keep_base_block(curr)
            self.__result.append(curr)
            return tmp_reg

    def __process_side_val(self, expr: Node) -> dict:
        if expr.node_type in (NodeType.NUM, NodeType.IDENT, NodeType.ARRAY):
            res = self.__process_var_use(expr)
            if res['type'] is Reg_Type.VOID_REG:
                self.__error("Can't use VOID value in expression", expr.lineno)
            return res
        else:
            return self.__a_expr(expr)

    def __convert_i32_i1(self, target_reg: dict, source_reg: dict, lineno: int = 0) -> Sentence:
        trans = Sentence(sentence_type=Sentence_Type.NEQ, lineno=lineno)
        trans.info['lvar'] = source_reg
        trans.info['rvar'] = {
            "type": "num",
            "value": "0",
            "size": 32
        }
        trans.info['avar'] = target_reg
        if self.__last_label:
            trans.label = self.__last_label
            self.__last_label = None
        return trans

    def __convert_i1_i32(self, target_reg: dict, source_reg: dict, lineno: int = 0) -> Sentence:
        trans = Sentence(sentence_type=Sentence_Type.ZEXT, lineno=lineno)
        trans.info['lvar'] = target_reg
        trans.info['rvar'] = source_reg
        trans.info['avar'] = target_reg
        if self.__last_label:
            trans.label = self.__last_label
            self.__last_label = None
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
        if reg['size'] != 1:
            tmp = {
                "type": Reg_Type.TMP_REG,
                "reg": self.__create_tmp_reg(),
                "size": 1,
            }
            self.__result.append(self.__convert_i32_i1(tmp, reg))
            reg = tmp
        curr = Sentence(Sentence_Type.IF_JMP, lineno=0)
        curr.info['var'] = reg
        curr.info['tl'] = true_label
        curr.info['fl'] = false_label
        self.__set_label_and_keep_base_block(curr)
        self.__result.append(curr)

    def __create_tmp_reg(self) -> str:
        reg = f"{OTHER}t{self.__reg_counter}"
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
            sym.value = sym.value + "i" * len(self.__function_table[sym.value])
        else:
            self.__function_table[sym.value] = []
        self.__function_table[sym.value].append(sym)
        return True

    def __push_var_table(self):
        """
        storage last block's variable table

        :return: None
        """

        curr_variable_stack = copy.deepcopy(self.__variable_stack)
        curr_function_stack = copy.deepcopy(self.__function_table)
        self.__var_stack_flow.append(curr_variable_stack)
        self.__fun_stack_flow.append(curr_function_stack)

        self.__curr_var_table = {}
        self.__variable_stack.append(self.__curr_var_table)

    def __pop_var_table(self):
        """
        pop useless variable table

        :return: None
        """
        curr_variable_stack = copy.deepcopy(self.__variable_stack)
        curr_function_stack = copy.deepcopy(self.__function_table)
        self.__var_stack_flow.append(curr_variable_stack)
        self.__fun_stack_flow.append(curr_function_stack)
        if self.__variable_stack:
            self.__variable_stack.pop()
            self.__curr_var_table = self.__variable_stack[-1]

    def __set_label_and_keep_base_block(self, curr: Sentence):
        if self.__last_label:
            curr.label = self.__last_label
            self.__last_label = None
            if self.__result[-1].sentence_type not in [Sentence_Type.JMP, Sentence_Type.IF_JMP]:
                bb = Sentence(Sentence_Type.JMP, lineno=0)
                bb.info['label'] = curr.label
                self.__result.append(bb)

    def __a_define_var(self, var_node: Node) -> tuple[Sentence, Symbol]:
        """


        :param var_node:
        :return:
        """
        reg = self.__set_reg(var_node.value)
        symbol = Symbol(value=var_node.value, symbol_type="int var", reg=reg, lineno=var_node.lineno)
        var = Sentence(sentence_type=Sentence_Type.DEFINE_LOCAL_VAR, value=var_node.value, lineno=var_node.lineno,
                       reg=reg)
        var.info = {
            "type": Reg_Type.INT_REG,
            "reg": reg,
            "size": 32
        }
        return var, symbol

    def __a_define_array(self, array_node: Node) -> tuple[Sentence, Symbol]:
        """


        :param array_node:
        :return:
        """
        reg = self.__set_reg(array_node.value)
        symbol = Symbol(value=array_node.value, symbol_type="int array", reg=reg, lineno=array_node.lineno)
        array = Sentence(sentence_type=Sentence_Type.DEFINE_LOCAL_ARRAY,
                         value=array_node.value,
                         lineno=array_node.lineno,
                         reg=reg)
        array.info = {
            "type": Reg_Type.INT_REG,
            "reg": reg,
            "size": 32,
            "dimension": array_node.info['size'],
            "define_dime": []
        }
        for j in range(array_node.info['size']):
            if array_node.info[str(j)] is None:
                array.info['define_dime'].append(None)
            else:
                array.info['define_dime'].append(int(array_node.info[str(j)].value))
        symbol.size = array.info['dimension']
        symbol.dimension = array.info['define_dime']
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
        func_paras_def = []
        # process parameters of function
        for para in function.info['paras']:
            if para.node_type is NodeType.INT_VAR:
                sent, symb = self.__a_define_var(para)
                func.info['paras'].append(sent)
                ins_reg = self.__create_tmp_reg()
                ins_info = {
                    'type': sent.info.get('type'),
                    'reg': ins_reg,
                    'size': sent.info.get('size'),
                }
                curr = Sentence(Sentence_Type.DEFINE_LOCAL_VAR, lineno=0)
                curr.info = ins_info
                func_paras_def.append(curr)
                curr = Sentence(Sentence_Type.ASSIGN, lineno=0)
                curr.info['rvar'] = sent.info
                curr.info['avar'] = ins_info
                func_paras_def.append(curr)
                symb.reg = ins_reg
                self.__insert_var_table(symb)
                func_paras.append({
                    "type": "int var",
                    "value": para.value,
                    "size": 32
                })
            elif para.node_type is NodeType.INT_ARRAY:
                sent, symb = self.__a_define_array(para)
                func.info['paras'].append(sent)
                ins_reg = self.__create_tmp_reg()
                ins_info = {
                    'type': sent.info.get('type'),
                    'reg': ins_reg,
                    'size': sent.info.get('size'),
                    'dimension': sent.info.get('dimension'),
                    'define_dime': sent.info.get('define_dime'),
                }
                curr = Sentence(Sentence_Type.DEFINE_LOCAL_ARRAY, lineno=0)
                curr.info = ins_info
                func_paras_def.append(curr)
                curr = Sentence(Sentence_Type.ASSIGN, lineno=0)
                curr.info['rvar'] = sent.info
                curr.info['avar'] = ins_info
                func_paras_def.append(curr)
                symb.reg = ins_reg
                self.__insert_var_table(symb)
                func_paras.append({
                    "type": "int array",
                    "value": para.value,
                    "size": 32,
                    "dimension": symb.dimension
                })

        # generate symbol info
        func_entry = self.__set_label()
        func_leave = self.__set_label()
        self.__func_ret = func_leave
        symb = Symbol(function.value,
                      symbol_type=f"{func_type} func",
                      lineno=function.lineno,
                      func_paras=func_paras,
                      func_entry=func_entry,
                      func_leave=func_leave)
        if function.info['funcbody'] is None:
            symb.def_from = "declare"
            self.__pop_var_table()
            if self.__insert_func_table(symb):
                return func, symb
        else:
            symb_dec = self.__find_func_define(symb.value, symb.func_paras, declare=True)
            if symb_dec:
                symb = symb_dec
                func_entry = symb.func_entry
                func_leave = symb.func_leave

                func.label = func_entry
                self.__func_ret = func_leave
            else:
                self.__insert_func_table(symb)

            func.value = symb.value
            self.__result.append(func)
            self.__result.extend(func_paras_def)
            if func_type == "int":
                ret_reg = self.__set_reg("retg")
                self.__return_reg = {
                    "type": Reg_Type.INT_REG,
                    "reg": ret_reg,
                    "size": 32
                }
                ret_sym = Symbol(symbol_type="int var", value="retg", reg=ret_reg)
                ret_sen = Sentence(Sentence_Type.DEFINE_LOCAL_VAR, value="retg", lineno=0)
                ret_sen.info = self.__return_reg
                self.__insert_var_table(ret_sym)
                self.__result.append(ret_sen)

            # self.__last_label = func_entry
            self.__a_statement(function.info['funcbody'])

            if self.__last_label:
                curr = Sentence(Sentence_Type.JMP, lineno=function.lineno)
                curr.label = self.__last_label
                self.__last_label = None
                curr.info['label'] = self.__func_ret
                self.__result.append(curr)

            self.__last_label = self.__func_ret
            # add ret instruction
            if self.__return_reg:
                curr = Sentence(Sentence_Type.LOAD, lineno=function.lineno)
                ret_t = {
                    "type": Reg_Type.TMP_REG,
                    "reg": self.__create_tmp_reg(),
                    "size": 32
                }
                curr.info['lvar'] = ret_t
                curr.info['rvar'] = self.__return_reg
                curr.info['avar'] = ret_t
                self.__set_label_and_keep_base_block(curr)
                self.__result.append(curr)
            else:
                ret_t = self.__return_reg
            curr = Sentence(Sentence_Type.RETURN, lineno=function.lineno)
            curr.info['return_reg'] = ret_t
            self.__set_label_and_keep_base_block(curr)
            self.__result.append(curr)

            func_end = Sentence(Sentence_Type.FUNC_END, lineno=function.lineno)
            self.__result.append(func_end)

        self.__pop_var_table()
        self.__func_ret = None
        self.__return_reg = None

        return func, symb

    def __a_statement(self, statement: Node) -> None:
        if statement.node_type is NodeType.BLOCK:
            for sub in statement.info['subprogram']:
                self.__a_statement(sub)
        elif statement.node_type is NodeType.INT_VAR:
            sent, symb = self.__a_define_var(statement)
            self.__set_label_and_keep_base_block(sent)
            self.__insert_var_table(symb)
            self.__result.append(sent)
        elif statement.node_type is NodeType.INT_ARRAY:
            sent, symb = self.__a_define_array(statement)
            self.__set_label_and_keep_base_block(sent)
            self.__insert_var_table(symb)
            self.__result.append(sent)
        elif statement.node_type is NodeType.WHILE:
            self.__a_while(statement)
        elif statement.node_type is NodeType.IF:
            self.__a_if(statement)
        elif statement.node_type is NodeType.SWITCH:
            self.__a_switch(statement)
        elif statement.node_type in (NodeType.CONTINUE, NodeType.BREAK):
            self.__a_continue_or_break(statement)
        elif statement.node_type is NodeType.RETURN:
            self.__a_return(statement)
        elif statement.node_type is NodeType.BLOCK:
            self.__push_var_table()
            self.__a_statement(statement)
            self.__pop_var_table()
        else:
            self.__a_expr(statement)

    def __a_while(self, while_node: Node) -> None:
        # follow this sequence to storage jump label info
        old_label = (self.__condition_entry, self.__block_leave)
        self.__condition_entry = self.__set_label() if self.__last_label is None else self.__last_label
        self.__block_leave = self.__set_label()
        true_label = self.__set_label()
        false_label = self.__block_leave

        # add branch for base block
        if self.__result[-1].sentence_type not in [Sentence_Type.JMP, Sentence_Type.IF_JMP]:
            curr = Sentence(Sentence_Type.JMP, lineno=0)
            curr.info['label'] = self.__condition_entry
            self.__result.append(curr)

        self.__last_label = self.__condition_entry
        condition_reg = self.__a_expr(while_node.info['condition'])
        self.__create_jump_sentences(condition_reg, true_label, false_label)
        # given statement is a sub-block(node_type may not be BLOCK), we need to push stack
        self.__push_var_table()
        self.__last_label = true_label
        self.__a_statement(while_node.info['statement'])
        # after we left statement process, we need to restore all stack info
        self.__pop_var_table()
        # add loop jump
        curr = Sentence(Sentence_Type.JMP, lineno=while_node.lineno)
        if self.__last_label is not None:
            curr.label = self.__last_label
            self.__last_label = None
        curr.info['label'] = self.__condition_entry
        self.__result.append(curr)

        # before leave loop block, should pass loop leave label to next sentence correctly
        self.__last_label = self.__block_leave
        # and then restore all jump control label
        self.__condition_entry, self.__block_leave = old_label

    def __a_if(self, if_node: Node) -> None:
        condition_entry = self.__set_label() if self.__last_label is None else self.__last_label
        block_leave = self.__set_label()
        true_leave = self.__set_label()
        false_leave = self.__set_label()

        # add branch for base block
        if self.__result[-1].sentence_type not in [Sentence_Type.JMP, Sentence_Type.IF_JMP]:
            curr = Sentence(Sentence_Type.JMP, lineno=0)
            curr.info['label'] = condition_entry
            self.__result.append(curr)

        self.__last_label = condition_entry
        condition_reg = self.__a_expr(if_node.info['condition'])
        self.__create_jump_sentences(condition_reg, true_leave, false_leave)
        # given statement is a sub-block(node_type may not be BLOCK), we need to push stack
        self.__push_var_table()
        self.__last_label = true_leave
        self.__a_statement(if_node.info['statement'])
        # after we left statement process, we need to restore all stack info
        self.__pop_var_table()

        curr = Sentence(Sentence_Type.JMP, lineno=if_node.lineno)
        if self.__last_label is not None:
            curr.label = self.__last_label
            self.__last_label = None
        curr.info['label'] = block_leave
        self.__result.append(curr)

        self.__last_label = false_leave
        if if_node.info['elsestat'] is not None:
            self.__push_var_table()
            self.__a_statement(if_node.info['elsestat'].info['statement'])
            self.__pop_var_table()

        # if exit labels have conflict, set a branch instruction jump to outer exit label
        # FIXME:it will make system more complex
        curr = Sentence(Sentence_Type.JMP, lineno=if_node.lineno)
        if self.__last_label is not None:
            curr.label = self.__last_label
            self.__last_label = None
        curr.info['label'] = block_leave
        self.__result.append(curr)

        # before leave if block, should pass loop leave label to next sentence correctly
        self.__last_label = block_leave

    def __a_switch(self, switch_node: Node) -> None:
        pass

    def __a_continue_or_break(self, node: Node) -> None:
        target_label = ""
        if node.node_type is NodeType.CONTINUE:
            if self.__condition_entry is None:
                self.__error("Can't find loop block to set 'continue'", node.lineno)
                return
            target_label = self.__condition_entry
        elif node.node_type is NodeType.BREAK:
            if self.__condition_entry is None:
                self.__error("Can't find loop block to set 'break'", node.lineno)
                return
            target_label = self.__block_leave

        curr = Sentence(Sentence_Type.JMP, lineno=node.lineno)
        if self.__last_label:
            curr.label = self.__last_label
            self.__last_label = None
        curr.info['label'] = target_label
        self.__result.append(curr)

    def __a_return(self, node: Node):
        if self.__func_ret is None:
            self.__error("Can't find function block to set 'return'", node.lineno)
        if node.info.get('return_expr'):
            if self.__return_reg is None:
                self.__error("Return type 'void' can't have return value", node.lineno)
                return
            expr_res = self.__a_expr(node.info['return_expr'])
            curr = Sentence(Sentence_Type.ASSIGN, lineno=node.lineno)
            curr.info['lvar'] = self.__return_reg
            curr.info['avar'] = self.__return_reg
            curr.info['rvar'] = expr_res
            if self.__last_label:
                curr.label = self.__last_label
                self.__last_label = None
            self.__result.append(curr)
        curr = Sentence(Sentence_Type.JMP, lineno=node.lineno)
        if self.__last_label:
            curr.label = self.__last_label
            self.__last_label = None
        curr.info['label'] = self.__func_ret
        self.__result.append(curr)

    def __a_expr(self, expr: Node) -> dict:
        """
        use to translate expression to a couple of base calculation sentences

        :param expr:
        :return:
        """
        if expr.node_type is NodeType.ASSIGN:
            curr = Sentence(Sentence_Type.ASSIGN, lineno=expr.lineno)
            # left value
            if expr.info['lvar'].node_type is NodeType.NUM:
                self.__error("Number can't be evaluated", expr.lineno)
                curr.info['lvar'] = {"type": None, "reg": None, "size": None}
            elif expr.info['lvar'].node_type in (NodeType.IDENT, NodeType.ARRAY):
                curr.info['lvar'] = self.__process_var_use(expr.info['lvar'], False)
            else:
                self.__error("Excepted left identifier of '='", expr.lineno)
                curr.info['lvar'] = {"type": None, "reg": None, "size": None}

            # right value
            curr.info['rvar'] = self.__process_side_val(expr.info['rvar'])
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
            if target.node_type in (NodeType.NUM, NodeType.IDENT, NodeType.ARRAY):
                rvar = self.__process_var_use(target, False)
            else:  # target.node_type in (NodeType.UNARY_LEFT, NodeType.UNARY_RIGHT):
                rvar = self.__a_expr(target)
            value_pass['size'] = rvar['size']
            if lop.node_type in (NodeType.SELF_PLUS, NodeType.SELF_MINUS):
                # t = a
                curr = Sentence(Sentence_Type.LOAD, lineno=expr.lineno)
                curr.info['avar'] = value_pass
                curr.info['lvar'] = value_pass
                curr.info['rvar'] = rvar
                if self.__last_label:
                    curr.label = self.__last_label
                    self.__last_label = None
                self.__result.append(curr)

                # t = a +/- 1
                tmp_reg = self.__create_tmp_reg()
                tmp_info = {
                    "type": Reg_Type.TMP_REG,
                    "reg": tmp_reg,
                    "size": 32
                }
                if lop.node_type is NodeType.SELF_PLUS:
                    curr = Sentence(Sentence_Type.ADD, lineno=expr.lineno)
                else:
                    curr = Sentence(Sentence_Type.MINUS, lineno=expr.lineno)
                curr.info['avar'] = tmp_info
                curr.info['lvar'] = value_pass
                curr.info['rvar'] = {
                    "type": "num",
                    "value": "1",
                    "size": 32
                }
                self.__result.append(curr)

                # a = t
                curr = Sentence(Sentence_Type.ASSIGN, lineno=expr.lineno)
                curr.info['avar'] = rvar
                curr.info['lvar'] = rvar
                curr.info['rvar'] = tmp_info
                self.__result.append(curr)
                value_pass = tmp_info
            else:
                if rvar.get('reg') and rvar.get("type") is not Reg_Type.TMP_REG:
                    curr = Sentence(Sentence_Type.LOAD, lineno=expr.lineno)
                    curr.info['avar'] = value_pass
                    curr.info['lvar'] = value_pass
                    curr.info['rvar'] = rvar
                    self.__set_label_and_keep_base_block(curr)
                    self.__result.append(curr)
                else:
                    value_pass = rvar
                if lop.node_type is NodeType.NEGATIVE:
                    # t = 0 - a
                    curr = Sentence(Sentence_Type.MINUS, lineno=expr.lineno)
                    curr.info['avar'] = {
                        "type": Reg_Type.TMP_REG,
                        "reg": self.__create_tmp_reg(),
                        "size": rvar['size']
                    }
                    curr.info['lvar'] = {
                        "type": "num",
                        "value": "0",
                        "size": rvar['size']
                    }
                    curr.info['rvar'] = value_pass
                    self.__set_label_and_keep_base_block(curr)
                    self.__result.append(curr)
                    value_pass = curr.info['avar']
                else:
                    # t1 = a != 0
                    neq = Sentence(Sentence_Type.NEQ, lineno=expr.lineno)
                    neq.info['avar'] = {
                        "type": Reg_Type.TMP_REG,
                        "reg": self.__create_tmp_reg(),
                        "size": 1
                    }
                    neq.info['lvar'] = value_pass
                    neq.info['rvar'] = {
                        "type": "num",
                        "value": "0",
                        "size": 32
                    }
                    self.__set_label_and_keep_base_block(neq)
                    self.__result.append(neq)

                    # t2 = t1 xor true
                    curr = Sentence(Sentence_Type.XOR, lineno=expr.lineno)
                    curr.info['avar'] = {
                        "type": Reg_Type.TMP_REG,
                        "reg": self.__create_tmp_reg(),
                        "size": 1
                    }
                    curr.info['lvar'] = neq.info['avar']
                    curr.info['rvar'] = {
                        "type": "num",
                        "value": "1",
                        "size": 1
                    }
                    self.__set_label_and_keep_base_block(curr)
                    self.__result.append(curr)
                    value_pass = curr.info['avar']
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
                rvar = self.__process_var_use(target, False)
            elif target.node_type in (NodeType.UNARY_LEFT, NodeType.UNARY_RIGHT):
                rvar = self.__a_expr(target)
            else:
                self.__error("lvalue required as decrement operand", expr.lineno)
                return {
                    "type": None,
                    "reg": None
                }

            # t1 = a
            curr = Sentence(Sentence_Type.LOAD, lineno=expr.lineno)
            self.__set_label_and_keep_base_block(curr)
            curr.info['lvar'] = value_pass
            curr.info['avar'] = value_pass
            curr.info['rvar'] = rvar
            self.__result.append(curr)

            # t2 = a +/- 1
            tmp_reg = self.__create_tmp_reg()
            tmp_info = {
                "type": Reg_Type.TMP_REG,
                "reg": tmp_reg,
                "size": 32
            }
            if rop.node_type is NodeType.SELF_PLUS:
                curr = Sentence(Sentence_Type.ADD, lineno=expr.lineno)
            else:
                curr = Sentence(Sentence_Type.MINUS, lineno=expr.lineno)
            curr.info['avar'] = tmp_info
            curr.info['lvar'] = value_pass
            curr.info['rvar'] = {
                "type": "num",
                "value": "1",
                "size": 32
            }
            self.__result.append(curr)

            # a = t2
            curr = Sentence(Sentence_Type.ASSIGN, lineno=expr.lineno)
            curr.info['avar'] = rvar
            curr.info['lvar'] = rvar
            curr.info['rvar'] = tmp_info
            self.__result.append(curr)

            return value_pass
        elif expr.node_type is NodeType.LOGIC_AND:
            all_leave_label = self.__set_label()
            l_true_label = self.__set_label()
            and_res = {
                "type": Reg_Type.TMP_REG,
                "reg": self.__create_tmp_reg(),
                "size": 1
            }
            curr = Sentence(Sentence_Type.DEFINE_LOCAL_VAR, lineno=0)
            curr.info = and_res
            self.__set_label_and_keep_base_block(curr)
            self.__result.append(curr)
            l_j_info = {
                "type": Reg_Type.TMP_REG,
                "reg": self.__create_tmp_reg(),
                "size": 1
            }

            l_reg = self.__process_side_val(expr.info['lvar'])
            if l_reg['size'] != 1:
                l_trans = self.__convert_i32_i1(and_res, l_reg, expr.lineno)
                self.__result.append(l_trans)
            else:
                curr = Sentence(Sentence_Type.ASSIGN, lineno=0)
                curr.info['lvar'] = and_res
                curr.info['rvar'] = l_reg
                curr.info['avar'] = and_res
                self.__set_label_and_keep_base_block(curr)
                self.__result.append(curr)
                curr = Sentence(Sentence_Type.LOAD, lineno=0)
                curr.info['lvar'] = l_j_info
                curr.info['rvar'] = and_res
                curr.info['avar'] = l_j_info
                self.__set_label_and_keep_base_block(curr)
                self.__result.append(curr)

            self.__create_jump_sentences(l_j_info, l_true_label, all_leave_label)

            self.__last_label = l_true_label
            r_reg = self.__process_side_val(expr.info['rvar'])
            if r_reg['size'] != 1:
                r_trans = self.__convert_i32_i1(and_res, r_reg, expr.lineno)
                self.__result.append(r_trans)
            else:
                curr = Sentence(Sentence_Type.ASSIGN, lineno=0)
                curr.info['lvar'] = and_res
                curr.info['rvar'] = r_reg
                curr.info['avar'] = and_res
                self.__set_label_and_keep_base_block(curr)
                self.__result.append(curr)

            self.__last_label = all_leave_label
            tmp_info = {
                "type": Reg_Type.TMP_REG,
                "reg": self.__create_tmp_reg(),
                "size": 1
            }
            curr = Sentence(Sentence_Type.LOAD, lineno=0)
            curr.info['lvar'] = tmp_info
            curr.info['rvar'] = and_res
            curr.info['avar'] = tmp_info
            self.__set_label_and_keep_base_block(curr)
            self.__result.append(curr)
            and_res = tmp_info

            return and_res
        elif expr.node_type is NodeType.LOGIC_OR:
            all_leave_label = self.__set_label()
            l_false_label = self.__set_label()
            or_res = {
                "type": Reg_Type.TMP_REG,
                "reg": self.__create_tmp_reg(),
                "size": 1
            }
            curr = Sentence(Sentence_Type.DEFINE_LOCAL_VAR, lineno=0)
            curr.info = or_res
            self.__set_label_and_keep_base_block(curr)
            self.__result.append(curr)
            l_j_info = {
                "type": Reg_Type.TMP_REG,
                "reg": self.__create_tmp_reg(),
                "size": 1
            }

            l_reg = self.__process_side_val(expr.info['lvar'])
            if l_reg['size'] != 1:
                l_trans = self.__convert_i32_i1(or_res, l_reg, expr.lineno)
                self.__result.append(l_trans)
            else:
                curr = Sentence(Sentence_Type.ASSIGN, lineno=0)
                curr.info['lvar'] = or_res
                curr.info['rvar'] = l_reg
                curr.info['avar'] = or_res
                self.__set_label_and_keep_base_block(curr)
                self.__result.append(curr)
                curr = Sentence(Sentence_Type.LOAD, lineno=0)
                curr.info['lvar'] = l_j_info
                curr.info['rvar'] = or_res
                curr.info['avar'] = l_j_info
                self.__set_label_and_keep_base_block(curr)
                self.__result.append(curr)

            self.__create_jump_sentences(l_j_info, all_leave_label, l_false_label)

            self.__last_label = l_false_label
            r_reg = self.__process_side_val(expr.info['rvar'])
            if r_reg['size'] != 1:
                l_trans = self.__convert_i32_i1(or_res, r_reg, expr.lineno)
                self.__result.append(l_trans)
            else:
                curr = Sentence(Sentence_Type.ASSIGN, lineno=0)
                curr.info['lvar'] = or_res
                curr.info['rvar'] = r_reg
                curr.info['avar'] = or_res
                self.__set_label_and_keep_base_block(curr)
                self.__result.append(curr)

            self.__last_label = all_leave_label
            tmp_info = {
                "type": Reg_Type.TMP_REG,
                "reg": self.__create_tmp_reg(),
                "size": 1
            }
            curr = Sentence(Sentence_Type.LOAD, lineno=0)
            curr.info['lvar'] = tmp_info
            curr.info['rvar'] = or_res
            curr.info['avar'] = tmp_info
            self.__set_label_and_keep_base_block(curr)
            self.__result.append(curr)
            or_res = tmp_info

            return or_res
        else:
            aval_reg_size = 32
            if expr.node_type is NodeType.PLUS:
                curr = Sentence(Sentence_Type.ADD, lineno=expr.lineno)
            elif expr.node_type is NodeType.MINUS:
                curr = Sentence(Sentence_Type.MINUS, lineno=expr.lineno)
            elif expr.node_type is NodeType.TIMES:
                curr = Sentence(Sentence_Type.TIMES, lineno=expr.lineno)
            elif expr.node_type is NodeType.DIVIDE:
                curr = Sentence(Sentence_Type.DIVIDE, lineno=expr.lineno)
            elif expr.node_type is NodeType.MOD:
                curr = Sentence(Sentence_Type.MOD, lineno=expr.lineno)
            elif expr.node_type is NodeType.EQ:
                curr = Sentence(Sentence_Type.EQ, lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.NEQ:
                curr = Sentence(Sentence_Type.NEQ, lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.GT:
                curr = Sentence(Sentence_Type.GT, lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.GEQ:
                curr = Sentence(Sentence_Type.GEQ, lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.LT:
                curr = Sentence(Sentence_Type.LT, lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.LEQ:
                curr = Sentence(Sentence_Type.LEQ, lineno=expr.lineno)
                aval_reg_size = 1
            elif expr.node_type is NodeType.NOT:
                curr = Sentence(Sentence_Type.NOT, lineno=expr.lineno)
            else:  # NUM, IDENT, ARRAY, FUNC CALL
                return self.__process_var_use(expr)
            l_reg = self.__process_side_val(expr.info['lvar'])
            r_reg = self.__process_side_val(expr.info['rvar'])

            curr.info['lvar'] = self.__convert_to_target_length(l_reg, 32, expr.lineno)
            curr.info['rvar'] = self.__convert_to_target_length(r_reg, 32, expr.lineno)

            aval_reg = self.__create_tmp_reg()
            aval_reg_info = {
                "type": Reg_Type.TMP_REG,
                "reg": aval_reg,
                "size": aval_reg_size
            }
            curr.info['avar'] = aval_reg_info
            self.__set_label_and_keep_base_block(curr)
            self.__result.append(curr)
            return aval_reg_info

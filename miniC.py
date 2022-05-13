#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：miniC.py
@Author ：OrangeJ
@Date ：2022/4/23 10:22
"""
import argparse
import os
import sys
import json
# from types import Union

from lex import Lex, Token
from yacc import Yacc, CustomEncoder, Node
from analyzer import Analyzer
from enum import Enum

EXEC_ = "minic.exe" if "win" in sys.platform else "minic"
DESC = "A miniC Compiler. if not set argument '-o', it will print the result of compiler to screen"
VERSION = 1.0


class OUTPUT_TARGET(Enum):
    STDOUT = 0
    FILE = 1
    PIPE = 2


class OUTPUT_TYPE(Enum):
    STD = 0
    JSON = 1


class INPUT_TYPE(Enum):
    TOKEN = 0
    NODE = 1
    TABLE = 2


class COMPILE_ACTION(Enum):
    NONE = 0
    LEX = 1
    YACC = 2
    IR = 3
    ANALYZE = 4
    ALL = 5
    COMPLEX = 6


def get_info_from_json(json_data: dict):
    if json_data.get('tokens', None) is not None:
        pass
        return INPUT_TYPE.TOKEN, iter([])
    elif json_data.get('root', None) is not None:
        pass
        return INPUT_TYPE.NODE, Node()
    else:
        raise Exception("Unsupported JSON content")


if __name__ == "__main__":
    # 预设参数解析
    argsParser = argparse.ArgumentParser(EXEC_, description=DESC)
    argsParser.add_argument("input", nargs="?", type=str, default=None, metavar="input")
    argsParser.add_argument("-l", "--lex", action="store_true", default=False, dest="lex", help="词法处理")
    argsParser.add_argument("-y", "--yacc", action="store_true", default=False, dest="yacc", help="语法处理")
    argsParser.add_argument("-a", "--analyze", action="store_true", default=False, dest="analyze", help="语义处理")
    argsParser.add_argument("-i", "--ir", action="store_true", default=False, dest="ir", help="IR生成")
    argsParser.add_argument("-j", "--json", action="store_true", default=False, dest="json", help="输出为json格式")
    argsParser.add_argument("-o", nargs="?", default=None, type=str, dest="output", help="输出文件")
    argsParser.add_argument("-v", "--version", action="version", version=f"v{VERSION}", help="版本信息")
    opts = argsParser.parse_args()

    input_file = opts.input
    output_file = opts.output

    # 输入文件名判断
    if input_file is None:
        argsParser.error("no input file")
        sys.exit(1)
    if not os.path.exists(input_file):
        argsParser.error(f"{input_file} not exist!")
        sys.exit(2)

    # 执行过程控制变量
    task = COMPILE_ACTION.NONE
    output_dest = OUTPUT_TARGET.STDOUT if output_file is None else OUTPUT_TARGET.FILE
    output_type = OUTPUT_TYPE.STD if not opts.json else OUTPUT_TYPE.JSON

    # 任务选择
    if opts.lex:
        task = COMPILE_ACTION.LEX if task == COMPILE_ACTION.NONE else COMPILE_ACTION.COMPLEX
    if opts.yacc:
        task = COMPILE_ACTION.YACC if task == COMPILE_ACTION.NONE else COMPILE_ACTION.COMPLEX
    if opts.analyze:
        task = COMPILE_ACTION.ANALYZE if task == COMPILE_ACTION.NONE else COMPILE_ACTION.COMPLEX
    if opts.ir:
        task = COMPILE_ACTION.IR if task == COMPILE_ACTION.NONE else COMPILE_ACTION.COMPLEX
    task = COMPILE_ACTION.ALL if task == COMPILE_ACTION.NONE else task

    # 无法识别的参数
    if task == COMPILE_ACTION.COMPLEX:
        argsParser.error("too many action args")
        sys.exit(3)

    # 文件读入
    input_stream = ""
    try:
        with open(input_file, "r", encoding="UTF-8") as f:
            input_stream = f.read()
    except Exception as e:
        argsParser.error(str(e))
        sys.exit(4)

    # 词法处理
    curr_task = COMPILE_ACTION.LEX
    ll = Lex(input_stream)
    tokens = ll.get_token()

    # 如果目标任务为词法分析
    if curr_task.value >= task.value:
        # 输出格式为JSON
        if output_type == OUTPUT_TYPE.JSON:
            jsonify_tokens = json.dumps(
                {'tokens': [{"type": i.type, "value": i.value, "line": i.line} for i in tokens]}, indent=4)
            if output_dest == OUTPUT_TARGET.STDOUT:
                print(jsonify_tokens)
            else:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(jsonify_tokens)
        else:
            if output_dest == OUTPUT_TARGET.STDOUT:
                for i in tokens:
                    print(i)
            else:
                with open(output_file, "w", encoding="utf-8") as f:
                    for i in tokens:
                        f.write(str(i) + '\n')
        sys.exit(0)

    # 语法分析
    curr_task = COMPILE_ACTION.YACC
    yy = Yacc(tokens)
    yy.parser()
    json_ast = {"root": yy.ast}  # 该AST原生格式为JSON格式

    # 如果目标任务为语法分析
    if curr_task.value >= task.value:
        # 输出格式为JSON
        if output_type == OUTPUT_TYPE.JSON:
            jsonify_ast = json.dumps(json_ast, cls=CustomEncoder, indent=4)
            if output_dest == OUTPUT_TARGET.STDOUT:
                print(jsonify_ast)
            else:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(jsonify_ast)
        else:
            pass
        sys.exit(0)

    # 语义分析
    curr_task = COMPILE_ACTION.ANALYZE
    aa = Analyzer(yy.ast)
    aa.analysis()

    # IR生成
    curr_task = COMPILE_ACTION.IR

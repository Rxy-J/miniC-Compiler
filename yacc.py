#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：yacc.py
@Author ：OrangeJ
@Date ：2022/4/27 15:13
"""

from collections import Generator, Iterator
from enum import Enum
from typing import Union, Optional, Any
from json import JSONEncoder
from graphviz import Digraph

from lex import Token

DEBUG = False


class NodeType(Enum):
    ROOT = 0
    NUM = 1
    POINTER = 2
    INT = 3
    VOID = 4
    VAR = 5
    INT_VAR = 6
    POINTER_INT_VAR = 7
    FUNC = 8
    INT_FUNC = 9
    POINTER_INT_FUNC = 10
    VOID_FUNC = 11
    ARRAY = 12
    INT_ARRAY = 13
    POINTER_INT_ARRAY = 14
    IF = 15
    ELSE_IF = 16
    ELSE = 17
    WHILE = 18
    FOR = 19
    SWITCH = 20
    CASE = 21
    CONDITION = 22
    CONTINUE = 23
    BREAK = 24
    RETURN = 25
    BLOCK = 26
    IDENT = 27
    PLUS = 28
    MINUS = 29
    TIMES = 30
    DIVIDE = 40
    SELF_PLUS = 41
    SELF_MINUS = 42
    LOGIC_AND = 43
    LOGIC_OR = 44
    AND = 45
    OR = 46
    NOT = 47
    NEGATIVE = 48
    POSITIVE = 49
    LT = 50
    LEQ = 51
    GT = 52
    GEQ = 53
    EQ = 54
    NEQ = 55
    ASSIGN = 56


class CustomEncoder(JSONEncoder):
    """
    自定义类Node序列化编码器
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, Node):
            return o.__json__()


"""
Node类说明

Node类根据自身node_type的不同其info内信息也不同，具体如下
node_type: INT_VAR // 整型变量定义
    info:{}
    
node_type: POINTER_INT_VAR // 整型指针变量定义
    info:{}
    
node_type: INT_ARRAY // 整型数组定义
    info:{
        "size": x, //数组维度
        "1": Node(),
        "2": Node(),
        ...
        "i": Node(), // 第i维度长度信息，理论上Node类型为NUM
        "x": Node()
    }
    
node_type: INT_FUNC // 返回值为int的函数定义
    info: {
        "paras": [Node(), ...], // 参数定义
        "funcbody": Node() // 函数体信息，理论上为BLOCK类型Node
    }
node_type: VOID_FUNC // 无返回值函数定义
    info: {
        "paras": [Node(), ...], // 参数定义
        "funcbody": Node() // 函数体信息，理论上为BLOCK类型Node
    }
    
node_type: BLOCK // 代码块
    info: {
        subprogram: [Node(), ...] // 子可执行代码段信息
    }

node_type: FUNC // 函数调用
    info: {
        args: [Node(), ...] // 传入参数信息
    }

node_type: ARRAY // 数组调用
    info: {
        pos: Node() // 索引位置
    }
    
node_type: RETURN
    info: {
        return_expr: Node()
    }
    
node_type: BREAK
    info: {}
    
node_type: CONTINUE
    info: {}

node_type: WHILE
    info: {
        condition: Node() // 循环进行条件
        statement: Node() // 循环体
    }

node_type: IF
    info: {
        condition: Node() // if判断条件
        statement: Node() // if代码块
        elsestat: Node() // else代码块
    }

node_type: ELSE
    info: {
        statement: Node() // else代码块
    }
"""


class Node:
    """
    结点
    """
    def __init__(self, n_type: NodeType, value: str = "", info=None, graph_node: str = ""):
        if info is None:
            info = {}
        self.node_type = n_type
        self.value = value
        self.info = info
        self.graph_node = graph_node

    def __repr__(self):
        return f"node_type->{self.node_type}, value->{self.value}, info->{self.info}, graph_node->{self.graph_node}"

    def __json__(self):
        return {
            "node_type": self.node_type.name,
            "value": self.value,
            "info": self.info,
            "graph_node": self.graph_node
        }


S = 0  # for Segment
B = 0  # for Block
L = 0  # for Local definition
T = 0  # for Statement
P = 0  # for Operator
F = 0  # for Factor


class Yacc:
    """
    语法分析器
    """
    def __init__(self, tokens: Union[Generator[Token], Iterator[Token]]):
        self.__tokens = tokens
        self.__last_token = None
        self.__curr_token = None
        self.ast = Node(NodeType.ROOT, graph_node="ROOT")
        self.graph = Digraph("G")

    def __next(self):
        self.__last_token, self.__curr_token = self.__curr_token, next(self.__tokens, None)
        if DEBUG:
            print(self.__curr_token)

    def __accept(self, t_type: str) -> bool:
        if self.__curr_token.type == t_type:
            self.__next()
            return True
        else:
            return False

    def __except(self, t_type: str) -> None:
        if self.__curr_token is None or not self.__accept(t_type):
            self.__error(
                f"Excepted {t_type}, Found {self.__curr_token.type if self.__curr_token is not None else 'None'}")

    def __error(self, msg: str):
        print(f"[ERROR] [{self.__curr_token.line if self.__curr_token is not None else self.__last_token.line + 1}]: {msg}")
        exit(77)

    def _remove(self, graph_node: str):
        for i in self.graph.body:
            if graph_node in i:
                self.graph.body.remove(i)
                break

    def parser(self) -> None:
        """
        语法解析

        :return:
        """
        self.__next()
        self.ast.info['program'] = self.__y_program()
        self.graph.node("ROOT", "root", shape="rectangle")
        self.graph.node("PROGRAM", "program", shape="rectangle")
        self.graph.edge("ROOT", "PROGRAM")
        for i in self.ast.info['program']:
            self.graph.edge("PROGRAM", i.graph_node)

    def __y_program(self) -> list[Node]:
        global S
        """
        解析代码段

        :return:
        """
        y_segments = []
        while True:
            if self.__curr_token is None:
                break
            tmp = self.__y_segment()
            if type(tmp) == Node:
                y_segments.append(tmp)
            else:
                y_segments.extend(tmp)
        return y_segments

    def __y_segment(self) -> Union[list[Node], Node]:
        global S
        """
        解析

        :return:
        """
        y_defvars = []
        y_type = self.__y_type()
        y_def = self.__y_def()
        if type(y_def) == Node:
            # function
            if y_type.node_type == NodeType.INT:
                y_def.node_type = NodeType.INT_FUNC
                i_type = 'int func'
            else:
                y_def.node_type = NodeType.VOID_FUNC
                i_type = 'void func'
            # for graphviz
            func_head = f"S{S}"
            S += 1
            paras = f"S{S}"
            S += 1
            self.graph.node(func_head, i_type)
            self.graph.node(paras, "paras")
            self.graph.edge(func_head, y_def.graph_node)
            self.graph.edge(y_def.graph_node, paras)
            self.graph.edge(y_def.graph_node, y_def.info['funcbody'].graph_node)
            for j in y_def.info['paras']:
                if j.node_type == NodeType.INT_VAR:
                    arg_head = f"S{S}"
                    S += 1
                    self.graph.node(arg_head, "int")
                    self.graph.edge(arg_head, j.graph_node)
                elif j.node_type == NodeType.POINTER_INT_VAR:
                    arg_head = f"S{S}"
                    S += 1
                    self.graph.node(arg_head, "int*")
                    self.graph.edge(arg_head, j.graph_node)
                elif j.node_type == NodeType.INT_ARRAY:
                    arg_head = f"S{S}"
                    S += 1
                    self.graph.node(arg_head, "int"+"[]"*j.info['size'])
                    self.graph.edge(arg_head, j.graph_node)
                    for k in range(j.info['size']):
                        if j.info[f'{j}'] is not None:
                            self.graph.edge(j.graph_node, j.info[f'{j}'].graph_node)
                        else:
                            self.graph.node(f"S{S}", "ANY")
                            self.graph.edge(j.graph_node, f"S{S}")
                            S += 1
                self.graph.edge(paras, arg_head)
            y_def.graph_node = func_head
            # end of graphviz
            return y_def
        else:
            for i in y_def:
                if i[0].node_type == NodeType.POINTER:
                    # pointer variable
                    if y_type.node_type == NodeType.INT:
                        defvar = Node(NodeType.POINTER_INT_VAR, value=i[1].value, graph_node=f"S{S}")
                        self.graph.node(defvar.graph_node, "int*")
                        self.graph.edge(defvar.graph_node, i[1].graph_node)
                        y_defvars.append(defvar)
                    else:
                        self.__error("VOID Can't be used for POINTER!")
                else:
                    if y_type.node_type == NodeType.INT:
                        # variable or array
                        if len(i[1]):
                            defvar = Node(NodeType.INT_ARRAY, value=i[0].value, graph_node=f"S{S}")
                            self.graph.node(defvar.graph_node, "int"+"[]"*len(i[1]))
                            self.graph.edge(defvar.graph_node, i[0].graph_node)
                            info = {"size": len(i[1])}
                            for j in range(info['size']):
                                info[f'{j}'] = i[1][j]
                                self.graph.edge(i[0].graph_node, i[1][j].graph_node)
                            defvar.info = info
                        else:
                            defvar = Node(NodeType.INT_VAR, value=i[0].value, graph_node=f"S{S}")
                            self.graph.node(defvar.graph_node, "int")
                            self.graph.edge(defvar.graph_node, i[0].graph_node)
                        y_defvars.append(defvar)
                    else:
                        self.__error("VOID Can't be used for VAR or ARRAY")
                S += 1
            return y_defvars

    def __y_type(self) -> Node:
        """
        解析类型

        :return: 返回类型结点
        """
        if self.__accept('INT'):
            return Node(NodeType.INT)
        elif self.__accept('VOID'):
            return Node(NodeType.VOID)
        else:
            self.__error(f"Excepted INT or VOID, Found '{self.__curr_token.value}'")

    def __y_def(self) -> Union[list[list[Node, Node]], Node]:
        """
        解析定义

        :return:
        """
        if self.__accept('TIMES'):
            # pointer variable
            pointer = Node(NodeType.POINTER, "*")
            y_ident = self.__y_ident()
            y_deflist = self.__y_deflist()
            y_defvar = [[pointer, y_ident]]
            if y_deflist is not None:
                y_defvar.extend(y_deflist)
            return y_defvar
        else:
            # variable or array
            y_ident = self.__y_ident()
            y_idtail = self.__y_idtail()
            if type(y_idtail) == Node:
                # for function
                y_idtail.value = y_ident.value
                y_idtail.graph_node = y_ident.graph_node
                y_defvar = y_idtail
            else:
                # for variable or array
                y_defvar = [[y_ident, y_idtail[0]]]
                if len(y_idtail) > 1:
                    y_defvar.extend(y_idtail[1:])
            return y_defvar
        # else:
        #     self._error(f"Except IDENT or '*' in define, Found '{self.__curr_token.value}'")

    def __y_deflist(self) -> Union[list[list[Node, Node]], None]:
        """
        解析定义列表

        :return:
        """
        if self.__accept('COMMA'):
            # get other variables
            y_defdata = self.__y_defdata()
            y_deflist = self.__y_deflist()
            if y_deflist is None:
                return [y_defdata]
            else:
                return y_deflist.append(y_defdata)
        elif self.__accept('SEMICOLON'):
            # end of define
            return None
        else:
            self.__error(f"Excepted ';' or ',' at the first of define_list, Found '{self.__curr_token.value}'")

    def __y_defdata(self) -> Union[list[Node, Node], list[Node, list[Node]]]:
        """
        解析变量定义信息

        :return:
        """
        if self.__accept('TIMES'):
            # for pointer variable
            pointer = Node(NodeType.POINTER)
            ident = self.__y_ident()
            return [pointer, ident]
        else:
            # for variable or array
            ident = self.__y_ident()
            vardef = self.__y_vardef()
            return [ident, vardef]

    def __y_vardef(self) -> list[Node]:
        """
        返回变量定义维度信息

        :return: 返回维度列表，若维度为0则列表为空，证明不是数组
        """
        y_vars = []
        while self.__accept('LBRACE'):
            num = self.__y_num()
            self.__except('RBRACE')
            y_vars.append(num)
        return y_vars

    def __y_idtail(self) -> Union[list[list[Node], Node], Node]:
        """
        对于一个标识符定义，若为函数定义，则其尾部为'(){}'或'();'；若为变量定义，则其后可能跟随若干相同的变量定义。

        :return: 若为函数定义，则返回[参数列表，函数体]。若为变量定义，则为[上个标识符维度，[后续变量定义]]
        """
        if self.__accept('LPAREN'):
            y_para = self.__y_para()
            self.__except('RPAREN')
            y_functail = self.__y_functail()
            return Node(NodeType.FUNC, info={"paras": y_para, "funcbody": y_functail})
        else:
            y_vardef = self.__y_vardef()
            y_deflist = self.__y_deflist()
            tmp = [y_vardef]
            if y_deflist is not None:
                tmp.extend(y_deflist)
            return tmp

    def __y_functail(self) -> Union[Node, None]:
        global B
        """
        解析函数体，函数体可能为空

        :return: 函数体结点，若函数体为空则返回None
        """
        if self.__accept('SEMICOLON'):
            return None
        elif self.__accept('LBRACKET'):
            y_block = Node(NodeType.BLOCK, graph_node=f"B{B}")
            # for graphviz
            self.graph.node(y_block.graph_node, "Block")
            B += 1
            y_subprogram = self.__y_subprogram()
            # for graphviz
            for i in y_subprogram:
                self.graph.edge(y_block.graph_node, i.graph_node)
            y_block.info["subprogram"] = y_subprogram
            self.__except('RBRACKET')
            return y_block
        else:
            self.__error(f"Excepted ';' or '{{' in function body, Found '{self.__curr_token.value}'")

    def __y_para(self) -> list[Node]:
        """
        解析参数列表

        :return: parameter结点列表
        """
        para_list = []
        if self.__curr_token.type != 'RPAREN':
            para_list.append(self.__y_onepara())
            while self.__accept('COMMA'):
                para_list.append(self.__y_onepara())
        return para_list

    def __y_onepara(self) -> Node:
        """
        单个参数解析

        :return: 单个parameter结点
        """
        y_type = self.__y_type()
        y_paradata = self.__y_paradata()
        if y_paradata[0].node_type == NodeType.POINTER:
            if y_type.node_type == NodeType.INT:
                para = Node(NodeType.POINTER_INT_VAR, value=y_paradata[1].value, graph_node=y_paradata[1].graph_node)
                return para
            else:
                self.__error("VOID Can't be used for POINTER!")
        else:
            if y_type.node_type == NodeType.INT:
                if len(y_paradata[1]):
                    para = Node(NodeType.INT_ARRAY, value=y_paradata[0].value, graph_node=y_paradata[0].graph_node)
                    info = {"size": len(y_paradata[1])}
                    for i in range(info['size']):
                        info[f'{i}'] = y_paradata[1][i]
                    para.info = info
                else:
                    para = Node(NodeType.INT_VAR, value=y_paradata[0].value, graph_node=y_paradata[0].graph_node)
                return para
            else:
                self.__error("VOID Can't be used for VAR or ARRAY")

    def __y_paradata(self) -> Union[list[Node, Node], list[Node, list[Node]]]:
        """
        解析参数详细数据：是否为指针变量，是否为数组变量

        :return:
        """
        if self.__accept('TIMES'):
            pointer = Node(NodeType.POINTER)
            ident = self.__y_ident()
            return [pointer, ident]
        else:
            ident = self.__y_ident()
            paradatadetail = self.__y_paradatatail()
            return [ident, paradatadetail]

    def __y_paradatatail(self) -> list[Node]:
        """
        解析数组维度信息【维度可能为0】

        :return: 维度列表，若不是数组则列表为空。
        """
        dem = []
        if self.__accept('LBRACE'):
            if self.__curr_token.type == 'RBRACE':
                self.__next()
                dem.append(None)
            else:
                tmp = self.__y_num()
                dem.append(tmp)
                self.__except('RBRACE')
            while self.__accept('LBRACE'):
                tmp = self.__y_num()
                dem.append(tmp)
                self.__except('RBRACE')
        return dem

    def __y_subprogram(self):
        """
        内部代码块

        :return:
        """
        y_onestatements = []
        while True:
            if self.__curr_token is None or self.__curr_token.type == 'RBRACKET':
                break
            tmp = self.__y_onestatement()
            if tmp is not None:
                if type(tmp) == Node:
                    y_onestatements.append(tmp)
                else:
                    y_onestatements.extend(tmp)
        return y_onestatements

    def __y_onestatement(self) -> Union[list[Node], Node, None]:
        global L
        if self.__accept('INT') or self.__accept('VOID'):
            # for local variable definition
            y_localvars = []
            y_type = Node(NodeType.INT if self.__last_token.type == 'INT' else NodeType.VOID)
            y_defdata = self.__y_defdata()
            y_deflist = self.__y_deflist()
            defvars = [y_defdata]
            if y_deflist is not None:
                defvars.append(y_deflist)
            for i in defvars:
                if i[0].node_type == NodeType.POINTER:
                    # for pointer local variable
                    if y_type.node_type == NodeType.INT:
                        localvar = Node(NodeType.POINTER_INT_VAR, value=i[1].value, graph_node=f"L{L}")
                        # for graphviz
                        self._remove(i[1].graph_node)
                        self.graph.node(localvar.graph_node, "int*")
                        self.graph.edge(localvar.graph_node, i[1].graph_node)
                        L += 1
                        y_localvars.append(localvar)
                    else:
                        self.__error("VOID Can't be used for POINTER!")
                else:
                    if y_type.node_type == NodeType.INT:
                        if len(i[1]):
                            localvar = Node(NodeType.INT_ARRAY, value=i[0].value, graph_node=f"L{L}")
                            tmp = localvar.value
                            info = {'size': len(i[1])}
                            for j in range(info['size']):
                                info[f'{j}'] = i[1][j]
                                tmp += f"[{i[1][j]}]"
                            info['array'] = tmp
                            localvar.info = info
                            # for graphviz
                            self.graph.node(localvar.graph_node, "int")
                            self.graph.edge(localvar.graph_node, i[0].graph_node)
                        else:
                            localvar = Node(NodeType.INT_VAR, value=i[0].value, graph_node=f"L{L}")
                            self.graph.node(localvar.graph_node, "int")
                            self.graph.edge(localvar.graph_node, i[0].graph_node)
                        L += 1
                        y_localvars.append(localvar)
                    else:
                        self.__error("VOID Can't be used for VAR or ARRAY")
            return y_localvars
        else:
            y_statement = self.__y_statement()
            return y_statement

    def __y_statement(self) -> Optional[Node]:
        global T, B
        if self.__accept('WHILE'):
            y_while = Node(NodeType.WHILE, value='WHILE', graph_node=f"T{T}")
            # for graphviz
            self.graph.node(y_while.graph_node, "while")
            T += 1
            self.__except('LPAREN')
            y_expr = self.__y_expr()
            self.__except('RPAREN')
            y_statement = self.__y_statement()
            info = {
                "condition": y_expr,
                "statement": y_statement
            }
            y_while.info = info
            # for graphviz
            self.graph.edge(y_while.graph_node, y_expr.graph_node)
            if y_statement is not None:
                self.graph.edge(y_while.graph_node, y_statement.graph_node)
            return y_while
        elif self.__accept('IF'):
            y_if = Node(NodeType.IF, value='IF', graph_node=f"T{T}")
            # for graphviz
            self.graph.node(y_if.graph_node, "if")
            T += 1
            self.__except('LPAREN')
            y_expr = self.__y_expr()
            self.__except('RPAREN')
            y_statement = self.__y_statement()
            y_elsestat = self.__y_elsestat()
            info = {
                "condition": y_expr,
                "statement": y_statement,
                "elsestat": y_elsestat
            }
            y_if.info = info
            # for graphviz
            self.graph.edge(y_if.graph_node, y_expr.graph_node)
            if y_statement is not None:
                self.graph.edge(y_if.graph_node, y_statement.graph_node)
            if y_elsestat is not None:
                self.graph.edge(y_if.graph_node, y_elsestat.graph_node)
            return y_if
        elif self.__accept('BREAK'):
            y_break = Node(NodeType.BREAK, value='break', graph_node=f"T{T}")
            # for graphviz
            self.graph.node(y_break.graph_node, "break")
            T += 1
            self.__except('SEMICOLON')
            return y_break
        elif self.__accept('CONTINUE'):
            y_continue = Node(NodeType.CONTINUE, value='continue', graph_node=f"T{T}")
            # for graphviz
            self.graph.node(y_continue.graph_node, "continue")
            T += 1
            self.__except('SEMICOLON')
            return y_continue
        elif self.__accept('RETURN'):
            y_return = Node(NodeType.RETURN, value='return', graph_node=f"T{T}")
            # for graphviz
            self.graph.node(y_return.graph_node, "return")
            T += 1
            if not self.__accept('SEMICOLON'):
                y_expr = self.__y_expr()
                y_return.info = {"return_expr": y_expr}
                # for graphviz
                self.graph.edge(y_return.graph_node, y_expr.graph_node)
            self.__except('SEMICOLON')
            return y_return
        elif self.__accept('LBRACKET'):
            y_block = Node(NodeType.BLOCK, graph_node=f"B{B}")
            self.graph.node(y_block.graph_node, "Block")
            B += 1
            y_subprogram = self.__y_subprogram()
            # for graphviz
            for i in y_subprogram:
                self.graph.edge(y_block.graph_node, i.graph_node)
            y_block.info["subprogram"] = y_subprogram
            self.__except('RBRACKET')
            return y_block
        elif self.__accept('SEMICOLON'):
            return None
        else:
            y_expr = self.__y_expr()
            return y_expr

    def __y_elsestat(self) -> Optional[Node]:
        global T
        if self.__accept('ELSE'):
            y_else = Node(NodeType.ELSE, graph_node=f"T{T}")
            # for graphviz
            self.graph.node(y_else.graph_node, "else")
            T += 1
            y_statement = self.__y_statement()
            if y_statement is not None:
                self.graph.edge(y_else.graph_node, y_statement.graph_node)
            y_else.info['statement'] = y_statement
            return y_else
        else:
            return None

    def __y_expr(self) -> Node:
        """

        :return:
        """
        return self.__y_assexpr()

    def __y_assexpr(self) -> Node:
        """


        :return:
        """
        y_orexpr = self.__y_orexpr()
        y_asstail = self.__y_asstail()
        if y_asstail is not None:
            y_asstail.info['lvar'] = y_orexpr
            # for graphviz
            self.graph.edge(y_asstail.graph_node, y_orexpr.graph_node)
            return y_asstail
        else:
            return y_orexpr

    def __y_orexpr(self) -> Node:
        """

        :return:
        """
        y_andexpr = self.__y_andexpr()
        y_ortail = self.__y_ortail()
        if y_ortail is not None:
            y_ortail.info['lvar'] = y_andexpr
            # for graphviz
            self.graph.edge(y_ortail.graph_node, y_andexpr.graph_node)
            return y_ortail
        else:
            return y_andexpr

    def __y_asstail(self) -> Optional[Node]:
        global P
        """

        :return:
        """
        if self.__accept('ASSIGN'):
            y_assign = Node(NodeType.ASSIGN, graph_node=f"P{P}")
            # for graphviz
            self.graph.node(y_assign.graph_node, "=")
            P += 1
            y_assexpr = self.__y_assexpr()
            y_asstail = self.__y_asstail()
            if y_asstail is not None:
                y_asstail.info['lvar'] = y_assexpr
                y_assign.info['rvar'] = y_asstail
                # for graphviz
                self.graph.edge(y_asstail.graph_node, y_assexpr.graph_node)
                self.graph.edge(y_assign.graph_node, y_asstail.graph_node)
                return y_assign
            else:
                y_assign.info['rvar'] = y_assexpr
                # for graphviz
                self.graph.edge(y_assign.graph_node, y_assexpr.graph_node)
                return y_assign
        else:
            return None

    def __y_ortail(self) -> Optional[Node]:
        global P
        """


        :return:
        """
        if self.__accept('LOGIC_OR'):
            y_logic_or = Node(NodeType.LOGIC_OR, graph_node=f"P{P}")
            # for graphviz
            self.graph.node(y_logic_or.graph_node, "||")
            P += 1
            y_andexpr = self.__y_andexpr()
            y_ortail = self.__y_ortail()
            if y_ortail is not None:
                y_ortail.info['lvar'] = y_andexpr
                y_logic_or.info['rvar'] = y_ortail
                # for graphviz
                self.graph.edge(y_ortail.graph_node, y_andexpr.graph_node)
                self.graph.edge(y_logic_or.graph_node, y_ortail.graph_node)
                return y_logic_or
            else:
                y_logic_or.info['rvar'] = y_andexpr
                # for graphviz
                self.graph.edge(y_logic_or.graph_node, y_andexpr.graph_node)
                return y_logic_or
        else:
            return None

    def __y_andexpr(self) -> Node:
        """

        :return:
        """
        y_cmpexpr = self.__y_cmpexpr()
        y_andtail = self.__y_andtail()
        if y_andtail is not None:
            y_andtail.info['lvar'] = y_cmpexpr
            # for graphviz
            self.graph.edge(y_andtail.graph_node, y_cmpexpr.graph_node)
            return y_andtail
        else:
            return y_cmpexpr

    def __y_andtail(self) -> Optional[Node]:
        global P
        """


        :return:
        """
        if self.__accept('LOGIC_AND'):
            y_logic_and = Node(NodeType.LOGIC_AND, graph_node=f"P{P}")
            # for graphviz
            self.graph.node(y_logic_and.graph_node, "&&")
            P += 1
            y_cmpexpr = self.__y_cmpexpr()
            y_andtail = self.__y_andtail()
            if y_andtail is not None:
                y_andtail.info['lvar'] = y_cmpexpr
                y_logic_and.info['rvar'] = y_andtail
                # for graphviz
                self.graph.edge(y_andtail.graph_node, y_cmpexpr.graph_node)
                self.graph.edge(y_logic_and.graph_node, y_andtail.graph_node)
                return y_logic_and
            else:
                y_logic_and.info['rvar'] = y_cmpexpr
                # for graphviz
                self.graph.edge(y_logic_and.graph_node, y_cmpexpr.graph_node)
                return y_logic_and
        else:
            return None

    def __y_cmpexpr(self) -> Node:
        """


        :return:
        """
        y_aloexpr = self.__y_aloexpr()
        y_cmptail = self.__y_cmptail()
        if y_cmptail is not None:
            y_cmptail.info['lvar'] = y_aloexpr
            # for graphviz
            self.graph.edge(y_cmptail.graph_node, y_aloexpr.graph_node)
            return y_cmptail
        else:
            return y_aloexpr

    def __y_cmptail(self) -> Optional[Node]:
        global P
        """


        :return:
        """
        if self.__curr_token.type in ('GEQ', 'GT', 'LT', 'LEQ', 'EQ', 'NEQ'):
            if self.__curr_token.type == 'GEQ':
                cmp = NodeType.GEQ
            elif self.__curr_token.type == 'GT':
                cmp = NodeType.GT
            elif self.__curr_token.type == 'LT':
                cmp = NodeType.LT
            elif self.__curr_token.type == 'LEQ':
                cmp = NodeType.LEQ
            elif self.__curr_token.type == 'EQ':
                cmp = NodeType.EQ
            else:
                cmp = NodeType.NEQ
            self.__next()
            y_cmps = Node(cmp, value=self.__last_token.value, graph_node=f"P{P}")
            # for graphviz
            self.graph.node(y_cmps.graph_node, self.__last_token.value)
            P += 1
            y_aloexpr = self.__y_aloexpr()
            y_cmptail = self.__y_cmptail()
            if y_cmptail is not None:
                y_cmptail.info['lvar'] = y_aloexpr
                y_cmps.info['rval'] = y_cmptail
                # for graphviz
                self.graph.edge(y_cmptail.graph_node, y_aloexpr.graph_node)
                self.graph.edge(y_cmps.graph_node, y_cmptail.graph_node)
                return y_cmps
            else:
                y_cmps.info['rval'] = y_aloexpr
                # for graphviz
                self.graph.edge(y_cmps.graph_node, y_aloexpr.graph_node)
                return y_cmps
        else:
            return None

    def __y_aloexpr(self) -> Node:
        y_item = self.__y_item()
        y_alotail = self.__y_alotail()
        if y_alotail is not None:
            y_alotail.info['lvar'] = y_item
            # for graphviz
            self.graph.edge(y_alotail.graph_node, y_item.graph_node)
            return y_alotail
        else:
            return y_item

    def __y_alotail(self) -> Optional[Node]:
        global P
        """


        :return:
        """
        if self.__accept('PLUS') or self.__accept('MINUS'):
            y_addsub = Node(NodeType.PLUS if self.__last_token.type == 'PLUS' else NodeType.MINUS, graph_node=f"P{P}")
            # for graphviz
            self.graph.node(y_addsub.graph_node, self.__last_token.value)
            P += 1
            y_item = self.__y_item()
            y_alotail = self.__y_alotail()
            if y_alotail is not None:
                y_alotail.info['lvar'] = y_item
                y_addsub.info['rvar'] = y_alotail
                # for graphviz
                self.graph.edge(y_alotail.graph_node, y_item.graph_node)
                self.graph.edge(y_addsub.graph_node, y_alotail.graph_node)
                return y_addsub
            else:
                y_addsub.info['rvar'] = y_item
                # for graphviz
                self.graph.edge(y_addsub.graph_node, y_item.graph_node)
                return y_addsub
        else:
            return None

    def __y_item(self) -> Node:
        """


        :return:
        """
        y_factor = self.__y_factor()
        y_itemtail = self.__y_itemtail()
        if y_itemtail is not None:
            y_itemtail.info['lvar'] = y_factor
            # for graphviz
            self.graph.edge(y_itemtail.graph_node, y_factor.graph_node)
            return y_itemtail
        else:
            return y_factor

    def __y_factor(self) -> Node:
        global P
        """


        :return:
        """
        if self.__curr_token.type in ('NOT', 'MINUS', 'AND', 'TIMES', 'SELF_PLUS', 'SELF_MINUS'):
            if self.__curr_token.type == 'NOT':
                lop = NodeType.NOT
            elif self.__curr_token.type == 'MINUS':
                lop = NodeType.NEGATIVE
            elif self.__curr_token.type == 'AND':
                lop = NodeType.AND
            elif self.__curr_token.type == 'TIMES':
                lop = NodeType.POINTER
            elif self.__curr_token.type == 'SELF_PLUS':
                lop = NodeType.SELF_PLUS
            else:
                lop = NodeType.SELF_MINUS
            self.__next()
            y_lop = Node(lop, value=self.__last_token.value, graph_node=f"P{P}")
            # for graphviz
            self.graph.node(y_lop.graph_node, self.__last_token.value)
            P += 1
            y_factor = self.__y_factor()
            y_factor.info['lop'] = y_lop
            # for graphviz
            self.graph.edge(y_factor.graph_node, y_lop.graph_node)
            return y_factor
        else:
            y_val = self.__y_val()
            return y_val

    def __y_itemtail(self) -> Optional[Node]:
        global P
        """


        :return:
        """
        if self.__accept('TIMES') or self.__accept('DIVIDE'):
            y_muldiv = Node(NodeType.TIMES if self.__last_token.type == 'TIMES' else NodeType.DIVIDE, graph_node=f"P{P}")
            # for graphviz
            self.graph.node(y_muldiv.graph_node, self.__last_token.value)
            P += 1
            y_factor = self.__y_factor()
            y_itemtail = self.__y_itemtail()
            if y_itemtail is not None:
                y_itemtail.info['lvar'] = y_factor
                y_muldiv.info['rvar'] = y_itemtail
                # for graphviz
                self.graph.edge(y_itemtail.graph_node, y_factor.graph_node)
                self.graph.edge(y_muldiv.graph_node, y_itemtail.graph_node)
            else:
                y_muldiv.info['rvar'] = y_factor
                # for graphviz
                self.graph.edge(y_muldiv.graph_node, y_factor.graph_node)
            return y_muldiv
        else:
            return None

    def __y_val(self) -> Node:
        global P
        """
        解析运算元素是否存在右运算符

        :return:
        """
        y_elem = self.__y_elem()
        if self.__accept('SELF_PLUS') or self.__accept('SELF_MINUS'):
            y_rop = Node(NodeType.SELF_PLUS if self.__last_token.type == 'SELF_PLUS' else NodeType.SELF_MINUS,
                       value=self.__last_token.value, graph_node=f"P{P}")
            # for graphviz
            self.graph.node(y_rop.graph_node, self.__last_token.value)
            P += 1
            y_elem.info["rop"] = y_rop
            # for graphviz
            self.graph.edge(y_elem.graph_node, y_rop.graph_node)
        return y_elem

    def __y_elem(self) -> Node:
        global F
        """
        解析单个运算元素

        :return:
        """
        if self.__accept('LPAREN'):
            y_expr = self.__y_expr()
            self.__except('RPAREN')
            return y_expr
        elif self.__accept('NUM'):
            y_num = Node(NodeType.NUM, value=self.__last_token.value, graph_node=f"F{F}")
            # for graphviz
            self.graph.node(y_num.graph_node, self.__last_token.value)
            F += 1
            return y_num
        elif self.__accept('IDENT'):
            y_ident = Node(NodeType.IDENT, value=self.__last_token.value, graph_node=f"F{F}")
            F += 1
            graph_node_value = self.__last_token.value
            y_idexpr = self.__y_idexpr()
            if y_idexpr is not None:
                if type(y_idexpr) == Node:
                    y_ident.node_type = NodeType.ARRAY
                    y_ident.info["pos"] = y_idexpr
                    graph_node_value += "[]"
                    self.graph.edge(y_ident.graph_node, y_idexpr.graph_node)
                elif type(y_idexpr) == list:
                    y_ident.node_type = NodeType.FUNC
                    y_ident.info["args"] = y_idexpr
                    graph_node_value += "()"
                    for i in y_idexpr:
                        self.graph.edge(y_ident.graph_node, i.graph_node)
            # for graphviz
            self.graph.node(y_ident.graph_node, graph_node_value)
            return y_ident
        else:
            self.__error(f"Excepted '(' or NUM or IDENT, Found '{self.__curr_token.value}'")

    def __y_idexpr(self) -> Union[Node, list[Node], None]:
        """
        解析ID相关调用解析式：数组引用、函数调用参数、空

        :return:
        """
        if self.__accept('LBRACE'):
            y_expr = self.__y_expr()
            self.__except('RBRACE')
            return y_expr
        elif self.__accept('LPAREN'):
            y_realargs = self.__y_realarg()
            self.__except('RPAREN')
            return y_realargs
        else:
            return None

    def __y_realarg(self) -> list[Node]:
        """
        返回函数调用参数列表

        :return:
        """
        y_args = []
        y_expr = self.__y_expr()
        if y_expr is not None:
            y_args.append(y_expr)
            while self.__accept('COMMA'):
                y_expr = self.__y_expr()
                if y_expr is None:
                    self.__error("Excepted an expr after ',' in REALARG, Found None")
                y_args.append(y_expr)
        return y_args

    def __y_num(self) -> Node:
        global F
        """
        期望解析数字，若当前不为数字则抛出错误

        :return:
        """
        if self.__accept('NUM'):
            tmp = Node(NodeType.NUM, self.__last_token.value, graph_node=f"F{F}")
            # for graphviz
            self.graph.node(tmp.graph_node, self.__last_token.value)
            F += 1
            return tmp
        else:
            self.__error(f"Excepted NUM, Found '{self.__curr_token.value}'")

    def __y_ident(self) -> Node:
        global F
        """
        期望解析标识符，若当前不为标识符则抛出错误

        :return:
        """
        if self.__accept('IDENT'):
            tmp = Node(NodeType.IDENT, value=self.__last_token.value, graph_node=f"F{F}")
            # for graphviz
            self.graph.node(tmp.graph_node, self.__last_token.value)
            F += 1
            return tmp
        else:
            self.__error(f"Excepted IDENT, Found '{self.__curr_token.value}'")

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：lex.py
@Author ：OrangeJ
@Date ：2022/4/27 13:07
"""

import re
import collections


IDENT = r'(?P<IDENT>[a-zA-Z_][a-zA-Z0-9_]*)'
NUM = r'(?P<NUM>[1-9][0-9]*)'

INT = r'(?P<INT>int)'
VOID = r'(?P<VOID>void)'
WHILE = r'(?P<WHILE>while)'
FOR = r'(?P<FOR>for)'
IF = r'(?P<IF>if)'
ELSE = r'(?P<ELSE>else)'
SWITCH = r'(?P<SWITCH>switch)'
CASE = r'(?P<CASE>case)'
BREAK = r'(?P<BREAK>break)'
CONTINUE = r'(?P<CONTINUE>continue)'
RETURN = r'(?P<RETURN>return)'

ASSIGN = r'(?P<ASSIGN>\=)'
PLUS = r'(?P<PLUS>\+)'
MINUS = r'(?P<MINUS>-)'
TIMES = r'(?P<TIMES>\*)'
DIVIDE = r'(?P<DIVIDE>/)'
MOD = r'(?P<MOD>\%)'
NOT = r'(?P<NOT>\!)'
AND = r'(?P<AND>&)'
OR = r'(?P<OR>\|)'
LOGIC_AND = r'(?P<LOGIC_AND>&&)'
LOGIC_OR = r'(?P<LOGIC_OR>\|\|)'
GT = r'(?P<GT>\>)'
GEQ = r'(?P<GEQ>\>\=)'
LT = r'(?P<LT>\<)'
LEQ = r'(?P<LEQ>\<\=)'
EQ = r'(?P<EQ>\=\=)'
NEQ = r'(?P<NEQ>\!\=)'
SELF_PLUS = r'(?P<SELF_PLUS>\+\+)'
SELF_MINUS = r'(?P<SELF_MINUS>--)'
LPAREN = r'(?P<LPAREN>\()'
RPAREN = r'(?P<RPAREN>\))'
LBRACE = r'(?P<LBRACE>\[)'
RBRACE = r'(?P<RBRACE>\])'
LBRACKET = r'(?P<LBRACKET>\{)'
RBRACKET = r'(?P<RBRACKET>\})'
COMMA = r'(?P<COMMA>,)'
SEMICOLON = r'(?P<SEMICOLON>;)'
LINE_COMMENT = r'(?P<LINE_COMMENT>//.*)'
BLOCK_COMMENT = r'(?P<BLOCK_COMMENT>/\*(.|\n)*?\*/)'
UNKNOWN = r'(?P<UNKNOWN>.+?)'

WS = r'(?P<WS>[\s])'
NL = r'(?P<NL>(\r\n|\n))'

patterns = [NUM, LOGIC_AND, LOGIC_OR, SELF_PLUS, SELF_MINUS, EQ, NEQ, LEQ, GEQ,
            COMMA, SEMICOLON, LINE_COMMENT, BLOCK_COMMENT,
            PLUS, MINUS, TIMES, DIVIDE, MOD, AND, OR, NOT, ASSIGN, LT, GT,
            LPAREN, RPAREN, LBRACE, RBRACE, LBRACKET, RBRACKET,
            INT, VOID, WHILE, FOR, IF, ELSE, SWITCH, CASE, BREAK, CONTINUE, RETURN,
            NL, WS, IDENT, UNKNOWN]


Token = collections.namedtuple('Token', ['type', 'value', 'line'])


class Lex:
    def __init__(self, content: str):
        self.content = content
        self.token_map = re.compile('|'.join(patterns))

    def get_token(self):
        line = 1
        scanner = self.token_map.scanner(self.content)
        for m in iter(scanner.match, None):
            tok = Token(m.lastgroup, m.group(), line)
            if tok.type == 'NL' or tok.type == 'LINE_COMMENT':
                line += 1
            elif tok.type == 'BLOCK_COMMENT':
                line_count = len(re.findall(r'\n', tok.value))
                line += line_count
            elif tok.type != 'WS':
                yield tok

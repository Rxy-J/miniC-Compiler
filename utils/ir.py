#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：ir.py
@Author ：OrangeJ
@Date ：2022/5/9 14:48
"""

import re

DEFINE = "define"
DECLARE = "declare"

GLOBAL_PREFIX = "@"
LOCAL_PREFIX = "%"

VAR_NAME_PATTERN = r'[-a-zA-Z_][-a-zA-Z0-9_]*'


"""
LLVM Global Variable Definition

@<GlobalVarName> = [Linkage] [PreemptionSpecifier] [Visibility]
                   [DLLStorageClass] [ThreadLocal]
                   [(unnamed_addr|local_unnamed_addr)] [AddrSpace]
                   [ExternallyInitialized]
                   <global | constant> <Type> [<InitializerConstant>]
                   [, section "name"] [, partition "name"]
                   [, comdat [($name)]] [, align <Alignment>]
                   (, !name !N)*
                   
LLVM Function Definition

define [linkage] [PreemptionSpecifier] [visibility] [DLLStorageClass]
       [cconv] [ret attrs]
       <ResultType> @<FunctionName> ([argument list])
       [(unnamed_addr|local_unnamed_addr)] [AddrSpace] [fn Attrs]
       [section "name"] [partition "name"] [comdat [($name)]] [align N]
       [gc] [prefix Constant] [prologue Constant] [personality Constant]
       (!name !N)* { ... }
       
LLVM Function Parameter Definition(a comma separated sequence of arguments)

<type> [parameter Attrs] [name]

LLVM Alias Definition(for variable)

@<Name> = [Linkage] [PreemptionSpecifier] [Visibility] [DLLStorageClass] [ThreadLocal] 
          [(unnamed_addr|local_unnamed_addr)] alias <AliaseeTy>, <AliaseeTy>* @<Aliasee>
          [, partition "name"]

LLVM Ifunc Definition(for function)

@<Name> = [Linkage] [PreemptionSpecifier] [Visibility] ifunc <IFuncTy>, <ResolverTy>* @<Resolver>
          [, partition "name"]
          
          
"""

"""
for comparison, LLVM provide an instruction: icmp

the syntax of 'icmp':

<result> = icmp <cond> <ty> <op1>, <op2>   ; yields i1 or <N x i1>:result

cond: it's not a value. it uses a keyword to guide operation.

eq: equal
ne: not equal
ugt: unsigned greater than
uge: unsigned greater or equal
ult: unsigned less than
ule: unsigned less or equal
sgt: signed greater than
sge: signed greater or equal
slt: signed less than
sle: signed less or equal

the rules of icmp in every condition:

eq: yields true if the operands are equal, false otherwise. No sign interpretation is necessary or performed.
ne: yields true if the operands are unequal, false otherwise. No sign interpretation is necessary or performed.
ugt: interprets the operands as unsigned values and yields true if op1 is greater than op2.
uge: interprets the operands as unsigned values and yields true if op1 is greater than or equal to op2.
ult: interprets the operands as unsigned values and yields true if op1 is less than op2.
ule: interprets the operands as unsigned values and yields true if op1 is less than or equal to op2.
sgt: interprets the operands as signed values and yields true if op1 is greater than op2.
sge: interprets the operands as signed values and yields true if op1 is greater than or equal to op2.
slt: interprets the operands as signed values and yields true if op1 is less than op2.
sle: interprets the operands as signed values and yields true if op1 is less than or equal to op2.

"""

"""
the syntax of 'br':

br i1 <cond>, label <iftrue>, label <iffalse>
br label <dest>          ; Unconditional branch

It's important to remind that the condition value's length(or width) must be 1.     
"""

"""
Use icmp causes a problem. the length of return value of icmp is 1, but the length of int is 32.
And another problem is instruction 'br' points that the condition value's length must be 1.

Therefore we need convert register length to correct length before jump action or after comparison.

use instruction 'zext' to extend register length.
The syntax of 'zext' is:

<result> = zext <ty> <value> to <ty2> 

if we except a small length of the value(only for int to bool), use 'icmp'.

"""



class LLVM:
    def __init__(self):
        pass

    def __error(self, msg: str, lineno: int):
        print(f"[ERROR] [{lineno}]: {msg}")

    def set_comment(self, content: str):
        return f"; {content}"

    def set_global_var(self, name: str, size: int = 32):
        if re.match(VAR_NAME_PATTERN, name) is None:
            self.__error(f"{name} is not match GlobalVarName requirement: {VAR_NAME_PATTERN}", -1)
            return None
        return f"{DEFINE} i{size} {GLOBAL_PREFIX}{name}"


#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：ir.py
@Author ：OrangeJ
@Date ：2022/5/9 14:48
"""

DEFINE = "define"
DECLARE = "declare"

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


class llvm:
    def __init__(self):
        pass

    def set_comment(self, content: str):
        return f"; {content}"

    def set_global_val(self, name: str, size: int = 32):
        return f"{DEFINE} i{size} {name}"
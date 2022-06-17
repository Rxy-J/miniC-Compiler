#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：ir.py
@Author ：OrangeJ
@Date ：2022/5/9 14:48
"""

import re
import hashlib
import random
from collections import namedtuple

from utils.analyzer import Sentence, Sentence_Type

DEFINE = "define"
DECLARE = "declare"

GLOBAL_PREFIX = "@"
LOCAL_PREFIX = "%"

VAR_NAME_PATTERN = r'[-a-zA-Z_][-a-zA-Z0-9_]*'

STD_FILE = """
@.str = private unnamed_addr constant [3 x i8] c"%d\\00", align 1
@.str.1 = private unnamed_addr constant [3 x i8] c"%c\\00", align 1
@.str.2 = private unnamed_addr constant [4 x i8] c"%d\\0A\\00", align 1
@.str.3 = private unnamed_addr constant [4 x i8] c"%c\\0A\\00", align 1
@.str.4 = private unnamed_addr constant [4 x i8] c"%d:\\00", align 1
@.str.5 = private unnamed_addr constant [4 x i8] c" %d\\00", align 1
@.str.6 = private unnamed_addr constant [2 x i8] c"\\0A\\00", align 1
@.str.7 = private unnamed_addr constant [4 x i8] c"%s\\0A\\00", align 1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @getint() #0 {
  %1 = alloca i32, align 4
  %2 = call i32 (i8*, ...) @__isoc99_scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str, i64 0, i64 0), i32* %1)
  %3 = load i32, i32* %1, align 4
  ret i32 %3
}

declare dso_local i32 @__isoc99_scanf(i8*, ...) #1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @getch() #0 {
  %1 = alloca i8, align 1
  %2 = call i32 (i8*, ...) @__isoc99_scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str.1, i64 0, i64 0), i8* %1)
  %3 = load i8, i8* %1, align 1
  %4 = sext i8 %3 to i32
  ret i32 %4
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @getarray(i32* %0) #0 {
  %2 = alloca i32*, align 8
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  store i32* %0, i32** %2, align 8
  %5 = call i32 (i8*, ...) @__isoc99_scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str, i64 0, i64 0), i32* %3)
  store i32 0, i32* %4, align 4
  br label %6

6:                                                ; preds = %16, %1
  %7 = load i32, i32* %4, align 4
  %8 = load i32, i32* %3, align 4
  %9 = icmp slt i32 %7, %8
  br i1 %9, label %10, label %19

10:                                               ; preds = %6
  %11 = load i32*, i32** %2, align 8
  %12 = load i32, i32* %4, align 4
  %13 = sext i32 %12 to i64
  %14 = getelementptr inbounds i32, i32* %11, i64 %13
  %15 = call i32 (i8*, ...) @__isoc99_scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str, i64 0, i64 0), i32* %14)
  br label %16

16:                                               ; preds = %10
  %17 = load i32, i32* %4, align 4
  %18 = add nsw i32 %17, 1
  store i32 %18, i32* %4, align 4
  br label %6

19:                                               ; preds = %6
  %20 = load i32, i32* %3, align 4
  ret i32 %20
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @putint(i32 %0) #0 {
  %2 = alloca i32, align 4
  store i32 %0, i32* %2, align 4
  %3 = load i32, i32* %2, align 4
  %4 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.2, i64 0, i64 0), i32 %3)
  ret void
}

declare dso_local i32 @printf(i8*, ...) #1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @putch(i32 %0) #0 {
  %2 = alloca i32, align 4
  store i32 %0, i32* %2, align 4
  %3 = load i32, i32* %2, align 4
  %4 = trunc i32 %3 to i8
  %5 = sext i8 %4 to i32
  %6 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.3, i64 0, i64 0), i32 %5)
  ret void
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @putarray(i32 %0, i32* %1) #0 {
  %3 = alloca i32, align 4
  %4 = alloca i32*, align 8
  %5 = alloca i32, align 4
  store i32 %0, i32* %3, align 4
  store i32* %1, i32** %4, align 8
  %6 = load i32, i32* %3, align 4
  %7 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.4, i64 0, i64 0), i32 %6)
  store i32 0, i32* %5, align 4
  br label %8

8:                                                ; preds = %19, %2
  %9 = load i32, i32* %5, align 4
  %10 = load i32, i32* %3, align 4
  %11 = icmp slt i32 %9, %10
  br i1 %11, label %12, label %22

12:                                               ; preds = %8
  %13 = load i32*, i32** %4, align 8
  %14 = load i32, i32* %5, align 4
  %15 = sext i32 %14 to i64
  %16 = getelementptr inbounds i32, i32* %13, i64 %15
  %17 = load i32, i32* %16, align 4
  %18 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.5, i64 0, i64 0), i32 %17)
  br label %19

19:                                               ; preds = %12
  %20 = load i32, i32* %5, align 4
  %21 = add nsw i32 %20, 1
  store i32 %21, i32* %5, align 4
  br label %8

22:                                               ; preds = %8
  %23 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.6, i64 0, i64 0))
  ret void
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @putstr(i8* %0) #0 {
  %2 = alloca i8*, align 8
  store i8* %0, i8** %2, align 8
  %3 = load i8*, i8** %2, align 8
  %4 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.7, i64 0, i64 0), i8* %3)
  ret void
}


"""

END_FILE = """
attributes #0 = { noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"clang version 10.0.0-4ubuntu1 "}

"""

T_V = namedtuple("T_V", ["type", "value"])


def rand(typ: int = 0, length: int = 6) -> str:
    Digit = "0123456789"
    LAlpha = "abcdefghijklmnopqrstuvwxyz"
    BAlpha = "ABCDEFGHIJKLMNOPQRISUVWXYZ"
    if typ < 1:
        target = Digit + LAlpha + BAlpha
    elif typ < 2:
        target = Digit + LAlpha
    elif typ < 3:
        target = LAlpha + BAlpha
    else:
        target = Digit
    res = ""
    for i in range(length):
        res += random.choice(target)
    return res


class LLVM:
    """
    仅实现最基础的（miniC会用到的）部分。后续重构会完善
    """

    def __init__(self):
        self.tab_counter = 0
        self.error = False

    def __error(self, msg: str, lineno: int):
        print(f"[ERROR] [{lineno}]: {msg}")
        self.error = True

    def set_tab(self, inst: str) -> str:
        return "\t" * self.tab_counter + inst

    def set_res(self, res: str, inst: str) -> str:
        return f"{res} = {inst}"

    def set_type(self, size: int, dime: list = None) -> str:
        ty = f"i{size}"
        if dime:
            for i in dime[::-1]:
                if i:
                    ty = f"[{i} x {ty}]"
                else:
                    ty = f"{ty}*"
        return ty

    # basic instruction format
    def __inst(self, binop: str, ty: str, op1: str, op2: str) -> str:
        inst = "{} {} {}, {}"

        return inst.format(binop, ty, op1, op2)

    def __inst_with_exact(self, binop: str, ty: str, op1: str, op2: str, exact: bool = False) -> str:
        inst = "{} {} {}, {}"
        inst_exact = "{} exact {} {}, {}"

        if exact:
            return inst_exact.format(binop, ty, op1, op2)
        else:
            return inst.format(binop, ty, op1, op2)

    def __inst_with_nuw_nsw(self, binop: str, ty: str, op1: str, op2: str, nuw: bool = False, nsw: bool = False) -> str:
        inst = "{} {} {}, {}"
        inst_nuw = "{} nuw {} {}, {}"
        inst_nsw = "{} nsw {} {}, {}"
        inst_all = "{} nuw nsw {} {}, {}"

        if nuw:
            if nsw:
                return inst_all.format(binop, ty, op1, op2)
            else:
                return inst_nuw.format(binop, ty, op1, op2)
        elif nsw:
            return inst_nsw.format(binop, ty, op1, op2)
        else:
            return inst.format(binop, ty, op1, op2)

    def set_label_(self, label: str) -> str:
        return f"{label}:"

    def set_comment_(self, content: str):
        return f"; {content}"

    def set_global_var_(self, v_type: str = "i32", is_array: bool = True):
        if is_array:
            return f"common dso_local global {v_type} 0"
        else:
            return f"common dso_local global {v_type} zeroinitializer"

    def set_func_(self, name: str, ret_type: str, args: list[T_V]):
        args = [f"{i.type} {i.value}" for i in args]
        paras = ', '.join(args)
        return f"{DEFINE} {ret_type} @{name} ({paras}) #0 {{"

    def ret_(self, ret_type: str = None, ret_value: str = None) -> str:
        ret = "ret"
        inst = "{} {} {}"
        inst_void = "{} void"
        if ret_type is None and ret_value is None:
            return inst_void.format(ret)
        elif ret_value is None or ret_type is None:
            self.__error("return error", 0)
        else:
            return inst.format(ret, ret_type, ret_value)

    def br_(self, cond: str = None, iftrue: str = None, iffalse: str = None, dest: str = None) -> str:
        """
        注意br指令

        当设置dest参数时，认为使用无条件跳转
        只有未设置dest且设置cond参数时，认为使用条件跳转

        :param cond:
        :param iftrue:
        :param iffalse:
        :param dest:
        :return:
        """
        br = "br"
        inst_cond = "{} i1 {}, label %{}, label %{}"
        inst_uncond = "{} label %{}"
        if dest:
            return inst_uncond.format(br, dest)
        else:
            if cond:
                if iftrue is None or iffalse is None:
                    self.__error("branch true label or false label lost", 0)
                else:
                    return inst_cond.format(br, cond, iftrue, iffalse)
            else:
                self.__error("unset branch", 0)

    # binary operation instruction
    def add_(self, ty: str, op1: str, op2: str, nuw: bool = False, nsw: bool = False) -> str:
        return self.__inst_with_nuw_nsw("add", ty, op1, op2, nuw, nsw)

    def sub_(self, ty: str, op1: str, op2: str, nuw: bool = False, nsw: bool = False) -> str:
        return self.__inst_with_nuw_nsw("sub", ty, op1, op2, nuw, nsw)

    def mul_(self, ty: str, op1: str, op2: str, nuw: bool = False, nsw: bool = False) -> str:
        return self.__inst_with_nuw_nsw("mul", ty, op1, op2, nuw, nsw)

    def udiv_(self, ty: str, op1: str, op2: str, exact: bool = False) -> str:
        return self.__inst_with_exact("udiv", ty, op1, op2, exact)

    def sdiv_(self, ty: str, op1: str, op2: str, exact: bool = False) -> str:
        return self.__inst_with_exact("sdiv", ty, op1, op2, exact)

    def urem_(self, ty: str, op1: str, op2: str) -> str:
        return self.__inst("urem", ty, op1, op2)

    def srem_(self, ty: str, op1: str, op2: str) -> str:
        return self.__inst("srem", ty, op1, op2)

    def shl_(self, ty: str, op1: str, op2: str, nuw: bool = False, nsw: bool = False) -> str:
        return self.__inst_with_nuw_nsw("shl", ty, op1, op2, nuw, nsw)

    def lshr_(self, ty: str, op1: str, op2: str, exact: bool = False) -> str:
        return self.__inst_with_exact("lshr", ty, op1, op2, exact)

    def ashr_(self, ty: str, op1: str, op2: str, exact: bool = False) -> str:
        return self.__inst_with_exact("ashr", ty, op1, op2, exact)

    def and_(self, ty: str, op1: str, op2: str) -> str:
        return self.__inst("and", ty, op1, op2)

    def or_(self, ty: str, op1: str, op2: str) -> str:
        return self.__inst("or", ty, op1, op2)

    def xor_(self, ty: str, op1: str, op2: str) -> str:
        return self.__inst("xor", ty, op1, op2)

    # vector relate instruction
    def extractelement_(self, ty: str, n: int, val: str, ty2: str, idx: int, vc: bool = False) -> str:
        extractelement = "extractelement"
        inst = "{} <{} x {}> {}, {} {}"
        inst_vc = "{} <vscale x {} x {}> {}, {} {}"

        if vc:
            return inst_vc.format(extractelement, n, ty, val, ty2, idx)
        else:
            return inst.format(extractelement, n, ty, val, ty2, idx)

    def insertelement_(self, ty: str, n: int, val: str, elt: str, ty2: str, idx: int, vc: bool = False) -> str:
        insertelement = "insertelement"
        inst = "{} <{} x {}> {}, {} {}, {} {}"
        inst_vc = "{} <vscale x {} x {}> {}, {} {}, {} {}"

        if vc:
            return inst_vc.format(insertelement, n, ty, val, ty, elt, ty2, idx)
        else:
            return inst.format(insertelement, n, ty, val, ty, elt, ty2, idx)

    def alloca_(self, ty: str, init_value: int = None, align: int = None):
        inst = "alloca {}"
        inst_init = f"{inst}, {{}} {{}}"
        inst_align = f"{inst}, align {{}}"
        inst_init_align = f"{inst}, {{}} {{}}, align {{}}"
        if init_value:
            if align:
                return inst_init_align.format(ty, ty, init_value, align)
            else:
                return inst_init.format(ty, ty, init_value)
        elif align:
            return inst_align.format(ty, align)
        else:
            return inst.format(ty)

    def load_(self, ty: str, ptr: str):
        inst = "load {}, {}* {}"
        return inst.format(ty, ty, ptr)

    def store_(self, ty: str, value: str, ptr: str):
        inst = "store {} {}, {}* {}"
        return inst.format(ty, value, ty, ptr)

    def sext_(self, ty: str, val: str, ty2: str):
        sext = "sext"
        inst = "{} {} {} to {}"

        return inst.format(sext, ty, val, ty2)

    def zext_(self, ty: str, val: str, ty2: str):
        zext = "zext"
        inst = "{} {} {} to {}"

        return inst.format(zext, ty, val, ty2)

    def icmp_(self, cond: str, ty: str, op1: str, op2: str) -> str:
        icmp = "icmp"
        inst = "{} {} {} {}, {}"

        if cond not in ("eq", "ne", "ult", "ule", "ugt", "uge", "slt", "sle", "sgt", "sge"):
            self.__error("unknown icmp type", 0)
        return inst.format(icmp, cond, ty, op1, op2)

    def eq_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("eq", ty, op1, op2)

    def neq_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("ne", ty, op1, op2)

    def slt_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("slt", ty, op1, op2)

    def ult_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("ult", ty, op1, op2)

    def sgt_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("sgt", ty, op1, op2)

    def ugt_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("ugt", ty, op1, op2)

    def sle_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("sle", ty, op1, op2)

    def ule_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("ule", ty, op1, op2)

    def sge_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("sge", ty, op1, op2)

    def uge_(self, ty: str, op1: str, op2: str) -> str:
        return self.icmp_("uge", ty, op1, op2)

    def call_(self, ty: str, fnval: str, arg_list: list[T_V]) -> str:
        call = "call"
        inst = "{} {} @{} ({})"

        args = [f"{i.type} {i.value}" for i in arg_list]
        args = ", ".join(args)

        return inst.format(call, ty, fnval, args)

    # array relate instruction
    def getelementptr_(self, t_ty: str, s_ty: str, ptrval: str, i_ty: str, idx: int, NoF: bool = False) -> str:
        inst = "getelementptr inbounds {}, {} {}, i32 0, {} {}"
        inst_nof = "getelementptr inbounds {}, {} {}, {} {}"
        if NoF:
            return inst_nof.format(t_ty, s_ty, ptrval, i_ty, idx)
        else:
            return inst.format(t_ty, s_ty, ptrval, i_ty, idx)

    def phi_(self, t_ty: str, flags: list[dict]) -> str:
        inst = "phi {} {}"
        flags = [f"[{i.get('value')}, %{i.get('label')}]" for i in flags]
        flags = ", ".join(flags)
        return inst.format(t_ty, flags)


class IRGenerator:
    def __init__(self, sentences: list[Sentence], ir: type):
        self.sentences = sentences
        self.ir: LLVM = ir()
        self.GDS = [Sentence_Type.DEFINE_GLOBAL_VAR, Sentence_Type.DEFINE_GLOBAL_ARRAY]
        self.LDS = [Sentence_Type.DEFINE_LOCAL_VAR, Sentence_Type.DEFINE_LOCAL_ARRAY]
        self.BC = [Sentence_Type.ASSIGN,
                   Sentence_Type.ADD,
                   Sentence_Type.MINUS,
                   Sentence_Type.TIMES,
                   Sentence_Type.DIVIDE,
                   Sentence_Type.MOD,
                   Sentence_Type.XOR]
        self.LC = [Sentence_Type.EQ,
                   Sentence_Type.NEQ,
                   Sentence_Type.LT,
                   Sentence_Type.LEQ,
                   Sentence_Type.GT,
                   Sentence_Type.GEQ]
        self.J = [Sentence_Type.JMP, Sentence_Type.IF_JMP]
        self.F = [Sentence_Type.DEFINE_FUNC, Sentence_Type.FUNC_END]
        self.res = []
        self.used_label = set()

    def get_ir(self) -> list[str]:
        self.res.append(STD_FILE)
        self.__process()
        self.res.append(END_FILE)
        # self.__remove_unused_label()
        if self.ir.error:
            self.res = []
        return self.res

    def __process(self):
        for i in self.sentences:
            if i.label is not None:
                self.res.append(self.ir.set_label_(i.label))
            if i.sentence_type in self.GDS:
                self.__g_GDS(i)
            elif i.sentence_type in self.LDS:
                self.__g_LDS(i)
            elif i.sentence_type in self.BC:
                self.__g_BC(i)
            elif i.sentence_type in self.LC:
                self.__g_LC(i)
            elif i.sentence_type in self.J:
                self.__g_J(i)
            elif i.sentence_type in self.F:
                self.__g_F(i)
            elif i.sentence_type is Sentence_Type.CALL:
                args = []
                f_type = "i32" if i.info['func_type'] == 'int' else 'void'
                avar = i.info.get('avar', None)
                if avar and avar.get('dimension') is not None:
                    avar = self.__proc_array(avar)
                for para in i.info['args']:
                    if para.get('dimension', None):
                        para = self.__proc_array(para)
                        v_type = self.ir.set_type(para['size'])
                    elif para.get('define_dime', None):
                        dd = para.get('define_dime', None)
                        t = [{"type": "num", "value": 0, "size": 32} for i in range(len(dd))]
                        n_para = {
                            "type": para.get("type"),
                            "reg": para.get("reg"),
                            "size": para.get("size"),
                            "dimension": t,
                            "define_dime": dd
                        }
                        para = self.__proc_array(n_para, False)
                        v_type = self.ir.set_type(para['size'], [None])
                    else:
                        v_type = self.ir.set_type(para['size'])
                    val = para.get('reg') if para.get('reg') else para.get('value')
                    args.append(T_V(v_type, val))
                ir = self.ir.call_(f_type, i.info['func'], args)
                if avar:
                    ir = self.ir.set_res(avar['reg'], ir)
                self.res.append(self.ir.set_tab(ir))
            elif i.sentence_type is Sentence_Type.RETURN:
                ret = i.info.get('return_reg', None)
                if ret:
                    if ret.get('dimension', None):
                        ret = self.__proc_array(ret)
                    val = ret.get('reg') if ret.get('reg') else ret.get('value')
                    v_type = self.ir.set_type(ret['size'])
                    ir = self.ir.ret_(v_type, val)
                else:
                    ir = self.ir.ret_()
                self.res.append(self.ir.set_tab(ir))
            elif i.sentence_type is Sentence_Type.ZEXT:
                rvar = i.info['rvar']
                avar = i.info['avar']
                s_type = self.ir.set_type(rvar['size'])
                t_type = self.ir.set_type(avar['size'])
                ir = self.ir.zext_(s_type, rvar['reg'], t_type)
                ir = self.ir.set_res(avar['reg'], ir)
                self.res.append(self.ir.set_tab(ir))
            elif i.sentence_type is Sentence_Type.LOAD:
                avar: dict = i.info['avar']
                if isinstance(avar.get('dimension'), list):
                    avar = self.__proc_array(avar)
                rvar: dict = i.info['rvar']
                if isinstance(rvar.get('dimension'), list):
                    rvar = self.__proc_array(rvar)
                    r_type = self.ir.set_type(rvar['size'])
                else:
                    r_type = self.ir.set_type(avar['size'], rvar.get('define_dime'))
                a_val = avar.get('reg')
                r_val = rvar.get('reg')
                ir = self.ir.load_(r_type, r_val)
                ir = self.ir.set_res(a_val, ir)
                self.res.append(self.ir.set_tab(ir))
            elif i.sentence_type is Sentence_Type.PHI:
                avar: dict = i.info['avar']
                if isinstance(avar.get('dimension'), list):
                    avar = self.__proc_array(avar)
                t_ty = self.ir.set_type(i.info['size'])
                flags = i.info['flags']
                ir = self.ir.phi_(t_ty, flags)
                ir = self.ir.set_res(avar.get('reg'), ir)
                self.res.append(self.ir.set_tab(ir))
            else:
                print(f"Unknown Sentence Type {i.sentence_type.name}")

    def __remove_unused_label(self):
        label_pattern = "[%s]*(L[0-9a-zA-Z]+):[%s]*"
        for i in self.res:
            t = re.findall(label_pattern, i)
            if t:
                label = t[0]
                if label not in self.used_label:
                    self.res.remove(i)

    def __proc_array(self, var: dict, load: bool = True) -> dict:
        d = var.get('dimension')
        dd = var.get('define_dime')
        dd = dd[:]
        ptr = var.get('reg')
        t_ptr = ptr.replace("@", "%")
        if not dd[0]:
            suffix = hashlib.md5(rand().encode('utf-8')).hexdigest()[:6]
            t_ptr = f"{t_ptr}_{suffix}"
            t_type = self.ir.set_type(var.get('size'), dd)
            ir = self.ir.load_(t_type, ptr)
            ir = self.ir.set_res(t_ptr, ir)
            self.res.append(self.ir.set_tab(ir))
            ptr = t_ptr
            t = d[0]
            if len(dd) == 1:
                dd = None
                d = []
            else:
                dd = dd[1:]
                d = d[1:]
            if t.get('dimension'):
                t = self.__proc_array(t)
            suffix = hashlib.md5(rand().encode('utf-8')).hexdigest()[:6]
            t_ptr = f"{t_ptr}_{suffix}"
            t_type = self.ir.set_type(var.get('size'), dd)
            v_type = self.ir.set_type(t.get('size'))
            val = t.get('reg') if t.get('reg') else t.get('value')
            ir = self.ir.getelementptr_(t_type, f"{t_type}*", ptr, v_type, val, True)
            ir = self.ir.set_res(t_ptr, ir)
            self.res.append(self.ir.set_tab(ir))
            ptr = t_ptr
        for curr in d:
            if curr.get('dimension'):
                curr = self.__proc_array(curr)
            suffix = hashlib.md5(rand().encode('utf-8')).hexdigest()[:6]
            t_ptr = f"{t_ptr}_{suffix}"
            val = curr.get('reg') if curr.get('reg') else curr.get('value')
            v_type = self.ir.set_type(curr.get('size'))
            if len(dd) == 1 and not dd[0]:
                a_type = self.ir.set_type(var.get('size'))
            else:
                a_type = self.ir.set_type(var.get('size'), dd)
            ir = self.ir.getelementptr_(a_type, f"{a_type}*", ptr, v_type, val)
            ir = self.ir.set_res(t_ptr, ir)
            self.res.append(self.ir.set_tab(ir))
            ptr = t_ptr
            if len(dd) > 1:
                dd = dd[1:]

        if load:
            r_ptr = f"{t_ptr}_load"
            ir = self.ir.load_(self.ir.set_type(var.get('size')), t_ptr)
            ir = self.ir.set_res(r_ptr, ir)
            self.res.append(self.ir.set_tab(ir))
        else:
            r_ptr = t_ptr
        return {
            "reg": r_ptr,
            "size": var.get('size')
        }

    def __g_GDS(self, sent: Sentence) -> None:
        if sent.info.get("dimension", None) is None:
            v_type = self.ir.set_type(sent.info['size'])
            ir = self.ir.set_global_var_(v_type)
        else:
            v_type = self.ir.set_type(sent.info['size'], sent.info['define_dime'])
            ir = self.ir.set_global_var_(v_type, False)
        ir = self.ir.set_res(sent.info['reg'], ir)
        self.res.append(self.ir.set_tab(ir))

    def __g_LDS(self, sent: Sentence) -> None:
        if sent.info.get("dimension", None) is None:
            v_type = self.ir.set_type(sent.info['size'])
            ir = self.ir.alloca_(v_type, align=4)
        else:
            v_type = self.ir.set_type(sent.info['size'], sent.info['define_dime'])
            ir = self.ir.alloca_(v_type, align=16)
        ir = self.ir.set_res(sent.info['reg'], ir)
        self.res.append(self.ir.set_tab(ir))

    def __g_BC(self, sent: Sentence) -> None:
        rvar: dict = sent.info['rvar']
        if isinstance(rvar.get('dimension'), list):
            rvar = self.__proc_array(rvar)
            r_type = self.ir.set_type(rvar['size'])
        else:
            r_type = self.ir.set_type(rvar['size'], rvar.get('define_dime'))
        avar: dict = sent.info['avar']
        if isinstance(avar.get('dimension'), list):
            avar = self.__proc_array(avar, False)
        r_val = rvar.get('reg') if rvar.get('reg') else rvar.get('value')
        if sent.sentence_type is Sentence_Type.ASSIGN:
            ir = self.ir.store_(r_type, r_val, avar.get('reg'))
        else:
            lvar: dict = sent.info['lvar']
            if lvar.get('dimension'):
                lvar = self.__proc_array(lvar)
            l_val = lvar.get('reg') if lvar.get('reg') else lvar.get('value')
            if sent.sentence_type is Sentence_Type.ADD:
                ir = self.ir.add_(r_type, l_val, r_val, nsw=True)
            elif sent.sentence_type is Sentence_Type.MINUS:
                ir = self.ir.sub_(r_type, l_val, r_val, nsw=True)
            elif sent.sentence_type is Sentence_Type.TIMES:
                ir = self.ir.mul_(r_type, l_val, r_val, nsw=True)
            elif sent.sentence_type is Sentence_Type.DIVIDE:
                ir = self.ir.sdiv_(r_type, l_val, r_val)
            elif sent.sentence_type is Sentence_Type.MOD:
                ir = self.ir.srem_(r_type, l_val, r_val)
            else:  # sent.sentence_type is Sentence_Type.XOR
                ir = self.ir.xor_(r_type, l_val, r_val)
            ir = self.ir.set_res(avar['reg'], ir)
        self.res.append(self.ir.set_tab(ir))

    def __g_LC(self, sent: Sentence) -> None:
        if sent.sentence_type is Sentence_Type.EQ:
            logic = self.ir.eq_
        elif sent.sentence_type is Sentence_Type.NEQ:
            logic = self.ir.neq_
        elif sent.sentence_type is Sentence_Type.LT:
            logic = self.ir.slt_
        elif sent.sentence_type is Sentence_Type.LEQ:
            logic = self.ir.sle_
        elif sent.sentence_type is Sentence_Type.GT:
            logic = self.ir.sgt_
        else:  # sent.sentence_type is Sentence_Type.GEQ
            logic = self.ir.sge_
        lvar: dict = sent.info['lvar']
        if lvar.get('dimension') is not None:
            lvar = self.__proc_array(lvar)
        rvar: dict = sent.info['rvar']
        if rvar.get('dimension') is not None:
            rvar = self.__proc_array(rvar)
        avar: dict = sent.info['avar']
        if avar.get('dimension') is not None:
            avar = self.__proc_array(avar)
        l_type = self.ir.set_type(lvar['size'])
        r_type = self.ir.set_type(rvar['size'])
        l_val = lvar.get('reg') if lvar.get('reg') else lvar.get('value')
        r_val = rvar.get('reg') if rvar.get('reg') else rvar.get('value')
        ir = logic(l_type, l_val, r_val)
        ir = self.ir.set_res(avar['reg'], ir)
        self.res.append(self.ir.set_tab(ir))

    def __g_J(self, sent: Sentence) -> None:
        if sent.sentence_type is Sentence_Type.JMP:
            ir = self.ir.br_(dest=sent.info['label'])
            self.used_label.add(sent.info['label'])
        else:  # sent.sentence_type is Sentence_Type.IF_JMP
            val = sent.info['var'].get('reg') if sent.info['var'].get('reg') else sent.info['var'].get('value')
            ir = self.ir.br_(val, sent.info['tl'], sent.info['fl'])
            self.used_label.add(sent.info['tl'])
            self.used_label.add(sent.info['fl'])
        self.res.append(self.ir.set_tab(ir))

    def __g_F(self, sent: Sentence) -> None:
        if sent.sentence_type is Sentence_Type.DEFINE_FUNC:
            paras = []
            f_type = "i32" if sent.info['type'] == 'int' else 'void'
            for para in sent.info['paras']:
                para = para.info
                if para.get('dimension', None):
                    v_type = self.ir.set_type(para['size'], para['define_dime'])
                else:
                    v_type = self.ir.set_type(para['size'])
                paras.append(T_V(v_type, para['reg']))
            ir = self.ir.set_func_(sent.value, f_type, paras)
            self.ir.tab_counter += 1
        else:  # sent.sentence_type is Sentence_Type.FUNC_END
            ir = "}"
            self.ir.tab_counter -= 1
        self.res.append(ir)

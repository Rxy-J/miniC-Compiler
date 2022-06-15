#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：miniCC 
@File ：optimizer.py
@Author ：OrangeJ
@Date ：2022/6/15 14:12 
'''

import re
import sys
import graphviz

from enum import Enum
from utils.analyzer import Sentence, Sentence_Type


class OptimizeType(Enum):
    BASE_BLOCK = 0
    CONTROL_GRAPH = 1
    O2 = 2


class BaseBlock:
    def __init__(self, block_id: int, block_label: str, block_content: list[Sentence] = None, block_to: list[str] = None):
        self.block_id = block_id
        self.block_label = block_label
        self.block_content = block_content if block_content else []
        self.block_to = set(block_to) if block_to else set([])

    def add_block_to(self, block_id: str):
        self.block_to.add(block_id)

    def add_block_content(self, block_content: Sentence):
        self.block_content.append(block_content)

    def __repr__(self):
        return f"block_label->{self.block_label}, \n" \
               f"block_content->{self.block_content}, \n" \
               f"block_to->{self.block_to}\n"


class Optimizer:
    def __init__(self, sentences: list[Sentence]):
        self.sentences = sentences
        self.graph = graphviz.Digraph()
        self.block_counter = 0
        self.base_blocks: list[BaseBlock] = []

    def get_base_block(self) -> list[BaseBlock]:
        curr = 0
        while curr < len(self.sentences):
            sent = self.sentences[curr]
            if sent.sentence_type in (Sentence_Type.DEFINE_GLOBAL_VAR,
                                      Sentence_Type.DEFINE_GLOBAL_ARRAY,
                                      Sentence_Type.DEFINE_FUNC,
                                      Sentence_Type.DECLARE_FUNC):
                curr += 1
                continue
            else:
                curr = self.__one_base_block(curr)
        return self.base_blocks

    def __one_base_block(self, pos: int) -> int:
        sent = self.sentences[pos]
        bb = BaseBlock(self.block_counter, sent.label)
        self.block_counter += 1
        while True:
            sent = self.sentences[pos]
            if sent.sentence_type is Sentence_Type.JMP:
                bb.add_block_content(sent)
                bb.add_block_to(sent.info['label'])
                break
            elif sent.sentence_type is Sentence_Type.IF_JMP:
                bb.add_block_content(sent)
                bb.add_block_to(sent.info['tl'])
                bb.add_block_to(sent.info['fl'])
                break
            elif sent.sentence_type is Sentence_Type.RETURN:
                bb.add_block_content(sent)
                pos += 1
                break
            else:
                bb.add_block_content(sent)
            pos += 1
        self.base_blocks.append(bb)
        return pos + 1

    def get_control_graph(self) -> str:
        self.get_base_block()
        for block in self.base_blocks:
            if block.block_label is None:
                block.block_label = f"KS{block.block_id}"
            self.graph.node(block.block_label)
            for to_label in block.block_to:
                self.graph.edge(block.block_label, to_label)
        return self.graph.source



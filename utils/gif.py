#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：gif.py
@Author ：OrangeJ
@Date ：2022/5/18 20:30
"""
import sys
import io
from typing import Union

try:
    import imageio
    from matplotlib import pyplot as plt
except ImportError as e:
    print(f"[ERROR] {e}")
    sys.exit(0)


class GifGenerator:

    @staticmethod
    def png2gif(frames: list, gif_name, duration=1.0):
        imageio.mimsave(gif_name, frames, 'GIF', duration=duration)

    @staticmethod
    def text2png(text: Union[str, list[str]],
                 height: int,
                 width: int,
                 fontsize: int = 10,
                 xpos: int = 0,
                 ypos: int = 1,
                 background_color: str = "#FFFFFF",
                 dpi: int = 100):
        """
        print text to a picture

        :param text: target plain text
        :param height: inch of height
        :param width: inch of width
        :param fontsize:
        :param xpos:
        :param ypos:
        :param dpi: the resolution of image, default 100
        :param background_color:
        :return:
        """
        plt.figure(figsize=(width, height), facecolor=background_color, dpi=dpi)
        plt.axis('off')
        out = io.BytesIO()
        box_style = dict(boxstyle="round, pad=0.5", fc="w", ec="k", lw=1)
        if isinstance(text, str):
            plt.text(xpos, ypos, text, fontsize=fontsize, ha="left", va="top", bbox=box_style)
        else:
            gap = 0.2
            xs = 0 + xpos
            for i in text:
                plt.text(xs, ypos, i, fontsize=10, ha="left", va="top", bbox=box_style)
                xs += gap
        plt.savefig(out)
        img = imageio.imread(out)
        plt.close()
        return img

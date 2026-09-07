#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组装《联结》全书成两种中间稿，供既有 skill 渲染成品；并可对渲染后的 HTML 做作者主页链接化。

模式
  --mode pdf   产出 build/for_pdf.md
               带 YAML frontmatter（含 copyright 授权声明，含作者 GitHub 主页可点链接）。
               由 md2book 渲染：封面 + 版权页 + 自动目录，每个 # 章自动另起一页。
  --mode html  产出 build/for_html.md
               正文各章标题逐级 +1，并前置「书名 # + 版权说明块（含作者主页 URL 纯文本）」。
               由 md-to-html 渲染：H1 书名作页眉、左侧目录从 ## 章起，版权块进正文。
  --linkify-html FILE
               把已渲染 HTML 版权块中的作者主页 URL 包成可点击 <a>（幂等），只执行此步。

说明
  - 跳过 src/01-目录.md（旧书名《代码的联结》且与自动目录重复）。
  - 围栏代码块内行首的 # 是伪代码注释，不作标题、不改写（逐行跟踪围栏开关）。
  - md_to_html 不解析 Markdown 链接/自动链接，故 HTML 先放纯文本 URL，渲染后 linkify。
  - md2book 的 copyright 以原样 HTML 嵌入版权页，PDF 用 <a>（属性用单引号，避开其简易 YAML 解析）。
  - 纯标准库，无第三方依赖。
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "build")
EXCLUDE = {"01-目录.md"}

TITLE = "联结"
SUBTITLE = "The Connection · 联结：代码的运转之道"
AUTHOR = "WorldHema"
AUTHOR_HOME = "https://github.com/worldhema"
VERSION = "1.0.0"
DATE = "2026-09-07"
DESCRIPTION = "一本写给所有人的代码科普书：从一个函数，到一群 AI，看懂软件世界的全部秘密。"

COPYRIGHT = (
    "本书《联结》(The Connection) 由 WorldHema 著，版权所有 © 2026 WorldHema，"
    "保留所有权利。个人非商业使用可自由阅读、下载、复制与分发，须保留作者署名与出处；"
    "商业使用（含出版发行、销售、企业内训与商用、营利性改编与衍生创作等）"
    "须事先取得作者书面授权。"
)
PDF_COPYRIGHT = COPYRIGHT + "<br>作者主页：<a href='%s'>%s</a>" % (AUTHOR_HOME, AUTHOR_HOME)

HTML_HEAD = """# {title}

> {subtitle}
> 作者：{author} · {date} · v{version}

**版权声明 · Copyright：** 本书由 {author} 著，© 2026 {author}，保留所有权利。
个人非商业使用可自由阅读、下载、复制与分发（须保留署名与出处）；
商业使用（出版发行、销售、企业内训与商用、营利性改编衍生等）须事先取得作者书面授权，详见仓库 `LICENSE`。
作者主页：{homepage}
"""


def src_files():
    files = sorted(glob.glob(os.path.join(SRC, "*.md")))
    return [f for f in files if os.path.basename(f) not in EXCLUDE]


def bump_headings(lines):
    """把非围栏内的标题行逐级 +1（每行行首多一个 #）。"""
    out = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(`{3,}|~{3,})", stripped):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence and re.match(r"^#{1,6}([ \t]|$)", line):
            out.append("#" + line)
        else:
            out.append(line)
    return out


def read_lines(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().split("\n")


def body_text(files, bump=False):
    blocks = []
    for f in files:
        lines = read_lines(f)
        if bump:
            lines = bump_headings(lines)
        # 去掉结尾空白行，块间以空行分隔
        text = "\n".join(lines).rstrip("\n")
        blocks.append(text)
    return "\n\n".join(blocks)


def frontmatter():
    def field(key, value):
        return '%s: "%s"' % (key, value.replace('"', '\\"'))

    lines = ["---"]
    for key, value in (
        ("title", TITLE),
        ("subtitle", SUBTITLE),
        ("author", AUTHOR),
        ("version", VERSION),
        ("date", DATE),
        ("description", DESCRIPTION),
        ("copyright", PDF_COPYRIGHT),
    ):
        lines.append(field(key, value))
    lines.append("---")
    return "\n".join(lines) + "\n"


def linkify_html(path):
    """把已渲染 HTML 版权块中的作者主页 URL 包成可点 <a>。幂等：已链接化则跳过。"""
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    if re.search(r"<a [^>]*href=['\"]%s['\"]" % re.escape(AUTHOR_HOME), html):
        print("already linkified, skip: %s" % path)
        return
    target = "作者主页：" + AUTHOR_HOME
    if target not in html:
        print("目标文本未找到: %s" % target)
        return
    html = html.replace(
        target,
        "<a href='%s'>%s</a>" % (AUTHOR_HOME, target),
        1,
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("linkified: %s" % path)


def main():
    ap = argparse.ArgumentParser(description="组装《联结》成书中间稿 / 链接化成品 HTML")
    ap.add_argument("--mode", choices=["pdf", "html"], help="产出模式")
    ap.add_argument("--linkify-html", metavar="FILE", help="链接化已渲染 HTML 的版权主页 URL（幂等）")
    ap.add_argument("-o", "--output", default=None, help="输出路径（默认 build/for_<mode>.md）")
    args = ap.parse_args()

    if args.linkify_html:
        linkify_html(args.linkify_html)
        return 0
    if not args.mode:
        ap.error("需要 --mode html|pdf 或 --linkify-html FILE")

    files = src_files()
    if args.mode == "pdf":
        content = frontmatter() + "\n" + body_text(files, bump=False)
    else:
        head = HTML_HEAD.format(
            title=TITLE, subtitle=SUBTITLE, author=AUTHOR, date=DATE, version=VERSION,
            homepage=AUTHOR_HOME,
        )
        content = head.rstrip("\n") + "\n\n" + body_text(files, bump=True)

    out_path = args.output or os.path.join(OUT, "for_%s.md" % args.mode)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    print("written: %s  (%d 文件, %d 字符)" % (out_path, len(files), len(content)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Lista os paragrafos (com estilo) e as linhas de tabela de um document.xml.

    PYTHONIOENCODING=utf-8 python dump.py pasta/word/document.xml
"""
import sys

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
body = etree.parse(sys.argv[1]).getroot().find(W + "body")
for i, e in enumerate(body):
    if e.tag == W + "tbl":
        for tr in e.findall(W + "tr"):
            print(i, "ROW:", " || ".join("".join(t.text or "" for t in tc.iter(W + "t"))
                                         for tc in tr.findall(W + "tc")))
        continue
    if e.tag != W + "p":
        continue
    st = e.find(f"{W}pPr/{W}pStyle")
    st = st.get(W + "val") if st is not None else ""
    t = "".join(x.text or "" for x in e.iter(W + "t"))
    print(i, st, "|", t)

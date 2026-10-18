"""Remonta o .docx a partir da pasta descompactada, usando o original como molde (inclui arquivos novos).

    python zipar2.py original.docx pasta saida.docx
"""
import os
import sys
import zipfile

orig, pasta, saida = sys.argv[1:4]
with zipfile.ZipFile(orig) as zi, zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as zo:
    vistos = set()
    for info in zi.infolist():
        p = f"{pasta}/{info.filename}"
        dados = open(p, "rb").read() if os.path.exists(p) else zi.read(info)
        zo.writestr(info, dados)
        vistos.add(info.filename)
    for raiz, _, arquivos in os.walk(pasta):
        for a in arquivos:
            cheio = os.path.join(raiz, a)
            nome = os.path.relpath(cheio, pasta).replace("\\", "/")
            if nome not in vistos:
                zo.write(cheio, nome)
                print("novo:", nome)

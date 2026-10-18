"""Edicao de document.xml (Word) com controle de alteracoes: troca de trecho, insercao e paragrafo novo.

Uso tipico (ver rev_*.py):
    d = Doc("pasta/word/document.xml")
    d.trocar("trecho que identifica o paragrafo", "velho", "novo")
    d.novo_paragrafo(d.achar("paragrafo de referencia"), "texto novo")
    d.salvar()
"""
import copy
import itertools

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
AUTOR = "Vitor Oliveira"
DATA = "2026-01-01T00:00:00Z"
_ids = itertools.count(880000)


def _marca(tag):
    e = etree.Element(W + tag)
    e.set(W + "id", str(next(_ids)))
    e.set(W + "author", AUTOR)
    e.set(W + "date", DATA)
    return e


class Doc:
    def __init__(self, caminho):
        self.caminho = caminho
        self.arv = etree.parse(caminho)
        self.body = self.arv.getroot().find(W + "body")

    def salvar(self):
        self.arv.write(self.caminho, xml_declaration=True, encoding="UTF-8", standalone=True)

    @staticmethod
    def texto(p):
        return "".join(t.text or "" for t in p.iter(W + "t"))

    def paragrafos(self):
        return list(self.body.iter(W + "p"))

    def achar(self, trecho, unico=True):
        achados = [p for p in self.paragrafos() if trecho in self.texto(p)]
        if unico:
            if len(achados) != 1:
                raise ValueError(f"{len(achados)} paragrafos contem: {trecho[:70]!r}")
            return achados[0]
        if not achados:
            raise ValueError(f"nenhum paragrafo contem: {trecho[:70]!r}")
        return achados

    # ------------------------------------------------------------ runs
    @staticmethod
    def _runs(p):
        """Runs com texto, na ordem, fora de w:del."""
        out = []
        for r in p.iter(W + "r"):
            if any(a.tag == W + "del" for a in r.iterancestors()):
                continue
            ts = r.findall(W + "t")
            if ts:
                out.append((r, "".join(t.text or "" for t in ts)))
        return out

    @staticmethod
    def _so_um_t(r):
        ts = r.findall(W + "t")
        tudo = "".join(t.text or "" for t in ts)
        for t in ts[1:]:
            r.remove(t)
        ts[0].text = tudo
        ts[0].set(XML_SPACE, "preserve")
        return ts[0]

    def _dividir(self, r, n):
        """Divide o run r no caractere n (r fica com o inicio; a copia, com o resto)."""
        t = self._so_um_t(r)
        tudo = t.text
        r2 = copy.deepcopy(r)
        t.text = tudo[:n]
        t2 = r2.find(W + "t")
        t2.text = tudo[n:]
        t2.set(XML_SPACE, "preserve")
        r.addnext(r2)
        return r2

    @staticmethod
    def _run_novo(texto, rpr_de=None):
        r = etree.Element(W + "r")
        if rpr_de is not None:
            rpr = rpr_de.find(W + "rPr")
            if rpr is not None:
                rpr = copy.deepcopy(rpr)
                for x in rpr.findall(W + "rPrChange"):
                    rpr.remove(x)
                r.append(rpr)
        t = etree.SubElement(r, W + "t")
        t.text = texto
        t.set(XML_SPACE, "preserve")
        return r

    @staticmethod
    def _deletar_run(r):
        for t in r.findall(W + "t"):
            t.tag = W + "delText"
        d = _marca("del")
        r.addprevious(d)
        d.append(r)
        return d

    def _cortar(self, p, ini, fim):
        """Garante limites de run em ini e fim; devolve os runs cobertos por [ini, fim)."""
        for corte in (ini, fim):
            pos = 0
            for r, t in self._runs(p):
                a, b = pos, pos + len(t)
                if a < corte < b:
                    self._dividir(r, corte - a)
                    break
                pos = b
        dentro, pos = [], 0
        for r, t in self._runs(p):
            a, b = pos, pos + len(t)
            if a >= ini and b <= fim and b > a:
                dentro.append(r)
            pos = b
        return dentro

    def trocar(self, p_ou_trecho, velho, novo):
        """Troca `velho` por `novo` no paragrafo, com marca de exclusao e de insercao."""
        p = self.achar(p_ou_trecho) if isinstance(p_ou_trecho, str) else p_ou_trecho
        cheio = "".join(t for _, t in self._runs(p))
        ini = cheio.find(velho)
        if ini < 0 or cheio.find(velho, ini + 1) >= 0:
            raise ValueError(f"trecho ausente ou repetido: {velho[:70]!r}")
        dentro = self._cortar(p, ini, ini + len(velho))
        modelo = dentro[0]
        ultimo = None
        for r in dentro:
            ultimo = self._deletar_run(r)
        if novo:
            ins = _marca("ins")
            ins.append(self._run_novo(novo, modelo))
            ultimo.addnext(ins)
        return p

    def inserir(self, p_ou_trecho, depois_de, texto):
        """Insere `texto` logo apos `depois_de` no paragrafo."""
        p = self.achar(p_ou_trecho) if isinstance(p_ou_trecho, str) else p_ou_trecho
        cheio = "".join(t for _, t in self._runs(p))
        ini = cheio.find(depois_de)
        if ini < 0 or cheio.find(depois_de, ini + 1) >= 0:
            raise ValueError(f"ancora ausente ou repetida: {depois_de[:70]!r}")
        fim = ini + len(depois_de)
        dentro = self._cortar(p, ini, fim)
        r = dentro[-1]
        ins = _marca("ins")
        ins.append(self._run_novo(texto, r))
        alvo = r.getparent() if r.getparent().tag == W + "ins" else r
        alvo.addnext(ins)
        return p

    # ------------------------------------------------------------ paragrafos
    def novo_paragrafo(self, ref, texto, depois=True, modelo=None):
        """Paragrafo novo (marcado) com a formatacao de `modelo` (ou de ref)."""
        ref = self.achar(ref) if isinstance(ref, str) else ref
        mod = modelo if modelo is not None else ref
        mod = self.achar(mod) if isinstance(mod, str) else mod
        p = etree.Element(W + "p")
        ppr = mod.find(W + "pPr")
        ppr = copy.deepcopy(ppr) if ppr is not None else etree.Element(W + "pPr")
        for velho in ppr.findall(W + "rPr") + ppr.findall(W + "sectPr"):
            ppr.remove(velho)
        rpr = etree.SubElement(ppr, W + "rPr")
        rpr.append(_marca("ins"))
        p.append(ppr)
        run_mod = next((r for r in mod.iter(W + "r") if r.find(W + "t") is not None), None)
        ins = _marca("ins")
        ins.append(self._run_novo(texto, run_mod))
        p.append(ins)
        (ref.addnext if depois else ref.addprevious)(p)
        return p

    def paragrafos_apos(self, ref, textos, modelo=None):
        ultimo = ref
        for tx in textos:
            ultimo = self.novo_paragrafo(ultimo, tx, modelo=modelo if modelo is not None else ref)
        return ultimo

    def substituir_paragrafo(self, trecho, novo):
        p = self.achar(trecho)
        self.trocar(p, self.texto(p), novo)
        return p

    # ------------------------------------------------------------ tabelas
    def tabela_com(self, trecho):
        tbls = [t for t in self.body.iter(W + "tbl") if trecho in "".join(x.text or "" for x in t.iter(W + "t"))]
        if len(tbls) != 1:
            raise ValueError(f"{len(tbls)} tabelas com {trecho!r}")
        return tbls[0]

    def linha_com(self, tbl, trecho):
        ls = [tr for tr in tbl.findall(W + "tr") if trecho in "".join(x.text or "" for x in tr.iter(W + "t"))]
        if len(ls) != 1:
            raise ValueError(f"{len(ls)} linhas com {trecho!r}")
        return ls[0]

    def nova_linha(self, tbl, modelo_trecho, celulas, depois_trecho=None):
        """Linha nova (marcada como insercao), com a formatacao da linha modelo."""
        mod = self.linha_com(tbl, modelo_trecho)
        ref = self.linha_com(tbl, depois_trecho) if depois_trecho else mod
        tr = copy.deepcopy(mod)
        trpr = tr.find(W + "trPr")
        if trpr is None:
            trpr = etree.Element(W + "trPr")
            tr.insert(0 if tr.find(W + "tblPrEx") is None else 1, trpr)
        trpr.append(_marca("ins"))
        for tc_, texto in zip(tr.findall(W + "tc"), celulas):
            ps = tc_.findall(W + "p")
            for extra in ps[1:]:
                tc_.remove(extra)
            p = ps[0]
            run_mod = copy.deepcopy(next((r for r in p.iter(W + "r") if r.find(W + "t") is not None), None))
            for filho in list(p):
                if filho.tag != W + "pPr":
                    p.remove(filho)
            ppr = p.find(W + "pPr")
            if ppr is None:
                ppr = etree.Element(W + "pPr")
                p.insert(0, ppr)
            for velho in ppr.findall(W + "rPr"):
                ppr.remove(velho)
            etree.SubElement(ppr, W + "rPr").append(_marca("ins"))
            ins = _marca("ins")
            ins.append(self._run_novo(texto, run_mod))
            p.append(ins)
        ref.addnext(tr)
        return tr

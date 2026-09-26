"""Gera o .docx da versao final do TCC a partir de TCC_final.md, no template oficial.

O template da USP/Esalq nao define os estilos nomeados que o pandoc usa
(Heading 1, Body Text, Table, ...); sem eles, o Word sai com titulos sem
negrito e tabelas sem grade. Este script:

1. copia o template e injeta em word/styles.xml os estilos que faltam, todos
   herdando de Normal (Arial 11, justificado, como no template);
2. prepara uma copia do Markdown em que as referencias e as legendas recebem
   estilos proprios (sem recuo, espacamento simples), via custom-style;
3. roda o pandoc com o template preparado como reference-doc;
4. se o LibreOffice estiver instalado, converte para PDF e conta as paginas.

Uso:
    .venv/bin/python docs/tcc/final/gerar_docx.py [--pdf]
"""

import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
FONTE = Path(__file__).with_name("TCC_final.md")
SAIDA = Path(__file__).with_name("TCC_final.docx")
TEMPLATE = RAIZ / "docs-tcc" / "Template TCC_PT (251, 252).docx"
CURSO = "Engenharia de Software"
ANO_DEFESA = "2026"

# Estilos que o pandoc procura pelo nome. Todos herdam de Normal; os titulos
# ficam em negrito e alinhados a esquerda (manual, itens 16.x); as celulas de
# tabela, referencias e legendas ficam sem recuo e com espacamento simples.
# A linha dos autores e centralizada e os enderecos (titulacao e e-mail) ficam
# em Arial 9, como pede a folha de rosto do manual.
ESTILOS = """
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/><w:jc w:val="left"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:bCs/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/><w:jc w:val="left"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:bCs/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="100"/><w:jc w:val="left"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:bCs/><w:i/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/><w:ind w:firstLine="709"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="FirstParagraph"><w:name w:val="First Paragraph"/><w:basedOn w:val="BodyText"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Compact"><w:name w:val="Compact"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Referencia"><w:name w:val="Referencia"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="0" w:after="200" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Legenda"><w:name w:val="Legenda"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="80" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="FonteTabela"><w:name w:val="FonteTabela"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="80" w:after="240" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/><w:basedOn w:val="Legenda"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="ImageCaption"><w:name w:val="Image Caption"/><w:basedOn w:val="Legenda"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="TableCaption"><w:name w:val="Table Caption"/><w:basedOn w:val="Legenda"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Figure"><w:name w:val="Figure"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="CaptionedFigure"><w:name w:val="Captioned Figure"/><w:basedOn w:val="Figure"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:spacing w:after="240"/><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr><w:rPr><w:b/><w:bCs/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Author"><w:name w:val="Author"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Date"><w:name w:val="Date"/><w:basedOn w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Abstract"><w:name w:val="Abstract"/><w:basedOn w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="BlockText"><w:name w:val="Block Text"/><w:basedOn w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="FootnoteText"><w:name w:val="footnote text"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:firstLine="0"/></w:pPr><w:rPr><w:sz w:val="18"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="SourceCode"><w:name w:val="Source Code"/><w:basedOn w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Titulo"><w:name w:val="Titulo"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="0" w:after="240" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr><w:rPr><w:b/><w:bCs/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Autores"><w:name w:val="Autores"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="120" w:after="120" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Endereco"><w:name w:val="Endereco"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Rotulo"><w:name w:val="Rotulo"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="SemRecuo"><w:name w:val="SemRecuo"/><w:basedOn w:val="BodyText"/><w:qFormat/><w:pPr><w:ind w:firstLine="0"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="ResumoTexto"><w:name w:val="ResumoTexto"/><w:basedOn w:val="BodyText"/><w:qFormat/><w:pPr><w:spacing w:line="240" w:lineRule="auto"/></w:pPr></w:style>
<w:style w:type="character" w:styleId="VerbatimChar"><w:name w:val="Verbatim Char"/><w:qFormat/></w:style>
<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/><w:qFormat/><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>
<w:style w:type="table" w:styleId="Table"><w:name w:val="Table"/><w:basedOn w:val="Tabelanormal"/><w:qFormat/><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tblBorders><w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="80" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>
"""


def preparar_referencia(destino):
    """Copia o template e injeta os estilos que faltam em word/styles.xml."""
    with zipfile.ZipFile(TEMPLATE) as z_in, zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z_out:
        for item in z_in.infolist():
            dados = z_in.read(item.filename)
            if item.filename.startswith("word/header") and b"Nome do curso" in dados:
                dados = dados.decode("utf-8").replace(
                    " _________ (Nome do curso) \u2013 ____ (ano da defesa)", f" {CURSO} \u2013 {ANO_DEFESA}"
                ).encode("utf-8")
            if item.filename == "word/styles.xml":
                xml = dados.decode("utf-8")
                existentes = set(re.findall(r'w:styleId="([^"]+)"', xml))
                novos = [e for e in ESTILOS.strip().splitlines()
                         if re.search(r'w:styleId="([^"]+)"', e).group(1) not in existentes]
                xml = xml.replace("</w:styles>", "".join(novos) + "</w:styles>")
                dados = xml.encode("utf-8")
            z_out.writestr(item, dados)


def preparar_markdown(destino):
    """Aplica estilos proprios a referencias, legendas e fontes, sem tocar na fonte."""
    texto = FONTE.read_text(encoding="utf-8")
    corpo, sep, refs = texto.partition("\n# Referências\n")
    apend = ""
    if "\n# Apêndice A" in refs:
        refs, apend = refs.split("\n# Apêndice A", 1)
        apend = "\n# Apêndice A" + apend
    linhas = []
    for l in refs.strip("\n").split("\n\n"):
        if l.strip():
            # o manual pede o endereco entre < e >; escapados, o pandoc os mantem
            ref = re.sub(r"<(https?://[^>]+)>", r"\\<\1\\>", l.strip())
            linhas.append(f'::: {{custom-style="Referencia"}}\n{ref}\n:::')
    refs_fmt = "\n\n".join(linhas)

    def larguras(bloco):
        """Reescreve a linha separadora de cada tabela com tracos proporcionais
        ao conteudo das colunas, que e como o pandoc define as larguras."""
        linhas = bloco.split("\n")
        i = 0
        while i < len(linhas):
            if linhas[i].startswith("|") and i + 1 < len(linhas) and re.match(r"^\|[-:| ]+\|$", linhas[i + 1]):
                j = i
                while j < len(linhas) and linhas[j].startswith("|"):
                    j += 1
                celulas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in linhas[i:j] if not re.match(r"^\|[-:| ]+\|$", l)]
                ncol = len(celulas[0])
                maximos = [max(len(r[c]) if c < len(r) else 0 for r in celulas) for c in range(ncol)]
                pesos = [min(max(m, 16), 50) for m in maximos]
                total = sum(pesos) or 1
                tracos = [max(3, round(60 * w / total)) for w in pesos]
                linhas[i + 1] = "|" + "|".join("-" * t for t in tracos) + "|"
                i = j
            else:
                i += 1
        return "\n".join(linhas)

    titulo = corpo.lstrip("\n").split("\n", 1)[0].removeprefix("# ").strip()
    titulo_visto = [False]

    def estilizar(bloco):
        out = []
        apos_resumo = False
        for par in bloco.split("\n\n"):
            t = par.strip()
            if apos_resumo and t:
                # texto do Resumo: paragrafo unico em espacamento simples (manual, item 6)
                out.append(f'::: {{custom-style="ResumoTexto"}}\n{t}\n:::')
                apos_resumo = False
                continue
            if t == "**Resumo**":
                apos_resumo = True
                # o template repete o titulo, centralizado e em negrito, no alto da
                # pagina 2, logo antes do Resumo (apontamento do formatador da USP)
                out.append("```{=openxml}\n<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>\n```")
                out.append(f'::: {{custom-style="Titulo"}}\n{titulo}\n:::')
            if t.startswith("# ") and not titulo_visto[0]:
                # titulo da folha de rosto: centralizado e em negrito, nao e secao
                titulo_visto[0] = True
                out.append(f'::: {{custom-style="Titulo"}}\n{titulo}\n:::')
            elif re.match(r"^\S.*¹\*; .*²$", t):
                # linha dos autores: centralizada (manual, folha de rosto)
                out.append(f'::: {{custom-style="Autores"}}\n{t}\n:::')
            elif re.match(r"^(¹\*|²) ", t):
                # enderecos dos autores: Arial 9, espacamento simples, a esquerda
                out.append(f'::: {{custom-style="Endereco"}}\n{t}\n:::')
            elif t == "**Resumo**":
                # rotulo do Resumo: negrito, a esquerda, sem recuo (manual, item 6)
                out.append(f'::: {{custom-style="Rotulo"}}\n{t}\n:::')
            elif t.startswith("**Palavras-chave:**"):
                out.append(f'::: {{custom-style="SemRecuo"}}\n{t}\n:::')
            elif re.match(r"^(Tabela|Figura) \d+\. ", t):
                out.append(f'::: {{custom-style="Legenda"}}\n{t}\n:::')
            elif t.startswith("Fonte: "):
                out.append(f'::: {{custom-style="FonteTabela"}}\n{t}\n:::')
            else:
                out.append(par)
        return "\n\n".join(out)

    destino.write_text(estilizar(larguras(corpo)) + sep + refs_fmt + "\n" + estilizar(larguras(apend)), encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ref = tmp / "referencia_estilos.docx"
        md = tmp / "TCC_final_preparado.md"
        preparar_referencia(ref)
        preparar_markdown(md)
        subprocess.run(
            ["pandoc", str(md), f"--resource-path={FONTE.parent}", f"--reference-doc={ref}",
             "-o", str(SAIDA)],
            check=True,
        )
        print(f"gerado: {SAIDA}")
        if "--pdf" in sys.argv:
            soffice = shutil.which("soffice") or "/Applications/LibreOffice.app/Contents/MacOS/soffice"
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(SAIDA)],
                           check=True, capture_output=True)
            pdf = tmp / (SAIDA.stem + ".pdf")
            texto = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
            print(f"paginas (PDF via LibreOffice): {texto.count(chr(12))}")
            shutil.copy(pdf, SAIDA.with_suffix(".pdf"))


if __name__ == "__main__":
    main()

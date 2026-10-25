"""Génère rapport.pdf à partir de rapport.md (Edge ou Chrome en mode headless).

Usage, depuis le dossier du dépôt :  python generer-pdf.py
Aucune dépendance : petit convertisseur Markdown limité à ce qu'utilise le rapport
(titres, paragraphes, listes, tableaux, citations, gras, code, liens).
"""
import html
import os
import re
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(RACINE, 'rapport.md')
SORTIE = os.path.join(RACINE, 'rapport.pdf')
NAVIGATEURS = [
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
]

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
* { box-sizing: border-box; }
body { font: 10pt/1.45 "Segoe UI", Roboto, Arial, sans-serif; color: #1d2130; margin: 0; }
h1 { font-size: 20pt; margin: 0 0 6pt; color: #3b2a99; }
h2 { font-size: 13.5pt; margin: 18pt 0 6pt; color: #3b2a99; border-bottom: 1.5pt solid #d9d3ff; padding-bottom: 3pt; break-after: avoid; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; break-after: avoid; }
p { margin: 0 0 6pt; }
ul { margin: 0 0 6pt; padding-left: 16pt; }
li { margin: 0 0 2pt; }
a { color: #3b2a99; text-decoration: none; }
code { font: 8.6pt Consolas, monospace; background: #f1effa; padding: 0 2pt; border-radius: 2pt; }
strong { color: #111; }
blockquote { margin: 0 0 8pt; padding: 5pt 9pt; border-left: 3pt solid #f0b429; background: #fff8e6; }
hr { border: 0; border-top: 1pt solid #e2e2ea; margin: 12pt 0; }
table { width: 100%; border-collapse: collapse; margin: 4pt 0 10pt; font-size: 8.4pt; line-height: 1.35; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th { background: #3b2a99; color: #fff; text-align: left; font-weight: 600; }
th, td { border: 0.6pt solid #cfcbe6; padding: 3.5pt 5pt; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f7f6fc; }
.todo { background: #fff1b8; color: #7a5a00; border-radius: 2pt; padding: 0 2pt; font-family: inherit; }
.entete p { margin: 0 0 2pt; }
"""


def inline(texte):
    """Gras, italique, code, liens <...>, en échappant le HTML."""
    codes = []

    def mettre_de_cote(m):
        contenu = m.group(1)
        classe = ' class="todo"' if 'à compléter' in contenu else ''
        codes.append('<code%s>%s</code>' % (classe, html.escape(contenu)))
        return '@@CODE%d@@' % (len(codes) - 1)

    t = re.sub(r'`([^`]+)`', mettre_de_cote, texte)
    t = html.escape(t, quote=False)
    t = re.sub(r'&lt;(https?://[^&\s]+)&gt;', r'<a href="\1">\1</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*([^*\n]+?)\*(?![\w*])', r'<em>\1</em>', t)
    return re.sub(r'@@CODE(\d+)@@', lambda m: codes[int(m.group(1))], t)


def cellules(ligne):
    return [c.strip() for c in ligne.strip().strip('|').split('|')]


def convertir(md):
    lignes = md.replace('\r\n', '\n').split('\n')
    out, i, premier_titre = [], 0, True
    while i < len(lignes):
        l = lignes[i]
        if not l.strip():
            i += 1
        elif l.startswith('#'):
            niveau = len(l) - len(l.lstrip('#'))
            out.append('<h%d>%s</h%d>' % (niveau, inline(l[niveau:].strip()), niveau))
            if premier_titre and niveau == 1:
                premier_titre = False
                bloc = []
                i += 1
                while i < len(lignes) and not lignes[i].strip():
                    i += 1
                while i < len(lignes) and lignes[i].strip():
                    bloc.append('<p>%s</p>' % inline(lignes[i].strip()))
                    i += 1
                out.append('<div class="entete">%s</div>' % ''.join(bloc))
                continue
            i += 1
        elif l.strip() == '---':
            out.append('<hr>')
            i += 1
        elif l.startswith('|'):
            tableau = []
            while i < len(lignes) and lignes[i].startswith('|'):
                tableau.append(lignes[i])
                i += 1
            entetes = cellules(tableau[0])
            corps = [cellules(t) for t in tableau[2:]]
            out.append('<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (
                ''.join('<th>%s</th>' % inline(c) for c in entetes),
                ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r) for r in corps)))
        elif l.startswith('> '):
            bloc = []
            while i < len(lignes) and lignes[i].startswith('>'):
                bloc.append(lignes[i][1:].strip())
                i += 1
            out.append('<blockquote>%s</blockquote>' % inline(' '.join(bloc)))
        elif l.startswith('- '):
            items = []
            while i < len(lignes) and lignes[i].startswith('- '):
                items.append('<li>%s</li>' % inline(lignes[i][2:].strip()))
                i += 1
            out.append('<ul>%s</ul>' % ''.join(items))
        else:
            bloc = []
            while i < len(lignes) and lignes[i].strip() and not re.match(r'(#|\||- |> |---$)', lignes[i]):
                bloc.append(lignes[i].strip())
                i += 1
            out.append('<p>%s</p>' % inline(' '.join(bloc)))
    return '\n'.join(out)


def main():
    md = open(SOURCE, encoding='utf-8').read()
    page = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            '<title>Rapport d\'optimisation — TP R3.14</title><style>%s</style></head>'
            '<body>%s</body></html>') % (CSS, convertir(md))
    navigateur = next((n for n in NAVIGATEURS if os.path.exists(n)), None)
    if not navigateur:
        sys.exit('Edge ou Chrome introuvable.')
    with tempfile.TemporaryDirectory() as tmp:
        fichier = os.path.join(tmp, 'rapport.html')
        open(fichier, 'w', encoding='utf-8').write(page)
        subprocess.run([navigateur, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        '--user-data-dir=' + os.path.join(tmp, 'profil'),
                        '--print-to-pdf=' + SORTIE, 'file:///' + fichier.replace('\\', '/')],
                       check=True, capture_output=True, timeout=120)
    print('PDF créé :', SORTIE, '(%d Ko)' % (os.path.getsize(SORTIE) // 1024))


if __name__ == '__main__':
    main()

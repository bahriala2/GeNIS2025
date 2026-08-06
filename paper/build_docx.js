/*
 * build_docx.js — genere un document Word NATIF (docx-js) a partir de content.json.
 * Aucune conversion pandoc/LaTeX : styles, tableaux et figures sont construits
 * directement en OOXML. Le .docx produit est destine a devenir la source editable.
 *
 *   node build_docx.js            -> GeNIS_benchmark_article.docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, PageBreak,
  Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType,
  HeadingLevel, BorderStyle, VerticalAlign, TabStopType,
  Header, Footer, PageNumber, LevelFormat, convertInchesToTwip,
} = require("docx");

const ROOT = __dirname;
const DOC = JSON.parse(fs.readFileSync(path.join(ROOT, "content.json"), "utf8"));

/* ------------------------------------------------------------------ mise en page */
const PAGE_W = 11906, PAGE_H = 16838;          // A4 en DXA
const MARGIN = 1134;                            // 2 cm
const CONTENT_W = PAGE_W - 2 * MARGIN;          // 9638 DXA
const CONTENT_PX = Math.round((CONTENT_W / 1440) * 96);

const BODY_FONT = "Times New Roman";
const SANS = "Calibri";
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const RULE = (sz) => ({ style: BorderStyle.SINGLE, size: sz, color: "000000" });

/* ------------------------------------------------------------------ runs */
function toRuns(runs, opts = {}) {
  const { size = 22, font = BODY_FONT, bold = false, italics = false, color } = opts;
  if (!runs || !runs.length) return [new TextRun({ text: "", size, font })];
  return runs.map((r) => new TextRun({
    text: r.t,
    bold: bold || !!r.b,
    italics: italics || !!r.i,
    subScript: !!r.sub,
    superScript: !!r.sup,
    font: r.code ? "Consolas" : font,
    size: r.code ? size - 2 : size,
    color: r.warn ? "C00000" : color,     // placeholders a completer : en rouge
  }));
}

const para = (runs, opts = {}) => new Paragraph({
  children: [
    ...(opts.lead ? [new TextRun({ text: opts.lead + ". ", bold: true, size: opts.size ?? 22, font: BODY_FONT })] : []),
    ...toRuns(runs, opts),
  ],
  alignment: opts.alignment ?? AlignmentType.JUSTIFIED,
  spacing: { after: opts.after ?? 120, line: opts.line ?? 276 },
  indent: opts.indent,
  keepNext: opts.keepNext,
  border: opts.border,
});

/* ------------------------------------------------------------------ titres */
let n1 = 0, n2 = 0;
function heading(item, level) {
  let label;
  if (level === 1) { n1 += 1; n2 = 0; label = `${n1}. `; }
  else { n2 += 1; label = `${n1}.${n2} `; }
  const txt = item.runs.map((r) => r.t).join("");
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: level === 1 ? 320 : 240, after: 120 },
    keepNext: true,
    children: [new TextRun({
      text: label + txt,
      bold: true,
      size: level === 1 ? 28 : 24,
      font: SANS,
      color: "1F3864",
    })],
  });
}

/* ------------------------------------------------------------------ figures */
function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), buf: b };
}

function figure(item) {
  const file = path.join(ROOT, item.src);
  const { w, h, buf } = pngSize(file);
  const targetW = Math.round(CONTENT_PX * Math.min(item.width || 1, 1));
  const targetH = Math.round(targetW * (h / w));
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 80 },
      keepNext: true,
      children: [new ImageRun({ type: "png", data: buf,
        transformation: { width: targetW, height: targetH } })],
    }),
    new Paragraph({
      alignment: AlignmentType.JUSTIFIED,
      spacing: { after: 240 },
      children: [
        new TextRun({ text: `Figure ${item.num}. `, bold: true, size: 18, font: SANS }),
        ...toRuns(item.caption, { size: 18, font: SANS }),
      ],
    }),
  ];
}

/* ------------------------------------------------------------------ tableaux */
const CELL_PAD = 160;              // marges gauche+droite d'une cellule, en DXA

/* Largeurs de colonnes : chaque colonne recoit au minimum de quoi afficher son plus
   long mot sans cesure, puis le reste est reparti au prorata du besoin restant.
   Sans ce plancher, un en-tete comme « repeated » se coupe en « repeat / ed ». */
function colWidths(item, fs) {
  const n = item.align.length;
  const chW = (bold) => (bold ? 6.9 : 5.9) * fs;       // ~ largeur moyenne d'un caractere (avec marge)
  const minW = new Array(n).fill(0), prefW = new Array(n).fill(0);
  const scan = (rows, bold) => {
    for (const row of rows) {
      let c = 0;
      for (const cell of row) {
        const span = cell.span || 1;
        const txt = cell.runs.map((r) => r.t).join("");
        if (span === 1) {
          const longest = Math.max(0, ...txt.split(/\s+/).map((w) => w.length));
          minW[c] = Math.max(minW[c], longest * chW(bold) + CELL_PAD);
          prefW[c] = Math.max(prefW[c], txt.length * chW(bold) + CELL_PAD);
        }
        c += span;
      }
    }
  };
  scan(item.head, true);
  scan(item.body, false);
  for (let i = 0; i < n; i++) prefW[i] = Math.min(prefW[i], 2600);

  let out = minW.slice();
  let free = CONTENT_W - out.reduce((a, b) => a + b, 0);
  if (free < 0) return null;                            // ne tient pas : police plus petite
  // la colonne d'intitules profite le plus de la largeur : on lui donne priorite
  const need = prefW.map((p, i) => Math.max(0, p - minW[i]) * (i === 0 ? 3 : 1));
  const tot = need.reduce((a, b) => a + b, 0);
  if (tot > 0) {
    const share = Math.min(1, free / tot);
    out = out.map((w, i) => w + Math.min(need[i] * share, prefW[i] - minW[i]));
    free = CONTENT_W - out.reduce((a, b) => a + b, 0);
  }
  out = out.map((w) => w + free / n);                   // etaler le reliquat
  out = out.map(Math.floor);
  out[0] += CONTENT_W - out.reduce((a, b) => a + b, 0); // ajustement exact
  return out;
}

function table(item) {
  let fs_ = 18, widths = null;
  while (fs_ >= 11 && !(widths = colWidths(item, fs_))) fs_ -= 1;   // reduire jusqu'a ce que ca tienne
  if (!widths) { fs_ = 11; widths = new Array(item.align.length).fill(Math.floor(CONTENT_W / item.align.length)); }
  const nHead = item.head.length;
  const alignOf = (i) => item.align[i] === "left" ? AlignmentType.LEFT
    : item.align[i] === "right" ? AlignmentType.RIGHT : AlignmentType.CENTER;

  const mkRow = (row, kind, isLast) => {
    let c = 0;
    const cells = row.map((cell) => {
      const span = cell.span || 1;
      let w = 0;
      for (let k = 0; k < span; k++) w += widths[c + k];
      const first = c;
      c += span;
      return new TableCell({
        width: { size: w, type: WidthType.DXA },
        columnSpan: span,
        verticalAlign: VerticalAlign.CENTER,
        shading: kind === "head"
          ? { type: ShadingType.CLEAR, fill: "EDF0F5", color: "auto" }
          : undefined,
        margins: { top: 40, bottom: 40, left: 70, right: 70 },
        borders: {
          top: kind === "head" && row === item.head[0] ? RULE(12) : NONE,
          // filet sous les en-tetes groupes (equivalent du \cmidrule de booktabs)
          bottom: (kind === "head" && (isLast || span > 1)) || (kind === "body" && isLast)
            ? RULE(kind === "head" ? 6 : 12) : NONE,
          left: NONE, right: NONE,
        },
        children: [new Paragraph({
          alignment: span > 1 ? AlignmentType.CENTER : alignOf(first),
          spacing: { before: 20, after: 20, line: 240 },
          children: toRuns(cell.runs, { size: fs_, font: SANS, bold: kind === "head" }),
        })],
      });
    });
    return new TableRow({ children: cells, tableHeader: kind === "head" });
  };

  const rows = [
    ...item.head.map((r, i) => mkRow(r, "head", i === nHead - 1)),
    ...item.body.map((r, i) => mkRow(r, "body", i === item.body.length - 1)),
  ];

  return [
    new Paragraph({
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 240, after: 100 },
      keepNext: true,
      children: [
        new TextRun({ text: `Table ${item.num}. `, bold: true, size: 18, font: SANS }),
        ...toRuns(item.caption, { size: 18, font: SANS }),
      ],
    }),
    new Table({
      columnWidths: widths,
      width: { size: CONTENT_W, type: WidthType.DXA },
      borders: {
        top: NONE, bottom: NONE, left: NONE, right: NONE,
        insideHorizontal: NONE, insideVertical: NONE,
      },
      rows,
    }),
    new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: "", size: 4 })] }),
  ];
}

/* ------------------------------------------------------------------ page de titre */
const title = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({ text: DOC.title, bold: true, size: 34, font: SANS, color: "1F3864" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [new TextRun({ text: DOC.authors.join(", "), size: 24, font: BODY_FONT })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 320 },
    children: [new TextRun({
      text: "[A COMPLETER : affiliation 1 (Ala Bahri, Farah Jemili) · affiliation 2 (Mohamed Mosbah)]",
      size: 20, italics: true, bold: true, font: BODY_FONT, color: "C00000",
    })],
  }),
  new Paragraph({
    spacing: { after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "1F3864" } },
    children: [new TextRun({ text: "Abstract", bold: true, size: 24, font: SANS, color: "1F3864" })],
  }),
  ...DOC.abstract.map ? [] : [],
];
title.push(para(DOC.abstract, { size: 21, after: 200 }));
title.push(new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 320 },
  children: [
    new TextRun({ text: "Keywords: ", bold: true, size: 21, font: BODY_FONT }),
    new TextRun({ text: DOC.keywords, size: 21, font: BODY_FONT, italics: true }),
  ],
}));

/* ------------------------------------------------------------------ corps */
const body = [];
for (const item of DOC.items) {
  if (item.type === "h1") body.push(heading(item, 1));
  else if (item.type === "h2") body.push(heading(item, 2));
  else if (item.type === "p") body.push(para(item.runs, { lead: item.lead }));
  else if (item.type === "li") body.push(new Paragraph({
    children: toRuns(item.runs),
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 100, line: 264 },
    numbering: { reference: item.ord ? "contrib" : "bullets", level: 0 },
  }));
  else if (item.type === "math") body.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 140, after: 180 },
    children: toRuns(item.runs, { italics: true }),
  }));
  else if (item.type === "figure") body.push(...figure(item));
  else if (item.type === "table") body.push(...table(item));
}

/* ------------------------------------------------------------------ references */
const refs = [
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 0, after: 160 },
    children: [new TextRun({ text: "References", bold: true, size: 28, font: SANS, color: "1F3864" })],
  }),
  ...DOC.refs.map((r, i) => new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 80, line: 240 },
    indent: { left: 480, hanging: 480 },
    children: [
      new TextRun({ text: `[${i + 1}] `, size: 19, font: BODY_FONT }),
      new TextRun({ text: r, size: 19, font: BODY_FONT }),
    ],
  })),
];

/* ------------------------------------------------------------------ document */
const doc = new Document({
  creator: DOC.authors.join(", "),
  title: DOC.title,
  description: "Article 1 — benchmark audité du corpus GeNIS 2025",
  numbering: {
    config: [
      { reference: "contrib", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.START,
        style: { paragraph: { indent: { left: 600, hanging: 320 } } } }] },
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.START,
        style: { paragraph: { indent: { left: 600, hanging: 320 } } } }] },
    ],
  },
  styles: {
    default: { document: { run: { font: BODY_FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true, run: { size: 28, bold: true, font: SANS, color: "1F3864" },
        paragraph: { spacing: { before: 320, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true, run: { size: 24, bold: true, font: SANS, color: "1F3864" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
      },
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" } },
        children: [new TextRun({
          text: "A Leakage-Audited Benchmark on the GeNIS 2025 Corpus",
          size: 16, font: SANS, color: "808080", italics: true })],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, font: SANS })],
      })] }),
    },
    children: [...title, ...body, ...refs],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "GeNIS_benchmark_article.docx");
  fs.writeFileSync(out, buf);
  console.log(`${path.basename(out)} : ${(buf.length / 1024 / 1024).toFixed(2)} Mo | ` +
    `${DOC.items.length} blocs, ${DOC.refs.length} references`);
});

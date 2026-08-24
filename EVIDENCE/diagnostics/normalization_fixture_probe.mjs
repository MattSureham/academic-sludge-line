#!/usr/bin/env node

/**
 * Evidence-only normalization probe.
 *
 * This script generates a temporary academic fixture corpus, runs the current
 * bundled Smart Loader and the current Python adapter without changing either,
 * and writes raw/curated observations beneath a caller-selected temporary
 * directory. It is diagnostic support, not a product contract or test suite.
 *
 * Usage:
 *   node EVIDENCE/diagnostics/normalization_fixture_probe.mjs [output-directory]
 */

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createWriteStream, promises as fs } from "node:fs";
import { once } from "node:events";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

import { loadPath } from "../../asl/_vendor/smart-loader/dist/index.js";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDir, "../..");
const loaderPackage = path.join(repositoryRoot, "asl/_vendor/smart-loader/package.json");
const requireFromLoader = createRequire(loaderPackage);
const PDFDocument = requireFromLoader("pdfkit");

const requestedOutputRoot = process.argv[2]
  ? path.resolve(process.argv[2])
  : await fs.mkdtemp(path.join(os.tmpdir(), "asl-normalization-probe-"));
await fs.mkdir(requestedOutputRoot, { recursive: true });
// macOS exposes /tmp through a symlink; canonicalize it because the installed
// Tesseract/Leptonica build does not open image paths through that alias.
const outputRoot = await fs.realpath(requestedOutputRoot);
const fixtureRoot = path.join(outputRoot, "fixtures");
const generationRoot = path.join(outputRoot, "generation");
const rawAssetRoot = path.join(outputRoot, "raw-assets");
const adapterOutputRoot = path.join(outputRoot, "adapter-output");

await fs.mkdir(fixtureRoot, { recursive: true });
await fs.mkdir(generationRoot, { recursive: true });

const academicMarkdown = `---
title: Fixture Study TITLE_METADATA_MARKER
author: Ada Evidence
---

# ABSTRACT_MARKER

PARAGRAPH_ONE_MARKER describes the controlled normalization fixture.

PARAGRAPH_TWO_MARKER remains a separate paragraph.

## METHODS_MARKER

The structured observations are shown below.

| TABLE_HEADER_MARKER | count | note |
| --- | ---: | --- |
| TABLE_CELL_MARKER | 12 | preserved value |

![FIGURE_CAPTION_MARKER](figure.png)

$$
E = mc^2 \\tag{EQUATION_MARKER}
$$

A footnote is attached here.[^fixture]

[^fixture]: FOOTNOTE_MARKER

## REFERENCES_MARKER

REFERENCE_MARKER. Example reference. https://doi.org/10.0000/fixture
`;

await fs.writeFile(path.join(fixtureRoot, "academic.md"), academicMarkdown, "utf8");
await fs.writeFile(
  path.join(fixtureRoot, "academic.txt"),
  [
    "TITLE_METADATA_MARKER",
    "ABSTRACT_MARKER",
    "PARAGRAPH_ONE_MARKER describes the controlled normalization fixture.",
    "",
    "PARAGRAPH_TWO_MARKER remains a separate paragraph.",
    "METHODS_MARKER",
    "TABLE_HEADER_MARKER\tcount\tnote",
    "TABLE_CELL_MARKER\t12\tpreserved value",
    "FIGURE_CAPTION_MARKER",
    "EQUATION_MARKER: E = mc^2",
    "REFERENCES_MARKER",
    "REFERENCE_MARKER https://doi.org/10.0000/fixture",
    ""
  ].join("\n"),
  "utf8"
);
await fs.writeFile(
  path.join(fixtureRoot, "invalid-utf8.txt"),
  Buffer.concat([
    Buffer.from("INVALID_UTF8_LEFT", "utf8"),
    Buffer.from([0xff, 0xfe]),
    Buffer.from("INVALID_UTF8_RIGHT\nCONTROL_LEFT\0CONTROL_RIGHT\n", "utf8")
  ])
);

await fs.writeFile(
  path.join(fixtureRoot, "structured.json"),
  `${JSON.stringify(
    {
      metadata: { title: "TITLE_METADATA_MARKER", author: "Ada Evidence" },
      sections: [
        { heading: "ABSTRACT_MARKER", paragraphs: ["PARAGRAPH_ONE_MARKER", "PARAGRAPH_TWO_MARKER"] },
        {
          heading: "METHODS_MARKER",
          table: [{ TABLE_HEADER_MARKER: "TABLE_CELL_MARKER", count: 12 }],
          figure: { caption: "FIGURE_CAPTION_MARKER" },
          equation: { label: "EQUATION_MARKER", latex: "E = mc^2" }
        },
        { heading: "REFERENCES_MARKER", references: [{ id: "REFERENCE_MARKER", doi: "10.0000/fixture" }] }
      ]
    },
    null,
    2
  )}\n`,
  "utf8"
);
await fs.writeFile(
  path.join(fixtureRoot, "malformed.json"),
  '{"ABSTRACT_MARKER": true, "broken": [1, 2, }\n',
  "utf8"
);
await fs.writeFile(
  path.join(fixtureRoot, "duplicate-keys.json"),
  '{"duplicate": "DUPLICATE_FIRST_MARKER", "duplicate": "DUPLICATE_SECOND_MARKER"}\n',
  "utf8"
);

await fs.writeFile(
  path.join(fixtureRoot, "table.csv"),
  'TABLE_HEADER_MARKER,count,note\nTABLE_CELL_MARKER,12,"MULTILINE_FIRST_MARKER\nMULTILINE_SECOND_MARKER"\n',
  "utf8"
);
await fs.writeFile(
  path.join(fixtureRoot, "ragged.csv"),
  "TABLE_HEADER_MARKER,count\nTABLE_CELL_MARKER,12,UNEXPECTED_THIRD_CELL\nMISSING_SECOND_CELL\n",
  "utf8"
);

const academicHtml = `<!doctype html>
<html>
<head>
  <title>TITLE_METADATA_MARKER</title>
  <meta name="citation_author" content="Ada Evidence">
  <meta name="citation_doi" content="10.0000/fixture">
</head>
<body>
  <article>
    <h1>ABSTRACT_MARKER</h1>
    <p>PARAGRAPH_ONE_MARKER describes the controlled normalization fixture.</p>
    <p>PARAGRAPH_TWO_MARKER remains a separate paragraph.</p>
    <section>
      <h2>METHODS_MARKER</h2>
      <table><thead><tr><th>TABLE_HEADER_MARKER</th><th>count</th></tr></thead>
      <tbody><tr><td>TABLE_CELL_MARKER</td><td>12</td></tr></tbody></table>
      <figure><img src="figure.png" alt="FIGURE_ALT_MARKER"><figcaption>FIGURE_CAPTION_MARKER</figcaption></figure>
      <math><mtext>EQUATION_MARKER</mtext><mi>E</mi><mo>=</mo><mi>m</mi><msup><mi>c</mi><mn>2</mn></msup></math>
    </section>
    <section><h2>REFERENCES_MARKER</h2><p>REFERENCE_MARKER doi:10.0000/fixture</p></section>
  </article>
</body>
</html>\n`;
await fs.writeFile(path.join(fixtureRoot, "academic.html"), academicHtml, "utf8");
await fs.writeFile(
  path.join(fixtureRoot, "malformed.html"),
  "<article><h1>ABSTRACT_MARKER<p>UNCLOSED_PARAGRAPH_MARKER<table><tr><th>TABLE_HEADER_MARKER<td>TABLE_CELL_MARKER",
  "utf8"
);

const figurePng = path.join(generationRoot, "figure.png");
await writeTextPng(figurePng, "SCANNED_TEXT_MARKER");
await fs.copyFile(figurePng, path.join(fixtureRoot, "figure.png"));

await writeNativePdf(path.join(fixtureRoot, "academic.pdf"));
await writeImageOnlyPdf(path.join(fixtureRoot, "scanned.pdf"), figurePng);
await fs.writeFile(path.join(fixtureRoot, "malformed.pdf"), "NOT A PDF MALFORMED_PDF_MARKER\n", "utf8");

const docxSource = path.join(generationRoot, "academic-docx-source.md");
await fs.writeFile(docxSource, academicMarkdown, "utf8");
execFileSync("pandoc", [docxSource, "--resource-path", generationRoot, "-o", path.join(fixtureRoot, "academic.docx")], {
  cwd: generationRoot,
  stdio: "pipe"
});
await fs.writeFile(path.join(fixtureRoot, "malformed.docx"), "NOT A ZIP MALFORMED_DOCX_MARKER\n", "utf8");

const rtfSource = path.join(generationRoot, "academic-doc-source.rtf");
await fs.writeFile(
  rtfSource,
  String.raw`{\rtf1\ansi
{\b TITLE_METADATA_MARKER}\par
{\b ABSTRACT_MARKER}\par
PARAGRAPH_ONE_MARKER describes the controlled normalization fixture.\par
\par
PARAGRAPH_TWO_MARKER remains a separate paragraph.\par
{\b METHODS_MARKER}\par
TABLE_HEADER_MARKER\tab count\tab note\par
TABLE_CELL_MARKER\tab 12\tab preserved value\par
FIGURE_CAPTION_MARKER\par
EQUATION_MARKER: E = mc^2\par
{\b REFERENCES_MARKER}\par
REFERENCE_MARKER https://doi.org/10.0000/fixture\par
}`,
  "utf8"
);
execFileSync("textutil", ["-convert", "doc", "-output", path.join(fixtureRoot, "academic.doc"), rtfSource], {
  stdio: "pipe"
});
await fs.writeFile(path.join(fixtureRoot, "malformed.doc"), Buffer.from([0x00, 0xff, 0x00, 0xfe, 0x41]));

await writeHnCaj(path.join(fixtureRoot, "outline.caj"));
await fs.writeFile(path.join(fixtureRoot, "unknown.caj"), "NOT_A_REAL_CAJ UNKNOWN_CAJ_MARKER\n", "utf8");

await fs.writeFile(
  path.join(fixtureRoot, "unsupported.tex"),
  "\\section{ABSTRACT_MARKER} UNSUPPORTED_TEX_MARKER $E=mc^2$\n",
  "utf8"
);
await fs.writeFile(
  path.join(fixtureRoot, "unsupported.rtf"),
  String.raw`{\rtf1\ansi UNSUPPORTED_RTF_MARKER}`,
  "utf8"
);

const options = {
  chunkSize: 6000,
  chunkOverlap: 500,
  assetDir: rawAssetRoot,
  pdf: { renderPages: true, maxRenderedPages: 25, renderDpi: 180 }
};
const rawResult = await loadPath(fixtureRoot, options);
await fs.writeFile(path.join(outputRoot, "raw-loader-result.json"), `${JSON.stringify(rawResult, null, 2)}\n`, "utf8");

const unsupportedDirect = {};
for (const relativePath of ["unsupported.tex", "unsupported.rtf", "figure.png"]) {
  unsupportedDirect[relativePath] = await loadPath(path.join(fixtureRoot, relativePath), {
    ...options,
    assetDir: path.join(outputRoot, "unsupported-assets", relativePath.replaceAll(".", "-"))
  });
}
await fs.writeFile(
  path.join(outputRoot, "unsupported-direct-result.json"),
  `${JSON.stringify(unsupportedDirect, null, 2)}\n`,
  "utf8"
);

const adapterResultPath = path.join(outputRoot, "python-adapter-result.json");
const pythonProbe = `
import json
import sys
from pathlib import Path

from asl.smart_loader import SmartLoader

fixture_root = Path(sys.argv[1])
output_root = Path(sys.argv[2])
result_path = Path(sys.argv[3])
group = SmartLoader().load_group("references", [fixture_root], output_root)
payload = {
    "metadata_summary": group.metadata(),
    "markdown": group.markdown,
    "results": list(group.results),
}
result_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
`;
execFileSync("python3", ["-c", pythonProbe, fixtureRoot, adapterOutputRoot, adapterResultPath], {
  cwd: repositoryRoot,
  stdio: "pipe"
});
const adapterResult = JSON.parse(await fs.readFile(adapterResultPath, "utf8"));

const fixtureDigests = {};
for (const name of (await fs.readdir(fixtureRoot)).sort()) {
  const filePath = path.join(fixtureRoot, name);
  const stat = await fs.stat(filePath);
  if (stat.isFile()) {
    const buffer = await fs.readFile(filePath);
    fixtureDigests[name] = {
      sha256: createHash("sha256").update(buffer).digest("hex"),
      sizeBytes: buffer.length
    };
  }
}

const report = {
  schema: "asl-normalization-fixture-probe-v1",
  capturedAtUtc: new Date().toISOString(),
  repositoryRevision: execFileSync("git", ["rev-parse", "HEAD"], { cwd: repositoryRoot, encoding: "utf8" }).trim(),
  outputRoot,
  fixtureRoot,
  generatorTools: toolVersions(),
  fixtureDigests,
  directorySummary: rawResult.summary,
  errors: rawResult.errors,
  documents: rawResult.documents.map(summarizeDocument),
  unsupportedDirectoryObservation: {
    presentFixtureNames: ["unsupported.tex", "unsupported.rtf", "figure.png"],
    discoveredByDirectoryScan: rawResult.documents
      .map((document) => document.relativePath)
      .filter((name) => ["unsupported.tex", "unsupported.rtf", "figure.png"].includes(name)),
    skippedFilesCounter: rawResult.summary.skippedFiles
  },
  unsupportedDirect: Object.fromEntries(
    Object.entries(unsupportedDirect).map(([name, result]) => [name, { summary: result.summary, errors: result.errors }])
  ),
  adapterObservation: {
    metadataSummary: adapterResult.metadata_summary,
    markdownHasWarnings: adapterResult.markdown.includes("Warnings:"),
    markdownHasLoadErrors: adapterResult.markdown.includes("Load errors:"),
    markdownHasOcrText: adapterResult.markdown.includes("SCANNED_TEXT_MARKER"),
    markdownLength: adapterResult.markdown.length,
    rawDocumentWarningCount: adapterResult.results
      .flatMap((result) => result.documents ?? [])
      .reduce((count, document) => count + (document.warnings?.length ?? 0), 0),
    metadataSummaryHasDocumentWarnings: Object.hasOwn(adapterResult.metadata_summary, "warnings")
  }
};

await fs.writeFile(path.join(outputRoot, "probe-report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);

function summarizeDocument(document) {
  const combined = `${document.text}\n${document.markdown}`;
  const unescapedCombined = combined.replace(/\\([_*=])/g, "$1");
  const markerNames = [
    "TITLE_METADATA_MARKER",
    "ABSTRACT_MARKER",
    "PARAGRAPH_ONE_MARKER",
    "PARAGRAPH_TWO_MARKER",
    "METHODS_MARKER",
    "TABLE_HEADER_MARKER",
    "TABLE_CELL_MARKER",
    "FIGURE_ALT_MARKER",
    "FIGURE_CAPTION_MARKER",
    "EQUATION_MARKER",
    "FOOTNOTE_MARKER",
    "REFERENCES_MARKER",
    "REFERENCE_MARKER",
    "PAGE_TWO_MARKER",
    "SCANNED_TEXT_MARKER",
    "DUPLICATE_FIRST_MARKER",
    "DUPLICATE_SECOND_MARKER",
    "MULTILINE_FIRST_MARKER",
    "MULTILINE_SECOND_MARKER",
    "UNEXPECTED_THIRD_CELL",
    "MISSING_SECOND_CELL",
    "INVALID_UTF8_LEFT",
    "INVALID_UTF8_RIGHT",
    "CONTROL_LEFT",
    "CONTROL_RIGHT",
    "UNCLOSED_PARAGRAPH_MARKER",
    "UNKNOWN_CAJ_MARKER"
  ];
  return {
    relativePath: document.relativePath,
    format: document.format,
    title: document.title ?? null,
    mimeType: document.mimeType ?? null,
    loader: document.metadata.loader,
    textLength: document.text.length,
    markdownLength: document.markdown.length,
    chunkCount: document.chunks.length,
    chunkLocations: document.chunks.map((chunk) => ({
      startChar: chunk.metadata.startChar,
      endChar: chunk.metadata.endChar,
      format: chunk.metadata.format,
      relativePath: chunk.metadata.relativePath
    })),
    sourceMetadata: {
      sourcePath: document.sourcePath,
      relativePath: document.relativePath,
      sizeBytes: document.metadata.sizeBytes,
      modifiedAt: document.metadata.modifiedAt,
      formatMetadata: Object.fromEntries(
        Object.entries(document.metadata).filter(([key]) => !["sizeBytes", "modifiedAt", "loader"].includes(key))
      )
    },
    assets: document.assets.map((asset) => ({
      kind: asset.kind,
      mimeType: asset.mimeType ?? null,
      originalName: asset.originalName ?? null,
      metadata: asset.metadata ?? {}
    })),
    warnings: document.warnings,
    markers: Object.fromEntries(markerNames.map((marker) => [marker, unescapedCombined.includes(marker)])),
    structuralSignals: {
      markdownHeadingLines: document.markdown.split("\n").filter((line) => /^#{1,6} /.test(line)).length,
      markdownTableSeparator: /\|\s*---/.test(document.markdown),
      blankLineParagraphBoundary:
        /PARAGRAPH_ONE_MARKER[^]*?\n\s*\n[^]*?PARAGRAPH_TWO_MARKER/.test(document.markdown),
      literalEquation: /E\s*=\s*mc(?:\^?2|²)/.test(combined),
      pageCountMetadata: typeof document.metadata.pages === "number" ? document.metadata.pages : null,
      pageAttributedChunks: document.chunks.some((chunk) => Object.hasOwn(chunk.metadata, "page"))
    }
  };
}

async function writeNativePdf(filePath) {
  const document = new PDFDocument({
    info: {
      Title: "TITLE_METADATA_MARKER",
      Author: "Ada Evidence",
      Subject: "Normalization fixture",
      CreationDate: new Date("2020-01-01T00:00:00Z"),
      ModDate: new Date("2020-01-01T00:00:00Z")
    }
  });
  const stream = createWriteStream(filePath);
  document.pipe(stream);
  document.fontSize(18).text("ABSTRACT_MARKER");
  document.fontSize(11).text("PARAGRAPH_ONE_MARKER describes the controlled normalization fixture.");
  document.moveDown().text("PARAGRAPH_TWO_MARKER remains a separate paragraph.");
  document.moveDown().fontSize(16).text("METHODS_MARKER");
  document.fontSize(11).text("TABLE_HEADER_MARKER | count | note");
  document.text("TABLE_CELL_MARKER | 12 | preserved value");
  document.moveDown().text("FIGURE_CAPTION_MARKER");
  document.text("EQUATION_MARKER: E = mc^2");
  document.addPage();
  document.fontSize(16).text("REFERENCES_MARKER");
  document.fontSize(11).text("REFERENCE_MARKER https://doi.org/10.0000/fixture");
  document.text("PAGE_TWO_MARKER");
  document.end();
  await once(stream, "finish");
}

async function writeImageOnlyPdf(filePath, imagePath) {
  const document = new PDFDocument({
    info: {
      Title: "Scanned fixture",
      CreationDate: new Date("2020-01-01T00:00:00Z"),
      ModDate: new Date("2020-01-01T00:00:00Z")
    }
  });
  const stream = createWriteStream(filePath);
  document.pipe(stream);
  document.image(imagePath, 72, 72, { fit: [450, 200] });
  document.end();
  await once(stream, "finish");
}

async function writeTextPng(filePath, textValue) {
  const sourcePdf = path.join(generationRoot, "scan-source.pdf");
  const document = new PDFDocument({ size: [600, 220], margin: 20 });
  const stream = createWriteStream(sourcePdf);
  document.pipe(stream);
  document.font("Helvetica-Bold").fontSize(34).text(textValue, 25, 75);
  document.end();
  await once(stream, "finish");
  const prefix = path.join(generationRoot, "scan");
  execFileSync("pdftoppm", ["-png", "-r", "180", "-singlefile", sourcePdf, prefix], { stdio: "pipe" });
  await fs.rename(`${prefix}.png`, filePath);
}

async function writeHnCaj(filePath) {
  const tocOffset = 0x158;
  const entrySize = 0x134;
  const entries = [
    { title: "ABSTRACT_MARKER", page: 1, level: 1 },
    { title: "METHODS_MARKER", page: 3, level: 1 },
    { title: "REFERENCES_MARKER", page: 8, level: 1 }
  ];
  const buffer = Buffer.alloc(tocOffset + 4 + entrySize * entries.length);
  buffer.write("HN\0\0", 0, "latin1");
  buffer.writeInt32LE(entries.length, tocOffset);
  entries.forEach((entry, index) => {
    const start = tocOffset + 4 + entrySize * index;
    buffer.write(entry.title, start, "ascii");
    buffer.write(`${entry.page}\0`, start + 280, "ascii");
    buffer.writeInt32LE(entry.level, start + 0x130);
  });
  await fs.writeFile(filePath, buffer);
}

function toolVersions() {
  const probes = {
    node: ["node", ["--version"]],
    python: ["python3", ["--version"]],
    pandoc: ["pandoc", ["--version"]],
    pdftoppm: ["pdftoppm", ["-v"]],
    tesseract: ["tesseract", ["--version"]],
    textutil: ["textutil", ["-help"]],
    caj2pdf: ["caj2pdf", ["--help"]]
  };
  return Object.fromEntries(
    Object.entries(probes).map(([name, [command, args]]) => {
      try {
        const output = execFileSync(command, args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
        return [name, output.split(/\r?\n/).find(Boolean) ?? "available"];
      } catch (error) {
        const stderr = error?.stderr?.toString?.() ?? "";
        const stdout = error?.stdout?.toString?.() ?? "";
        const firstLine = `${stdout}\n${stderr}`.split(/\r?\n/).find((line) => line.trim());
        return [name, firstLine?.trim() ?? "unavailable"];
      }
    })
  );
}

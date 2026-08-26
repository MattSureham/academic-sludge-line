import { spawnSync } from "node:child_process";
import { createWriteStream, promises as fs } from "node:fs";
import { once } from "node:events";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import PDFDocument from "pdfkit";
import { describe, expect, it } from "vitest";
import { loadPath, splitText } from "../src/index.js";

const NO_EXTRACTABLE_PDF_TEXT_WARNING = "No extractable PDF text was found. The PDF may be scanned or image-heavy.";
const INVALID_UTF8_WARNING = "Invalid UTF-8 byte sequences were replaced during text decoding.";
const NUL_REMOVAL_WARNING = "NUL bytes were removed during text normalization.";
const ONE_PIXEL_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64"
);

describe("smart-loader", () => {
  it("loads supported files and reports unsupported directory inputs", async () => {
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), "smart-loader-test-"));
    await fs.writeFile(path.join(dir, "note.md"), "# Note\n\nHello world.");
    await fs.writeFile(path.join(dir, "data.json"), JSON.stringify({ ok: true, count: 2 }));
    await fs.writeFile(path.join(dir, "table.csv"), "name,score\nAda,10\nLinus,9\n");
    await fs.writeFile(path.join(dir, "image.png"), "not really an image");
    await fs.writeFile(path.join(dir, "paper.tex"), "\\section{Unsupported}");
    await fs.writeFile(path.join(dir, "notes.rtf"), "{\\rtf1 Unsupported}");

    const result = await loadPath(dir, { chunkSize: 1000, chunkOverlap: 100 });

    expect(result.summary.discoveredFiles).toBe(6);
    expect(result.summary.loadedFiles).toBe(3);
    expect(result.summary.skippedFiles).toBe(3);
    expect(result.summary.failedFiles).toBe(0);
    expect(result.documents.map((doc) => doc.relativePath).sort()).toEqual(["data.json", "note.md", "table.csv"]);
    expect(result.chunks.length).toBe(3);
    expect(result.documents.find((doc) => doc.relativePath === "table.csv")?.markdown).toContain("| name | score |");
    expect(
      result.errors
        .map((error) => ({
          sourcePath: error.sourcePath,
          reason: error.reason,
          code: error.code
        }))
        .sort((a, b) => a.sourcePath.localeCompare(b.sourcePath))
    ).toEqual([
      {
        sourcePath: path.join(dir, "image.png"),
        reason: "Unsupported file extension: .png",
        code: "unsupported_file"
      },
      {
        sourcePath: path.join(dir, "notes.rtf"),
        reason: "Unsupported file extension: .rtf",
        code: "unsupported_file"
      },
      {
        sourcePath: path.join(dir, "paper.tex"),
        reason: "Unsupported file extension: .tex",
        code: "unsupported_file"
      }
    ]);

    const cliPath = fileURLToPath(new URL("../dist/cli.js", import.meta.url));
    const mixedCli = spawnSync(process.execPath, [cliPath, dir, "--format", "json", "--fail-on-error"], {
      encoding: "utf8"
    });
    expect(mixedCli.status).toBe(0);
    expect(JSON.parse(mixedCli.stdout).summary).toMatchObject({ loadedFiles: 3, skippedFiles: 3, failedFiles: 0 });

    const directUnsupportedCli = spawnSync(
      process.execPath,
      [cliPath, path.join(dir, "paper.tex"), "--format", "json", "--fail-on-error"],
      { encoding: "utf8" }
    );
    expect(directUnsupportedCli.status).toBe(1);
    expect(JSON.parse(directUnsupportedCli.stdout)).toMatchObject({
      summary: { loadedFiles: 0, skippedFiles: 0, failedFiles: 1 },
      errors: [{ sourcePath: path.join(dir, "paper.tex"), code: "load_failed" }]
    });
  });

  it("warns about invalid UTF-8 replacement and NUL removal without rewriting normalized text", async () => {
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), "smart-loader-invalid-text-test-"));
    const filePath = path.join(dir, "invalid-utf8.txt");
    await fs.writeFile(
      filePath,
      Buffer.concat([
        Buffer.from("INVALID_UTF8_LEFT", "utf8"),
        Buffer.from([0xff, 0xfe]),
        Buffer.from("INVALID_UTF8_RIGHT\nCONTROL_LEFT\0CONTROL_RIGHT\n", "utf8")
      ])
    );

    const result = await loadPath(filePath, { chunkSize: 1000, chunkOverlap: 100 });
    const document = result.documents[0];
    const expectedText = "INVALID_UTF8_LEFT��INVALID_UTF8_RIGHT\nCONTROL_LEFTCONTROL_RIGHT\n";

    expect(result.errors).toEqual([]);
    expect(result.summary.loadedFiles).toBe(1);
    expect(document.text).toBe(expectedText);
    expect(document.markdown).toBe(expectedText);
    expect(document.chunks.map((chunk) => chunk.text)).toEqual([expectedText.trim()]);
    expect(document.warnings).toEqual([INVALID_UTF8_WARNING, NUL_REMOVAL_WARNING]);
  });

  it("keeps valid UTF-8 text warning-free, including an encoded replacement character", async () => {
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), "smart-loader-valid-text-test-"));
    const filePath = path.join(dir, "valid-utf8.txt");
    const sourceText = "Valid UTF-8: café, 研究, and �.\n";
    await fs.writeFile(filePath, sourceText, "utf8");

    const result = await loadPath(filePath, { chunkSize: 1000, chunkOverlap: 100 });
    const document = result.documents[0];

    expect(result.errors).toEqual([]);
    expect(document.text).toBe(sourceText);
    expect(document.markdown).toBe(sourceText);
    expect(document.chunks.map((chunk) => chunk.text)).toEqual([sourceText.trim()]);
    expect(document.warnings).toEqual([]);
  });

  it("splits long text with overlap", () => {
    const text = Array.from({ length: 100 }, (_, index) => `Sentence ${index}.`).join(" ");
    const chunks = splitText(text, 120, 20);

    expect(chunks.length).toBeGreaterThan(1);
    expect(chunks[0].endChar).toBeGreaterThan(chunks[1].startChar);
  });

  it("loads extractable PDF text", async () => {
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), "smart-loader-pdf-test-"));
    await writePdf(path.join(dir, "hello.pdf"), "Hello from a generated PDF.");

    const result = await loadPath(dir, { chunkSize: 1000, chunkOverlap: 100 });
    const document = result.documents.find((doc) => doc.relativePath === "hello.pdf");

    expect(result.errors).toEqual([]);
    expect(document?.format).toBe("pdf");
    expect(document?.text).toContain("Hello from a generated PDF.");
    expect(document?.warnings).not.toContain(NO_EXTRACTABLE_PDF_TEXT_WARNING);
  });

  it("warns when PDF extraction contains only page markers", async () => {
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), "smart-loader-image-pdf-test-"));
    await writeImageOnlyPdf(path.join(dir, "scan.pdf"));

    const result = await loadPath(dir, { chunkSize: 1000, chunkOverlap: 100 });
    const document = result.documents.find((doc) => doc.relativePath === "scan.pdf");

    expect(result.errors).toEqual([]);
    expect(result.summary.loadedFiles).toBe(1);
    expect(document?.format).toBe("pdf");
    expect(document?.text).toMatch(/^--\s+1\s+of\s+1\s+--$/);
    expect(document?.warnings).toContain(NO_EXTRACTABLE_PDF_TEXT_WARNING);
    expect(document?.markdown).toContain("-- 1 of 1 --");
    expect(document?.chunks).toHaveLength(1);
  });

  it("discovers CAJ files and falls back to outline metadata", async () => {
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), "smart-loader-caj-test-"));
    const filePath = path.join(dir, "sample.caj");
    const buffer = Buffer.alloc(0x158 + 4 + 0x134);
    buffer.write("HN\0\0", 0, "latin1");
    buffer.writeInt32LE(1, 0x158);
    buffer.write("Abstract", 0x158 + 4, "ascii");
    buffer.write("3\0", 0x158 + 4 + 280, "ascii");
    buffer.writeInt32LE(1, 0x158 + 4 + 0x130);
    await fs.writeFile(filePath, buffer);

    const previousConverter = process.env.SMART_LOADER_CAJ2PDF;
    process.env.SMART_LOADER_CAJ2PDF = path.join(dir, "missing-caj2pdf");
    try {
      const result = await loadPath(dir, { chunkSize: 1000, chunkOverlap: 100 });
      const document = result.documents.find((doc) => doc.relativePath === "sample.caj");

      expect(result.summary.discoveredFiles).toBe(1);
      expect(result.summary.loadedFiles).toBe(1);
      expect(document?.format).toBe("caj");
      expect(document?.text).toContain("Abstract");
      expect(document?.warnings.join("\n")).toContain("outline metadata");
    } finally {
      if (previousConverter === undefined) {
        delete process.env.SMART_LOADER_CAJ2PDF;
      } else {
        process.env.SMART_LOADER_CAJ2PDF = previousConverter;
      }
    }
  });
});

async function writePdf(filePath: string, text: string): Promise<void> {
  const document = new PDFDocument();
  const stream = createWriteStream(filePath);
  document.pipe(stream);
  document.text(text);
  document.end();
  await once(stream, "finish");
}

async function writeImageOnlyPdf(filePath: string): Promise<void> {
  const document = new PDFDocument();
  const stream = createWriteStream(filePath);
  document.pipe(stream);
  document.image(ONE_PIXEL_PNG, 72, 72, { width: 32 });
  document.end();
  await once(stream, "finish");
}

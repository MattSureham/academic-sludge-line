import { promises as fs } from "node:fs";
import path from "node:path";
import { loadPdf } from "./pdf.js";
import type { FileLoader } from "../types.js";
import { findExecutable, makeTempDir, runFile } from "../utils.js";

const KDH_PASSPHRASE = Buffer.from("FZHMEI");
const CAJ_MIME = "application/x-caj";

type CajFormat = "CAJ" | "HN" | "KDH" | "PDF" | "unknown";

export const loadCaj: FileLoader = async (filePath, context) => {
  const buffer = await fs.readFile(filePath);
  const cajFormat = detectCajFormat(buffer);
  const warnings: string[] = [];
  const title = path.basename(filePath);
  const outline = extractOutline(buffer, cajFormat, warnings);

  const convertedPdf = await convertCajToPdf(filePath, buffer, cajFormat, warnings);
  if (convertedPdf) {
    const parsed = await loadPdf(convertedPdf, context);
    const outlineText = outlineMarkdown(outline);
    const appendOutline = Boolean(outlineText && (cajFormat === "HN" || !parsed.text.trim()));
    const text = [parsed.text.trim(), appendOutline ? outlineText : ""].filter(Boolean).join("\n\n");
    if (appendOutline) {
      warnings.push(
        cajFormat === "HN"
          ? "HN conversion produced image-oriented PDF output; appended CAJ outline metadata as fallback context."
          : "Converted CAJ PDF had no extractable text; appended CAJ outline metadata as fallback context."
      );
    }
    return {
      ...parsed,
      text,
      title,
      markdown: `# ${title}\n\nConverted from ${cajFormat} through CAJ-to-PDF before text extraction.\n\n${parsed.markdown ?? parsed.text}${appendOutline ? `\n\n## CAJ Outline\n\n${outlineText}` : ""}`,
      warnings: [...warnings, ...(parsed.warnings ?? [])],
      metadata: {
        ...(parsed.metadata ?? {}),
        cajFormat,
        convertedPdf
      },
      loader: "caj",
      mimeType: CAJ_MIME
    };
  }

  const outlineText = outlineMarkdown(outline);
  warnings.push(
    cajFormat === "HN"
      ? "HN-format CAJ conversion requires JBIG decoder libraries; loaded outline metadata only."
      : "CAJ text could not be converted to PDF; loaded available outline metadata only."
  );

  const text = outlineText.trim();
  return {
    text,
    markdown: `# ${title}\n\nFormat: ${cajFormat}\n\n${text || "[No extractable CAJ text or outline metadata found.]"}`,
    warnings,
    metadata: {
      cajFormat,
      outlineCount: outline.length
    },
    title,
    loader: "caj",
    mimeType: CAJ_MIME
  };
};

async function convertCajToPdf(
  filePath: string,
  buffer: Buffer,
  cajFormat: CajFormat,
  warnings: string[]
): Promise<string | undefined> {
  const external = process.env.SMART_LOADER_CAJ2PDF || process.env.CAJ2PDF_BIN || await findExecutable(["caj2pdf"]);
  if (external) {
    const converted = await runExternalCaj2Pdf(external, filePath, warnings);
    if (converted) {
      return converted;
    }
  } else {
    warnings.push("caj2pdf was not found; install it or set SMART_LOADER_CAJ2PDF to enable CAJ/HN conversion.");
  }

  if (cajFormat === "KDH") {
    return convertKdh(buffer, warnings);
  }

  return undefined;
}

async function runExternalCaj2Pdf(command: string, filePath: string, warnings: string[]): Promise<string | undefined> {
  const tempDir = await makeTempDir("smart-loader-caj-");
  await copyOptionalCajLibraries(tempDir);
  const outPath = path.join(tempDir, `${path.basename(filePath, path.extname(filePath))}.pdf`);
  try {
    await runFile(command, ["convert", filePath, "-o", outPath], { cwd: tempDir, maxBuffer: 200 * 1024 * 1024 });
  } catch (error) {
    const message = compactCommandError(error);
    warnings.push(`caj2pdf conversion did not complete cleanly. ${message}`);
  }

  if (await existsWithSize(outPath)) {
    return outPath;
  }

  const intermediate = path.join(tempDir, "pdf_toc.pdf");
  if (await existsWithSize(intermediate)) {
    warnings.push("caj2pdf failed while adding outlines; using its repaired intermediate PDF without outlines.");
    return intermediate;
  }

  return undefined;
}

async function copyOptionalCajLibraries(tempDir: string): Promise<void> {
  const home = process.env.HOME;
  const candidates = [
    process.env.SMART_LOADER_CAJ_LIBDIR,
    home ? path.join(home, ".local", "share", "caj2pdf") : undefined
  ].filter(Boolean) as string[];

  for (const dir of candidates) {
    for (const name of ["libjbigdec.so", "libjbig2codec.so"]) {
      const source = path.join(dir, name);
      if (await existsWithSize(source)) {
        await fs.copyFile(source, path.join(tempDir, name));
      }
    }
  }
}

async function convertKdh(buffer: Buffer, warnings: string[]): Promise<string | undefined> {
  const mutool = await findExecutable(["mutool"]);
  if (!mutool) {
    warnings.push("KDH conversion requires mutool, but it was not found.");
    return undefined;
  }

  const tempDir = await makeTempDir("smart-loader-kdh-");
  const rawPath = path.join(tempDir, "raw.pdf");
  const outPath = path.join(tempDir, "clean.pdf");
  const decrypted = Buffer.alloc(Math.max(0, buffer.length - 254));
  for (let index = 254; index < buffer.length; index += 1) {
    decrypted[index - 254] = buffer[index] ^ KDH_PASSPHRASE[(index - 254) % KDH_PASSPHRASE.length];
  }
  const eof = decrypted.lastIndexOf(Buffer.from("%%EOF"));
  if (eof < 0) {
    warnings.push("KDH conversion failed: %%EOF marker was not found after decrypting.");
    return undefined;
  }
  await fs.writeFile(rawPath, decrypted.subarray(0, eof + 5));
  try {
    await runFile(mutool, ["clean", rawPath, outPath], { maxBuffer: 200 * 1024 * 1024 });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    warnings.push(`mutool failed while repairing decrypted KDH PDF. ${message}`);
    return undefined;
  }
  return (await existsWithSize(outPath)) ? outPath : undefined;
}

function detectCajFormat(buffer: Buffer): CajFormat {
  if (buffer.subarray(0, 4).toString("latin1") === "KDH ") {
    return "KDH";
  }
  if (buffer.subarray(0, 3).toString("latin1") === "CAJ") {
    return "CAJ";
  }
  if (buffer.subarray(0, 2).toString("latin1") === "HN") {
    return "HN";
  }
  if (buffer.subarray(0, 4).toString("latin1") === "%PDF") {
    return "PDF";
  }
  return "unknown";
}

function extractOutline(buffer: Buffer, cajFormat: CajFormat, warnings: string[]): Array<{ title: string; page: number; level: number }> {
  const tocOffset = cajFormat === "CAJ" ? 0x110 : cajFormat === "HN" ? 0x158 : 0;
  if (!tocOffset || buffer.length < tocOffset + 4) {
    return [];
  }

  const count = buffer.readInt32LE(tocOffset);
  if (count <= 0) {
    return [];
  }
  if (count > 1000) {
    warnings.push(`CAJ outline count looked invalid (${count}); skipping outline extraction.`);
    return [];
  }

  const decoder = new TextDecoder("gb18030", { fatal: false });
  const outline: Array<{ title: string; page: number; level: number }> = [];
  for (let index = 0; index < count; index += 1) {
    const start = tocOffset + 4 + 0x134 * index;
    if (start + 0x134 > buffer.length) {
      break;
    }
    const titleBytes = trimAtNull(buffer.subarray(start, start + 256));
    const pageBytes = trimAtNull(buffer.subarray(start + 280, start + 292));
    const title = decoder.decode(titleBytes).trim();
    const page = Number.parseInt(pageBytes.toString("ascii").trim(), 10);
    const level = buffer.readInt32LE(start + 0x130);
    if (title && Number.isFinite(page)) {
      outline.push({ title, page, level: Number.isFinite(level) && level > 0 ? level : 1 });
    }
  }
  return outline;
}

function outlineMarkdown(outline: Array<{ title: string; page: number; level: number }>): string {
  return outline.length
    ? outline.map((entry) => `${"  ".repeat(Math.max(0, entry.level - 1))}- p.${entry.page}: ${entry.title}`).join("\n")
    : "";
}

function trimAtNull(buffer: Buffer): Buffer {
  const end = buffer.indexOf(0);
  return end >= 0 ? buffer.subarray(0, end) : buffer;
}

async function existsWithSize(filePath: string): Promise<boolean> {
  try {
    const stat = await fs.stat(filePath);
    return stat.size > 0;
  } catch {
    return false;
  }
}

function compactCommandError(error: unknown): string {
  const details = error as { stderr?: string; stdout?: string; message?: string };
  const raw = details.stderr || details.stdout || details.message || String(error);
  const lines = raw.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const selected = lines.length > 8 ? [...lines.slice(0, 3), "...", ...lines.slice(-4)] : lines;
  return selected.join(" ");
}

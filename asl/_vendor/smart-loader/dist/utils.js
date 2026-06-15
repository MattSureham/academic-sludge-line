import { execFile } from "node:child_process";
import crypto from "node:crypto";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
const execFileAsync = promisify(execFile);
export function stableId(input) {
    return crypto.createHash("sha1").update(input).digest("hex").slice(0, 12);
}
export function documentId(filePath, rootPath) {
    return `doc_${stableId(path.relative(rootPath, filePath) || filePath)}`;
}
export function extensionOf(filePath) {
    return path.extname(filePath).toLowerCase();
}
export async function readUtf8(filePath) {
    const buffer = await fs.readFile(filePath);
    return new TextDecoder("utf-8", { fatal: false }).decode(buffer);
}
export function estimateTokens(text) {
    return Math.ceil(text.length / 4);
}
export async function ensureDir(dirPath) {
    await fs.mkdir(dirPath, { recursive: true });
}
export async function assetDirForFile(filePath, context) {
    const dir = path.join(context.options.assetDir, documentId(filePath, context.rootPath));
    await ensureDir(dir);
    return dir;
}
export function mimeTypeForImageExtension(ext) {
    switch (ext.toLowerCase()) {
        case ".png":
            return "image/png";
        case ".jpg":
        case ".jpeg":
            return "image/jpeg";
        case ".gif":
            return "image/gif";
        case ".webp":
            return "image/webp";
        case ".svg":
            return "image/svg+xml";
        case ".tif":
        case ".tiff":
            return "image/tiff";
        default:
            return undefined;
    }
}
export function extensionForMimeType(mimeType) {
    switch (mimeType) {
        case "image/png":
            return ".png";
        case "image/jpeg":
            return ".jpg";
        case "image/gif":
            return ".gif";
        case "image/webp":
            return ".webp";
        case "image/svg+xml":
            return ".svg";
        case "image/tiff":
            return ".tiff";
        default:
            return ".bin";
    }
}
export async function findExecutable(names) {
    const finder = process.platform === "win32" ? "where" : "which";
    for (const name of names) {
        try {
            const { stdout } = await execFileAsync(finder, [name]);
            const first = stdout.split(/\r?\n/).map((line) => line.trim()).find(Boolean);
            if (first) {
                return first;
            }
        }
        catch {
            // Continue probing the next candidate.
        }
    }
    return undefined;
}
export async function runFile(command, args, options = {}) {
    return execFileAsync(command, args, {
        cwd: options.cwd,
        maxBuffer: options.maxBuffer ?? 100 * 1024 * 1024
    });
}
export async function makeTempDir(prefix) {
    return fs.mkdtemp(path.join(os.tmpdir(), prefix));
}
export function stripControlCharacters(text) {
    return text.replace(/\u0000/g, "").replace(/\r\n/g, "\n");
}

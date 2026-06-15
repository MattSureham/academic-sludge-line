import type { LoaderContext } from "./types.js";
export declare function stableId(input: string): string;
export declare function documentId(filePath: string, rootPath: string): string;
export declare function extensionOf(filePath: string): string;
export declare function readUtf8(filePath: string): Promise<string>;
export declare function estimateTokens(text: string): number;
export declare function ensureDir(dirPath: string): Promise<void>;
export declare function assetDirForFile(filePath: string, context: LoaderContext): Promise<string>;
export declare function mimeTypeForImageExtension(ext: string): string | undefined;
export declare function extensionForMimeType(mimeType?: string): string;
export declare function findExecutable(names: string[]): Promise<string | undefined>;
export declare function runFile(command: string, args: string[], options?: {
    cwd?: string;
    maxBuffer?: number;
}): Promise<{
    stdout: string;
    stderr: string;
}>;
export declare function makeTempDir(prefix: string): Promise<string>;
export declare function stripControlCharacters(text: string): string;

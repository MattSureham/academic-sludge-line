import type { FileLoader, SupportedFormat } from "./types.js";
export declare const EXTENSION_TO_FORMAT: Map<string, SupportedFormat>;
export declare const FORMAT_LOADERS: Record<SupportedFormat, FileLoader>;
export declare const SUPPORTED_EXTENSIONS: string[];

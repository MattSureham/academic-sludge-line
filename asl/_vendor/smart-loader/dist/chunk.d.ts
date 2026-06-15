import type { DocumentChunk, LoadedDocument } from "./types.js";
export interface TextSlice {
    text: string;
    startChar: number;
    endChar: number;
}
export declare function splitText(text: string, maxChars: number, overlapChars: number): TextSlice[];
export declare function buildChunks(document: Omit<LoadedDocument, "chunks">, maxChars: number, overlapChars: number): DocumentChunk[];

import { estimateTokens } from "./utils.js";
export function splitText(text, maxChars, overlapChars) {
    const normalized = text.trim();
    if (!normalized) {
        return [];
    }
    const slices = [];
    let start = 0;
    while (start < normalized.length) {
        const hardEnd = Math.min(start + maxChars, normalized.length);
        let end = hardEnd;
        if (hardEnd < normalized.length) {
            const window = normalized.slice(start, hardEnd);
            const preferredBreaks = ["\n\n", "\n", ". ", " "];
            for (const marker of preferredBreaks) {
                const index = window.lastIndexOf(marker);
                if (index > maxChars * 0.55) {
                    end = start + index + marker.length;
                    break;
                }
            }
        }
        const sliceText = normalized.slice(start, end).trim();
        if (sliceText) {
            slices.push({ text: sliceText, startChar: start, endChar: end });
        }
        if (end >= normalized.length) {
            break;
        }
        start = Math.max(0, end - overlapChars);
        if (start >= end) {
            start = end;
        }
    }
    return slices;
}
export function buildChunks(document, maxChars, overlapChars) {
    const source = document.markdown || document.text;
    return splitText(source, maxChars, overlapChars).map((slice, index) => ({
        id: `${document.id}_chunk_${index + 1}`,
        documentId: document.id,
        text: slice.text,
        markdown: slice.text,
        index,
        metadata: {
            sourcePath: document.sourcePath,
            relativePath: document.relativePath,
            format: document.format,
            tokenEstimate: estimateTokens(slice.text),
            startChar: slice.startChar,
            endChar: slice.endChar
        }
    }));
}

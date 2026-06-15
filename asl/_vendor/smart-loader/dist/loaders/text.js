import path from "node:path";
import { parse as parseCsv } from "csv-parse/sync";
import TurndownService from "turndown";
import { readUtf8, stripControlCharacters } from "../utils.js";
export const loadMarkdown = async (filePath) => {
    const text = stripControlCharacters(await readUtf8(filePath));
    return {
        text,
        markdown: text,
        loader: "markdown"
    };
};
export const loadText = async (filePath) => {
    const text = stripControlCharacters(await readUtf8(filePath));
    return {
        text,
        markdown: text,
        loader: "text"
    };
};
export const loadJson = async (filePath) => {
    const raw = stripControlCharacters(await readUtf8(filePath));
    const warnings = [];
    let formatted = raw;
    try {
        formatted = JSON.stringify(JSON.parse(raw), null, 2);
    }
    catch (error) {
        warnings.push(`JSON parse failed; returning raw text. ${error.message}`);
    }
    return {
        text: formatted,
        markdown: fencedCode("json", formatted),
        warnings,
        loader: "json"
    };
};
export const loadCsv = async (filePath, context) => {
    const raw = stripControlCharacters(await readUtf8(filePath));
    const warnings = [];
    try {
        const rows = parseCsv(raw, {
            bom: true,
            relaxColumnCount: true,
            skipEmptyLines: false
        });
        const previewRows = rows.slice(0, context.options.csvPreviewRows);
        const markdown = csvRowsToMarkdown(previewRows);
        const omitted = rows.length > previewRows.length ? `\n\n_Only the first ${previewRows.length} of ${rows.length} CSV rows are shown above._` : "";
        return {
            text: raw,
            markdown: `${markdown}${omitted}\n\n${fencedCode("csv", raw)}`,
            warnings,
            metadata: {
                rows: rows.length,
                previewRows: previewRows.length
            },
            loader: "csv"
        };
    }
    catch (error) {
        warnings.push(`CSV parse failed; returning raw text. ${error.message}`);
        return {
            text: raw,
            markdown: fencedCode("csv", raw),
            warnings,
            loader: "csv"
        };
    }
};
export const loadHtml = async (filePath) => {
    const html = stripControlCharacters(await readUtf8(filePath));
    const turndown = new TurndownService({ codeBlockStyle: "fenced", headingStyle: "atx" });
    const markdown = turndown.turndown(html);
    return {
        text: markdown,
        markdown,
        title: path.basename(filePath),
        loader: "html"
    };
};
function fencedCode(language, value) {
    return `\`\`\`${language}\n${value}\n\`\`\``;
}
function csvRowsToMarkdown(rows) {
    if (rows.length === 0) {
        return "_Empty CSV file._";
    }
    const width = Math.max(...rows.map((row) => row.length));
    const normalized = rows.map((row) => Array.from({ length: width }, (_, index) => cellToMarkdown(row[index])));
    const header = normalized[0];
    const body = normalized.slice(1);
    return [
        `| ${header.join(" | ")} |`,
        `| ${header.map(() => "---").join(" | ")} |`,
        ...body.map((row) => `| ${row.join(" | ")} |`)
    ].join("\n");
}
function cellToMarkdown(value) {
    return String(value ?? "").replace(/\|/g, "\\|").replace(/\r?\n/g, " ").trim();
}

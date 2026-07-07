import { loadDoc } from "./loaders/doc.js";
import { loadDocx } from "./loaders/docx.js";
import { loadCaj } from "./loaders/caj.js";
import { loadPdf } from "./loaders/pdf.js";
import { loadCsv, loadHtml, loadJson, loadMarkdown, loadText } from "./loaders/text.js";
export const EXTENSION_TO_FORMAT = new Map([
    [".md", "markdown"],
    [".markdown", "markdown"],
    [".txt", "text"],
    [".json", "json"],
    [".csv", "csv"],
    [".html", "html"],
    [".htm", "html"],
    [".pdf", "pdf"],
    [".caj", "caj"],
    [".docx", "docx"],
    [".doc", "doc"]
]);
export const FORMAT_LOADERS = {
    markdown: loadMarkdown,
    text: loadText,
    json: loadJson,
    csv: loadCsv,
    html: loadHtml,
    pdf: loadPdf,
    caj: loadCaj,
    docx: loadDocx,
    doc: loadDoc
};
export const SUPPORTED_EXTENSIONS = [...EXTENSION_TO_FORMAT.keys()];

import { SUPPORTED_EXTENSIONS } from "./registry.js";
import type { LoadedDocument, LoaderContext, LoadResult, SmartLoaderOptions } from "./types.js";
export type * from "./types.js";
export { SUPPORTED_EXTENSIONS };
export { splitText } from "./chunk.js";
export declare function loadPath(inputPath: string, options?: SmartLoaderOptions): Promise<LoadResult>;
export declare function loadDirectory(dirPath: string, options?: SmartLoaderOptions): Promise<LoadResult>;
export declare function loadFile(filePath: string, contextOrOptions?: LoaderContext | SmartLoaderOptions): Promise<LoadedDocument>;

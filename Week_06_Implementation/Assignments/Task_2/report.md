# Repository chunking design

## Initial design and change

The first version split every text file into line-aware chunks of about 3,500 characters, with a 500-character overlap. That was a simple, language-independent baseline, but it could split code in the middle of a function and make retrieval less precise. We changed to a hybrid approach so chunks better match the structure of the repository.

## Current approach

- **Python:** use the built-in AST parser to create chunks for functions, methods, classes, class members, and module-level statements. Oversized units are split into bounded line chunks.
- **Markdown:** split at headings, keeping heading paths as metadata; oversized sections use the same bounded line splitting.
- **Other text files and unsupported Python syntax:** use line-based chunks with a 3,500-character target and 500-character overlap.

The script skips common generated, dependency, and version-control directories. Each JSON chunk records its repository-relative file path, kind, line range, text, and symbol when available. This metadata makes results easier to retrieve and trace to their source.

Using semantic boundaries for Python and Markdown should improve retrieval precision, while the line-based fallback keeps the script dependency-free and usable across the repository's other formats.

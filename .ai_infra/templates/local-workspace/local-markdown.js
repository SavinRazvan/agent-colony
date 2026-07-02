/**
 * File: local-markdown.js
 * Path: .ai_infra/templates/local-workspace/local-markdown.js
 * Role: Zero-dependency browser markdown renderer for local HTML dashboards.
 * Used By:
 *  - implementation-control-center.html
 * Depends On:
 *  - (none — pure DOM string output)
 * Notes:
 *  - Covers tables, blockquotes, lists, headings, code fences, and common inline marks.
 *  - Copy to `.local/agents-control-center/dashboards/` with other dashboard assets.
 */
(function (global) {
  "use strict";

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function parseInline(text) {
    let html = escapeHtml(text);
    const codeSpans = [];

    html = html.replace(/`([^`]+)`/g, function (_match, code) {
      const token = "@@CODE" + codeSpans.length + "@@";
      codeSpans.push("<code>" + code + "</code>");
      return token;
    });

    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (_match, label, href) {
      const safeHref = escapeHtml(href);
      return '<a href="' + safeHref + '" target="_blank" rel="noopener noreferrer">' + label + "</a>";
    });

    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/__([^_]+)__/g, "<strong>$1</strong>");
    html = html.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");
    html = html.replace(/~~([^~]+)~~/g, "<del>$1</del>");

    for (let i = 0; i < codeSpans.length; i += 1) {
      html = html.replace("@@CODE" + i + "@@", codeSpans[i]);
    }

    return html;
  }

  function isBlank(line) {
    return !line || !line.trim();
  }

  function isHtmlCommentStart(line) {
    return line.trim().startsWith("<!--");
  }

  function isFence(line) {
    return line.trim().startsWith("```");
  }

  function isTableRow(line) {
    const trimmed = line.trim();
    return trimmed.startsWith("|") && trimmed.includes("|", 1);
  }

  function isTableSeparator(line) {
    const trimmed = line.trim().replace(/^\|/, "").replace(/\|$/, "");
    if (!trimmed) {
      return false;
    }
    return trimmed.split("|").every(function (cell) {
      return /^:?-{3,}:?$/.test(cell.trim());
    });
  }

  function parseTableCells(line) {
    return line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map(function (cell) {
        return cell.trim();
      });
  }

  function renderTable(tableLines) {
    if (!tableLines.length) {
      return "";
    }

    const rows = tableLines.map(parseTableCells);
    let bodyStart = 1;
    if (rows.length > 1 && isTableSeparator(tableLines[1])) {
      bodyStart = 2;
    }

    const header = rows[0];
    const body = rows.slice(bodyStart);
    let html = "<table><thead><tr>";

    for (let c = 0; c < header.length; c += 1) {
      html += "<th>" + parseInline(header[c]) + "</th>";
    }
    html += "</tr></thead><tbody>";

    for (let r = 0; r < body.length; r += 1) {
      html += "<tr>";
      for (let c = 0; c < body[r].length; c += 1) {
        html += "<td>" + parseInline(body[r][c]) + "</td>";
      }
      html += "</tr>";
    }

    html += "</tbody></table>";
    return html;
  }

  function isHr(line) {
    return /^(\*{3,}|-{3,}|_{3,})\s*$/.test(line.trim());
  }

  function headingLevel(line) {
    const match = /^(#{1,6})\s+(.*)$/.exec(line);
    if (!match) {
      return 0;
    }
    return match[1].length;
  }

  function headingText(line) {
    const match = /^(#{1,6})\s+(.*)$/.exec(line);
    return match ? match[2] : "";
  }

  function listMatch(line) {
    const ul = /^(\s*)([-*+])\s+(.*)$/.exec(line);
    if (ul) {
      return { type: "ul", indent: ul[1].length, text: ul[3] };
    }
    const ol = /^(\s*)(\d+)\.\s+(.*)$/.exec(line);
    if (ol) {
      return { type: "ol", indent: ol[1].length, text: ol[3] };
    }
    return null;
  }

  function isBlockquote(line) {
    return /^>\s?/.test(line.trim());
  }

  function stripBlockquote(line) {
    return line.trim().replace(/^>\s?/, "");
  }

  function renderList(items) {
    if (!items.length) {
      return "";
    }

    let html = "";
    let openStack = [];

    function closeTo(indent) {
      while (openStack.length && openStack[openStack.length - 1].indent >= indent) {
        const node = openStack.pop();
        html += node.type === "ul" ? "</ul>" : "</ol>";
      }
    }

    for (let i = 0; i < items.length; i += 1) {
      const item = items[i];
      const indent = item.indent;

      if (!openStack.length || indent > openStack[openStack.length - 1].indent) {
        html += item.type === "ul" ? "<ul>" : "<ol>";
        openStack.push({ type: item.type, indent: indent });
      } else if (indent < openStack[openStack.length - 1].indent) {
        closeTo(indent + 1);
        if (!openStack.length || openStack[openStack.length - 1].indent !== indent) {
          html += item.type === "ul" ? "<ul>" : "<ol>";
          openStack.push({ type: item.type, indent: indent });
        }
      } else if (openStack[openStack.length - 1].type !== item.type) {
        closeTo(indent);
        html += item.type === "ul" ? "<ul>" : "<ol>";
        openStack.push({ type: item.type, indent: indent });
      }

      html += "<li>" + parseInline(item.text) + "</li>";
    }

    closeTo(-1);
    return html;
  }

  function renderMarkdown(md) {
    const lines = String(md).replace(/\r\n/g, "\n").split("\n");
    const out = [];
    let i = 0;

    while (i < lines.length) {
      const raw = lines[i];
      const line = raw.trimEnd();

      if (isHtmlCommentStart(line)) {
        i += 1;
        while (i < lines.length && !lines[i].includes("-->")) {
          i += 1;
        }
        i += 1;
        continue;
      }

      if (isFence(line)) {
        i += 1;
        const codeLines = [];
        while (i < lines.length && !isFence(lines[i].trimEnd())) {
          codeLines.push(lines[i]);
          i += 1;
        }
        if (i < lines.length) {
          i += 1;
        }
        out.push("<pre><code>" + escapeHtml(codeLines.join("\n")) + "</code></pre>");
        continue;
      }

      if (isBlank(line)) {
        i += 1;
        continue;
      }

      if (isHr(line)) {
        out.push("<hr />");
        i += 1;
        continue;
      }

      const level = headingLevel(line);
      if (level > 0) {
        out.push("<h" + level + ">" + parseInline(headingText(line)) + "</h" + level + ">");
        i += 1;
        continue;
      }

      if (isTableRow(line)) {
        const tableLines = [];
        while (i < lines.length && isTableRow(lines[i].trimEnd())) {
          tableLines.push(lines[i].trimEnd());
          i += 1;
        }
        out.push(renderTable(tableLines));
        continue;
      }

      if (isBlockquote(line)) {
        const quoteLines = [];
        while (i < lines.length && isBlockquote(lines[i].trimEnd())) {
          quoteLines.push(stripBlockquote(lines[i].trimEnd()));
          i += 1;
        }
        out.push("<blockquote>" + renderMarkdown(quoteLines.join("\n")) + "</blockquote>");
        continue;
      }

      const firstList = listMatch(line);
      if (firstList) {
        const listItems = [];
        while (i < lines.length) {
          const current = lines[i].trimEnd();
          const match = listMatch(current);
          if (match) {
            listItems.push(match);
            i += 1;
            continue;
          }
          if (isBlank(current) && i + 1 < lines.length && listMatch(lines[i + 1].trimEnd())) {
            i += 1;
            continue;
          }
          break;
        }
        out.push(renderList(listItems));
        continue;
      }

      const paraLines = [line];
      i += 1;
      while (i < lines.length) {
        const next = lines[i].trimEnd();
        if (
          isBlank(next) ||
          isFence(next) ||
          headingLevel(next) > 0 ||
          isTableRow(next) ||
          isBlockquote(next) ||
          listMatch(next) ||
          isHr(next) ||
          isHtmlCommentStart(next)
        ) {
          break;
        }
        paraLines.push(next);
        i += 1;
      }
      out.push("<p>" + parseInline(paraLines.join(" ")) + "</p>");
    }

    return out.join("\n");
  }

  global.LocalMarkdown = {
    render: renderMarkdown,
    escapeHtml: escapeHtml,
    parseInline: parseInline,
  };
})(typeof window !== "undefined" ? window : globalThis);

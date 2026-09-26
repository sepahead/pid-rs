-- PDF-only projection for audit/evidence/cross-implementation-reverification-2026-09-26.md.
-- The Markdown file is canonical. This filter changes layout and link form, not claims.

local dropped_title = false
local dropped_byline = false
local last_heading = ""
local repository_blob_root = "https://github.com/sepahead/pid-rs/blob/main/"
local source_directory = "audit/evidence/"
local report_title = "Cross-implementation re-verification of pid-rs estimators and mathematical results"

local function set_widths(element, widths)
  if #element.colspecs ~= #widths then
    return element
  end
  for index, colspec in ipairs(element.colspecs) do
    element.colspecs[index] = {colspec[1], widths[index]}
  end
  return element
end

-- Resolve a repository-relative target against the Markdown file's directory.
local function repository_path(target)
  local parts = {}
  for segment in (source_directory .. target):gmatch("[^/]+") do
    if segment == ".." then
      if #parts == 0 then
        error("link escapes the repository root: " .. target)
      end
      table.remove(parts)
    elseif segment ~= "." then
      table.insert(parts, segment)
    end
  end
  return table.concat(parts, "/")
end

function Header(element)
  local title = pandoc.utils.stringify(element.content)
  if not dropped_title and element.level == 1 and title == report_title then
    dropped_title = true
    return {}
  end
  if dropped_title and element.level > 1 then
    element.level = element.level - 1
  end
  last_heading = title
  if element.level == 1 then
    return {pandoc.RawBlock("latex", "\\par\\Needspace{14\\baselineskip}"), element}
  end
  if element.level == 2 then
    return {pandoc.RawBlock("latex", "\\par\\Needspace{10\\baselineskip}"), element}
  end
  return element
end

function Para(element)
  -- The title page carries the author and date; drop the duplicated Markdown byline.
  if not dropped_byline and dropped_title
      and pandoc.utils.stringify(element.content) == "Sepehr Mahmoudian · 26 September 2026" then
    dropped_byline = true
    return {}
  end
  return element
end

-- Let long code spans break after "::", "_" and "-" instead of stretching or overflowing lines.
local latex_replacements = {
  ["\\"] = "\\textbackslash{}", ["_"] = "\\_", ["{"] = "\\{", ["}"] = "\\}",
  ["#"] = "\\#", ["$"] = "\\$", ["&"] = "\\&", ["%"] = "\\%",
  ["~"] = "\\textasciitilde{}", ["^"] = "\\textasciicircum{}",
}

-- Escape every TeX special character in one pass so no replacement is escaped twice.
local function latex_escape(text)
  return (text:gsub("[\\_{}#$&%%~^]", latex_replacements))
end

function Code(element)
  if not FORMAT:match("latex") then
    return element
  end
  local text = element.text
  if not (text:find("::", 1, true) or #text > 24) then
    return element
  end
  local escaped = latex_escape(text)
  escaped = escaped:gsub("::", "::\\allowbreak{}")
  escaped = escaped:gsub("\\_", "\\_\\allowbreak{}")
  escaped = escaped:gsub("%-", "-\\allowbreak{}")
  return pandoc.RawInline("latex", "\\texttt{" .. escaped .. "}")
end

function Image(element)
  error("unexpected image in the cross-implementation re-verification report: " .. element.src)
end

function Link(element)
  if not FORMAT:match("latex") then
    return element
  end
  local target = element.target
  if target:match("^https?://") or target:match("^#") or target:match("^mailto:") then
    return element
  end
  -- Keep Markdown links repository-relative; give the PDF canonical repository navigation.
  element.target = repository_blob_root .. repository_path(target)
  return element
end


function Table(element)
  if not FORMAT:match("latex") then
    return element
  end
  local widths = nil
  local count = #element.colspecs
  if last_heading == "1.1 Checked objects" then
    widths = {0.16, 0.22, 0.24, 0.20, 0.18}
  elseif last_heading == "1.2 Evidence classes and independence" then
    widths = {0.16, 0.12, 0.72}
  elseif last_heading == "3.2 Results" and count == 4 then
    widths = {0.34, 0.22, 0.22, 0.22}
  elseif last_heading == "3.2 Results" or last_heading == "4.4 Method and results" then
    widths = {0.72, 0.28}
  elseif last_heading == "5. Complete test suite" then
    widths = {0.40, 0.20, 0.20, 0.20}
  elseif last_heading == "6.2 Exact-rational method and results" then
    widths = {0.55, 0.45}
  elseif last_heading == "6.3 Why the retired binary64 test reported ratios above one" then
    widths = {0.10, 0.26, 0.24, 0.18, 0.22}
  elseif last_heading == "9. Correction: intrinsic-dimension provenance" then
    widths = {0.32, 0.12, 0.56}
  elseif last_heading == "14.3 Results by package" then
    widths = {0.38, 0.49, 0.13}
  end
  if widths then
    return set_widths(element, widths)
  end
  if count == 2 then
    return set_widths(element, {0.30, 0.70})
  elseif count == 3 then
    return set_widths(element, {0.24, 0.38, 0.38})
  end
  return element
end

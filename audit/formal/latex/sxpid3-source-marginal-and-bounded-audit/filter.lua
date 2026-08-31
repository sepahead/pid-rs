-- Deterministic Pandoc projection for the SxPID3 audit PDF.
-- Markdown is canonical. The PDF drops only the duplicate body title and consumes PDF derivatives
-- of the two canonical SVG figures.

local dropped_title = false
local references_started = false
local repository_blob_root = "https://github.com/sepahead/pid-rs/blob/main/"

function Header(element)
  local title = pandoc.utils.stringify(element.content)
  local semantic_title = title:gsub("^%d+[%d%.]*%s+", "")
  if not dropped_title
      and element.level == 1
      and title
        == "Source-marginal factorization and a bounded exact audit of a declared categorical SxPID3 transcription" then
    dropped_title = true
    return {}
  end
  if dropped_title and element.level > 1 then
    element.level = element.level - 1
  end
  if semantic_title == "Abstract" then
    return {pandoc.RawBlock("latex", "\\clearpage"), element}
  end
  if semantic_title == "References" then
    references_started = true
    return {pandoc.RawBlock("latex", "\\Needspace{22\\baselineskip}"), element}
  end
  if semantic_title == "The 18/108/166 crosswalk" then
    return {pandoc.RawBlock("latex", "\\Needspace{18\\baselineskip}"), element}
  end
  if semantic_title == "Retained prohibited-transfer witness" then
    return {pandoc.RawBlock("latex", "\\Needspace{20\\baselineskip}"), element}
  end
  if semantic_title == "Exact finite-count formulation used by the bounded audit" then
    return {pandoc.RawBlock("latex", "\\Needspace{15\\baselineskip}"), element}
  end
  if semantic_title == "Formal, executable, and receipt evidence" then
    return {pandoc.RawBlock("latex", "\\Needspace{12\\baselineskip}"), element}
  end
  if semantic_title == "Explicit nonclaims and negative results" then
    return {pandoc.RawBlock("latex", "\\Needspace{5\\baselineskip}"), element}
  end
  if element.level == 1 or element.level == 2 then
    return {pandoc.RawBlock("latex", "\\Needspace{7\\baselineskip}"), element}
  end
  return element
end

function Para(element)
  local text = pandoc.utils.stringify(element.content)
  if text:match("^The source arity determines the carrier%.") then
    return {pandoc.RawBlock("latex", "\\Needspace{14\\baselineskip}"), element}
  end
  if text == "Thus" then
    return {pandoc.RawBlock("latex", "\\Needspace{5\\baselineskip}"), element}
  end
  if text == "Hence" then
    return {pandoc.RawBlock("latex", "\\Needspace{5\\baselineskip}"), element}
  end
  if text == "and" then
    return {pandoc.RawBlock("latex", "\\Needspace{5\\baselineskip}"), element}
  end
  if text:match("^With cumulatives as rows and atoms as columns, define") then
    return {pandoc.RawBlock("latex", "\\Needspace{11\\baselineskip}"), element}
  end
  if text:match("^and, for one fixed Möbius inverse") then
    return {pandoc.RawBlock("latex", "\\Needspace{7\\baselineskip}"), element}
  end
  if text:match("^For every component") then
    return {pandoc.RawBlock("latex", "\\Needspace{7\\baselineskip}"), element}
  end
  if text:match("^Standing assumptions for this counterexample%.") then
    return {pandoc.RawBlock("latex", "\\Needspace{14\\baselineskip}"), element}
  end
  if text:match("^Standing assumptions for the separate%-marginals counterexample%.") then
    return {pandoc.RawBlock("latex", "\\Needspace{12\\baselineskip}"), element}
  end
  if text:match("^For one fixed matrix") then
    return {pandoc.RawBlock("latex", "\\Needspace{5\\baselineskip}"), element}
  end
  if text:match("^Substitution into the three law%-level definitions") then
    return {pandoc.RawBlock("latex", "\\Needspace{12\\baselineskip}"), element}
  end
  if text:match("^For each cumulative, the exact positive%-rational products are") then
    return {pandoc.RawBlock("latex", "\\Needspace{15\\baselineskip}"), element}
  end
  if text:match("^Source inspection and hostile tests found") then
    return {pandoc.RawBlock("latex", "\\Needspace{13\\baselineskip}"), element}
  end
  if text:match("^The authoritative receipt is the source%-bound bounded%-audit receipt%.") then
    return {pandoc.RawBlock("latex", "\\Needspace{10\\baselineskip}"), element}
  end
  if text:match("^No new estimator is required to evaluate these deterministic identities") then
    return {pandoc.RawBlock("latex", "\\Needspace{13\\baselineskip}"), element}
  end
  if text:match("^The totals contribute respectively") then
    return {pandoc.RawBlock("latex", "\\Needspace{5\\baselineskip}"), element}
  end
  return element
end

function BulletList(element)
  if references_started then
    return {
      pandoc.RawBlock("latex", "\\begingroup\\interlinepenalty=10000"),
      element,
      pandoc.RawBlock("latex", "\\endgroup"),
    }
  end
  local text = pandoc.utils.stringify(element)
  if text:match("^The factorization does not extend in general") and #element.content >= 2 then
    local penultimate = element.content[#element.content - 1]
    table.insert(penultimate, 1, pandoc.RawBlock("latex", "\\Needspace{6\\baselineskip}"))
  end
  return element
end

function Image(element)
  if FORMAT:match("latex") and element.src:match("%.svg$") then
    element.src = element.src:gsub("%.svg$", ".pdf")
  end
  return element
end

function Link(element)
  if FORMAT:match("latex")
      and not element.target:match("^[A-Za-z][A-Za-z0-9+.-]*:")
      and not element.target:match("^#") then
    -- The canonical Markdown stays repository-relative. The PDF uses live GitHub navigation so
    -- readers do not need the original checkout layout. Exact evidence identity remains bound by
    -- the document's cited digests and immutable receipts, not by this mutable main URL.
    if element.target:match("^/")
        or element.target:match("^%./")
        or element.target:match("^%.%./") then
      error("noncanonical repository-relative link in SxPID3 audit source: " .. element.target)
    end
    element.target = repository_blob_root .. element.target
  end
  return element
end

function Table(element)
  if not FORMAT:match("latex") then
    return element
  end
  local count = #element.colspecs
  local widths = {}
  if count == 2 then
    widths = {0.66, 0.34}
  elseif count == 3 then
    widths = {0.13, 0.24, 0.63}
  elseif count == 4 then
    widths = {0.27, 0.18, 0.18, 0.37}
  elseif count == 5 then
    widths = {0.38, 0.155, 0.155, 0.155, 0.155}
  else
    for index = 1, count do
      widths[index] = 1.0 / count
    end
  end
  for index, colspec in ipairs(element.colspecs) do
    element.colspecs[index] = {colspec[1], widths[index]}
  end
  return element
end

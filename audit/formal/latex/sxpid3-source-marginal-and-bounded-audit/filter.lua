-- Deterministic Pandoc projection for the SxPID3 audit PDF.
-- Markdown is canonical. The PDF drops only the duplicate body title and consumes PDF derivatives
-- of the two canonical SVG figures.

local dropped_title = false

function Header(element)
  if not dropped_title
      and element.level == 1
      and pandoc.utils.stringify(element.content)
        == "Source-marginal factorization and a bounded exact audit of a declared categorical SxPID3 transcription" then
    dropped_title = true
    return {}
  end
  if dropped_title and element.level > 1 then
    element.level = element.level - 1
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
      and not element.target:match("^#")
      and not element.target:match("^%.%./%.%./") then
    -- The canonical Markdown lives at the repository root, while the committed PDF lives under
    -- output/pdf. Keep root-relative Markdown links usable on Git hosts and project them into the
    -- PDF's two-level-relative link domain only during rendering.
    element.target = "../../" .. element.target
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

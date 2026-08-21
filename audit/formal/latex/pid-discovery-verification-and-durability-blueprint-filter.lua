-- Deterministic Pandoc projection for the human PDF.
-- Markdown remains the canonical narrative; the PDF drops only the duplicate body title and
-- consumes vector-PDF derivatives of the two canonical SVG figures.

local dropped_title = false

function Header(element)
  if not dropped_title
      and element.level == 1
      and pandoc.utils.stringify(element.content)
        == "PID discovery, verification, and durability blueprint" then
    dropped_title = true
    return {}
  end
  -- The dropped body title is the Markdown parent of every report section.  Shift its children
  -- up exactly one level so the PDF has real top-level sections rather than orphaned 0.x
  -- subsections.  The canonical Markdown hierarchy remains unchanged.
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

function Table(element)
  if not FORMAT:match("latex") then
    return element
  end
  local count = #element.colspecs
  local widths = nil
  local first_header = ""
  if element.head and element.head.rows and #element.head.rows > 0
      and #element.head.rows[1].cells > 0 then
    first_header = pandoc.utils.stringify(element.head.rows[1].cells[1].contents)
  end
  if count == 2 then
    widths = {0.30, 0.70}
  elseif count == 3 then
    widths = {0.20, 0.38, 0.42}
  elseif count == 4 and first_header == "Program" then
    widths = {0.13, 0.17, 0.34, 0.36}
  elseif count == 4 then
    widths = {0.06, 0.16, 0.36, 0.42}
  else
    widths = {}
    for index = 1, count do
      widths[index] = 1.0 / count
    end
  end
  for index, colspec in ipairs(element.colspecs) do
    element.colspecs[index] = {colspec[1], widths[index]}
  end
  return element
end

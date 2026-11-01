-- Typesetting only: title/byline are supplied by the wrapper.
function Pandoc(doc)
  local b = doc.blocks
  if b[1].t ~= "Header" or b[1].level ~= 1 then error("missing source title") end
  if pandoc.utils.stringify(b[2]) ~= "Sepehr Mahmoudian · 24 October 2026, revised 31 October 2026" then
    error("unexpected source byline")
  end
  b:remove(1)
  b:remove(1)
  for _,block in ipairs(b) do
    if block.t == "Header" then block.level = block.level - 1 end
  end
  doc.blocks = b
  return doc
end
-- A PDF leaves the repository, so every relative link becomes an absolute repository URL.
-- The source lives in audit/research/source-coupling-compression; a link that would leave
-- the repository root is an error.
local BASE = {"audit", "research", "source-coupling-compression"}
local REPOSITORY = "https://github.com/sepahead/pid-rs/blob/main/"

local function absolute(target)
  if target:match("^%a[%w+.-]*:") then
    return target
  end
  local path, fragment = target:match("^([^#]*)(#?.*)$")
  if path == "" then
    error("unexpected fragment-only link: " .. target)
  end
  local parts = {}
  for _, part in ipairs(BASE) do
    parts[#parts + 1] = part
  end
  for part in path:gmatch("[^/]+") do
    if part == ".." then
      if #parts == 0 then
        error("relative link leaves the repository: " .. target)
      end
      table.remove(parts)
    elseif part ~= "." then
      parts[#parts + 1] = part
    end
  end
  return REPOSITORY .. table.concat(parts, "/") .. fragment
end

function Link(el)
  el.target = absolute(el.target)
  return el
end

-- The Markdown shows each figure through its SVG companion, which GitHub can display; the PDF
-- uses the vector PDF of the same figure. Inline elements are filtered before blocks, so the
-- image source is already the PDF when Figure writes the LaTeX.
function Image(el)
  local stem = el.src:match("^figures/(.+)%.svg$")
  if stem then
    el.src = "figures/" .. stem .. ".pdf"
  end
  return el
end

-- GitHub renders a display formula that carries \tag as a stacked table, so the Markdown writes
-- an equation number as \qquad(N) at the end of the display; the PDF sets it as \tag{N}.
function Math(el)
  if el.mathtype == "DisplayMath" then
    el.text = el.text:gsub("\\qquad%((%d+)%)(%s*)$", "\\tag{%1}%2")
  end
  return el
end

function Figure(fig)
  local image = pandoc.write(pandoc.Pandoc(fig.content), "latex")
  local caption = pandoc.write(pandoc.Pandoc(fig.caption.long), "latex")
  return pandoc.RawBlock("latex", "\\begin{figure}[H]\n\\centering\n" ..
    image .. "\n\\caption{" .. caption .. "}\n\\end{figure}")
end

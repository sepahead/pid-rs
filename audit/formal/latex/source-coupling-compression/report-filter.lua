-- Typesetting only: title/byline are supplied by the wrapper.
function Pandoc(doc)
  local b = doc.blocks
  if b[1].t ~= "Header" or b[1].level ~= 1 then error("missing source title") end
  if pandoc.utils.stringify(b[2]) ~= "Sepehr Mahmoudian · 24 October 2026" then
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
function Link(el)
  -- A PDF leaves the repository, so its links are absolute.
  if el.target == "../../../CITATION.cff" then
    el.target = "https://github.com/sepahead/pid-rs/blob/main/CITATION.cff"
  elseif el.target == "summary.csv" then
    el.target = "https://github.com/sepahead/pid-rs/blob/main/audit/research/source-coupling-compression/summary.csv"
  end
  return el
end

function Figure(fig)
  local image = pandoc.write(pandoc.Pandoc(fig.content), "latex")
  local caption = pandoc.write(pandoc.Pandoc(fig.caption.long), "latex")
  return pandoc.RawBlock("latex", "\\begin{figure}[H]\n\\centering\n" ..
    image .. "\n\\caption{" .. caption .. "}\n\\end{figure}")
end

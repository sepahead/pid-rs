-- Source-to-LaTeX filter for the finite target-copy MGW paper.
function Header(e)
  if e.level == 1 then return {} end
  e.level = e.level - 1
  return {pandoc.RawBlock("latex", "\\par\\Needspace{6\\baselineskip}"), e}
end
function Para(e)
  -- Keep this short introduction with the target-mass display that follows it.
  if pandoc.utils.stringify(e) == "write" then
    return {pandoc.RawBlock("latex", "\\Needspace{5\\baselineskip}"), e}
  end
end
function Image(e)
  if not e.src:match("mgw%-target%-copy/event%-union%.svg$") then error("unexpected image") end
  e.src = "event-union.pdf"; e.attributes.width = "100%"; return e
end
function Link(e)
  if e.target:match("^https://") or e.target:match("^#") then return e end
  local target = e.target
  if target:match("^%.%./") then target = "audit/" .. target:gsub("^%.%./", "") end
  if not target:match("^audit/") then target = "audit/evidence/" .. target end
  if target:match("^audit/") and not target:match("%.%.") then
    e.target = "https://github.com/sepahead/pid-rs/blob/main/" .. target; return e
  end
  error("unmapped repository link: " .. e.target)
end
function Table(e)
  local n = #e.colspecs; local widths = nil
  if n == 4 then widths = {0.23,0.22,0.23,0.32}
  elseif n == 2 then widths = {0.37,0.63} end
  if widths then for i,c in ipairs(e.colspecs) do e.colspecs[i] = {c[1], widths[i]} end end
  local latex = pandoc.write(pandoc.Pandoc({e}), "latex", PANDOC_WRITER_OPTIONS)
  latex = latex:gsub("\\\\\n", "\\\\*\n"):gsub("\\endlastfoot", "\\endfoot")
  return pandoc.RawBlock("latex", latex)
end

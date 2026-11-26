-- Rewrite only parsed Markdown links. The study's TeX math stays literal.
function Link(el)
  if el.target:match("^https://") then return el end
  if not el.target:match("^[%w_/%-%.]+$") or el.target:sub(1, 1) == "/" then
    error("unexpected relative publication link: " .. el.target)
  end
  local parts = {"audit", "research", "dendritic-stimulus-resolution"}
  for piece in el.target:gmatch("[^/]+") do
    if piece == ".." then
      if #parts == 0 then error("link outside repository") end
      table.remove(parts)
    elseif piece ~= "." then
      table.insert(parts, piece)
    end
  end
  local kind = el.target == "cases" and "tree" or "blob"
  el.target = "https://github.com/sepahead/pid-rs/" .. kind .. "/main/" .. table.concat(parts, "/")
  return el
end

-- Permit line breaks in a fixed hexadecimal identity and in long Rust module names.
function Code(el)
  if el.text:match("^[%w_./:%-]+$") then
    return pandoc.RawInline("latex", "\\nolinkurl{" .. el.text .. "}")
  end
  return el
end

-- Allocate space to the labels and enough room for each numeric value.
function Table(tbl)
  local n = #tbl.colspecs
  local first = pandoc.utils.stringify(tbl.head.rows[1].cells[1].contents)
  local widths
  if n == 2 then widths = {0.27, 0.73}
  elseif n == 7 then widths = {0.10, 0.15, 0.105, 0.105, 0.165, 0.15, 0.225}
  elseif n == 5 and first == "Width" then widths = {0.09, 0.17, 0.24, 0.25, 0.25}
  elseif n == 5 then widths = {0.36, 0.16, 0.16, 0.16, 0.16}
  end
  if widths then
    local specs = {}
    for i, width in ipairs(widths) do specs[i] = {tbl.colspecs[i][1], width} end
    tbl.colspecs = specs
  end
  return tbl
end

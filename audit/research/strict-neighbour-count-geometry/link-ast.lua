-- Rewrite only parsed Markdown links. The study's TeX math stays literal.
function Link(el)
  if el.target:match("^https://") then return el end
  if not el.target:match("^[%w_/%-%.]+$") or el.target:sub(1, 1) == "/" then
    error("unexpected relative publication link: " .. el.target)
  end
  local parts = {"audit", "research", "strict-neighbour-count-geometry"}
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

-- Typeset two comparison symbols as mathematics. Split the public Rust path
-- only at existing separators so that a line break never changes the name.
function Code(el)
  if el.text == "≤" then return pandoc.Math("InlineMath", "\\le") end
  if el.text == "<" then return pandoc.Math("InlineMath", "<") end
  if el.text == "pid_core::experimental::continuous::isx_redundancy_report" then
    return pandoc.RawInline("latex", "\\newline{}\\texttt{pid\\_core::experimental::continuous::isx\\_redundancy\\_report}\\newline{}")
  end
  return el
end

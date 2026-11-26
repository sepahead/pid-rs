-- Rewrite only parsed Markdown links. The study's TeX math stays literal.
function Link(el)
  if el.target:match("^https://") then return el end
  if not el.target:match("^[%w_/%-%.]+$") or el.target:sub(1, 1) == "/" then
    error("unexpected relative publication link: " .. el.target)
  end
  local parts = {"audit", "research", "nested-categorical-sources"}
  for piece in el.target:gmatch("[^/]+") do
    if piece == ".." then
      if #parts == 0 then error("link outside repository") end
      table.remove(parts)
    elseif piece ~= "." then
      table.insert(parts, piece)
    end
  end
  el.target = "https://github.com/sepahead/pid-rs/blob/main/" .. table.concat(parts, "/")
  return el
end

-- Presentation-only projection of the recorded sensor Markdown.
local section = ""
function Header(e)
  if e.level == 1 then return {} end
  e.level = e.level - 1
  section = pandoc.utils.stringify(e.content)
  local reserve = e.level == 1 and "14" or "10"
  return {pandoc.RawBlock("latex", "\\par\\Needspace{" .. reserve .. "\\baselineskip}"), e}
end
function Image(e)
  local name = e.src:match("([^/]+)%.svg$")
  if not name or (name ~= "recording-roles" and name ~= "signed-cancellation") then
    error("unexpected publication image")
  end
  e.src = name .. ".pdf"
  e.attributes.width = "100%"
  return e
end
function Code(e)
  -- Keep decimal witnesses intact; other code retains its existing wrapping.
  if e.text:match("^[0-9]+%.[0-9]+$") then
    return pandoc.RawInline("latex", "\\mbox{\\PidSavedTexttt{" .. e.text .. "}}")
  end
  -- Only canonical nonnegative decimal lists, as used by the two bin-edge lists.
  local inner = e.text:match("^%[(.*)%]$")
  if not inner then return e end
  local values = {}
  for token in inner:gmatch("[^, ]+") do
    if not token:match("^%d+%.?%d*$") then return e end
    values[#values + 1] = token
  end
  if #values < 2 or table.concat(values, ", ") ~= inner then return e end
  local pieces = {}
  for i, value in ipairs(values) do
    local left = i == 1 and "[" or ""
    local right = i == #values and "]" or ","
    pieces[i] = "\\mbox{\\PidSavedTexttt{" .. left .. value .. right .. "}}"
  end
  return pandoc.RawInline("latex", table.concat(pieces, "\\allowbreak\\space "))
end
function Link(e)
  if e.target:match("^https://") or e.target:match("^#") then return e end
  local path
  if e.target:match("^%.%./%.%./") then
    path = e.target:sub(7)
  elseif e.target:match("^%.%./formal/") then
    path = "audit/formal/" .. e.target:sub(11)
  elseif e.target:match("^real%-occupancy%-sensors%-example%-2026%-09%-08/") then
    path = "audit/evidence/" .. e.target
  else
    error("unmapped repository link: " .. e.target)
  end
  if path:match("^/") or path:find("..", 1, true) or path:find(":", 1, true) then
    error("unsafe repository navigation path")
  end
  e.target = "https://github.com/sepahead/pid-rs/blob/main/" .. path
  return e
end
function Table(e)
  local n = #e.colspecs
  local widths = nil
  if section == "Data and roles" and n == 5 then
    widths = {0.16,0.17,0.10,0.43,0.14}
  elseif section == "Data and roles" and n == 4 then
    widths = {0.25,0.25,0.25,0.25}
  elseif n == 7 then
    widths = {0.19,0.13,0.13,0.14,0.14,0.14,0.13}
  elseif n == 6 then
    widths = {0.20,0.16,0.16,0.16,0.16,0.16}
  elseif n == 4 then
    widths = {0.22,0.30,0.29,0.19}
  end
  if widths then
    for i,c in ipairs(e.colspecs) do e.colspecs[i] = {c[1],widths[i]} end
  end
  -- These eight source tables have at most eight body rows; review final page fit.
  -- Keep Pandoc's cell/column/caption projection; only forbid inter-row breaks.
  local latex = pandoc.write(pandoc.Pandoc({e}), "latex", PANDOC_WRITER_OPTIONS)
  latex = latex:gsub("\\\\\n", "\\\\*\n")
  -- Reserve the bottom rule with the body, rather than a separable last footer.
  latex = latex:gsub("\\endlastfoot", "\\endfoot")
  return pandoc.RawBlock("latex", latex)
end

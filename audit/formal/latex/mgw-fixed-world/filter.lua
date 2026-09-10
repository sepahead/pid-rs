-- Presentation projection; preserves all mathematical source content.
local section = ""
function Header(e)
  if e.level == 1 then return {} end
  section = pandoc.utils.stringify(e.content)
  e.level = e.level - 1
  return {pandoc.RawBlock("latex", "\\par\\Needspace{12\\baselineskip}"), e}
end
function Image(e)
  local name = e.src:match("([^/]+)%.svg$")
  local allowed = { ["observation-maps"]=true, ["shared-exclusion-events"]=true, ["mgw-matched-comparison"]=true }
  if not allowed[name] then error("unexpected publication image") end
  e.src = name .. ".pdf"
  e.attributes.width = "100%"
  return e
end
function Link(e)
  if e.target:match("^https://") or e.target:match("^#") then return e end
  if e.target:match("^%.%./formal/lean%-mgw%-fixed%-world/PidMgwFixedWorld/") then
    e.target = "https://github.com/sepahead/pid-rs/blob/main/audit/formal/lean-mgw-fixed-world/PidMgwFixedWorld/" .. e.target:match("([^/]+)$")
  elseif e.target == "../formal/lean-mgw-fixed-world/LATER_EXECUTION.json" or e.target == "../formal/lean-mgw-fixed-world/EVIDENCE.md" then
    e.target = "https://github.com/sepahead/pid-rs/blob/main/audit/formal/lean-mgw-fixed-world/" .. e.target:match("([^/]+)$")
  elseif e.target:match("^mgw%-fixed%-world%-added%-information%-2026%-09%-09/") then
    e.target = "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/" .. e.target
  elseif e.target:match("^real%-occupancy%-sensors%-example%-2026%-09%-08") then
    e.target = "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/" .. e.target
  elseif e.target == "../../METHODS.md" then
    e.target = "https://github.com/sepahead/pid-rs/blob/main/METHODS.md"
  else error("unmapped repository link: " .. e.target) end
  return e
end
function Table(e)
  local n = #e.colspecs
  local widths
  if n == 5 and section == "One world and two observation maps" then
    local first = pandoc.utils.stringify(e.head.rows[1].cells[1].contents)
    if first:match("World") then widths={0.22,0.13,0.17,0.24,0.24}
    else widths={0.36,0.16,0.16,0.16,0.16} end
  elseif n == 6 then widths={0.14,0.20,0.165,0.165,0.165,0.165}
  elseif n == 4 then widths={0.16,0.26,0.29,0.29}
  elseif n == 3 then
    if section == "Retained unsuccessful routes and limits" then widths={0.22,0.42,0.36}
    else widths={0.40,0.30,0.30} end
  elseif n == 2 then widths={0.18,0.82} end
  if widths then for i,c in ipairs(e.colspecs) do e.colspecs[i]={c[1],widths[i]} end end
  local latex=pandoc.write(pandoc.Pandoc({e}),"latex",PANDOC_WRITER_OPTIONS)
  latex=latex:gsub("\\\\\n","\\\\*\n"):gsub("\\endlastfoot","\\endfoot")
  return pandoc.RawBlock("latex",latex)
end

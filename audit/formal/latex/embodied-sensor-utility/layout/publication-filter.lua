-- Fixed embodied full/overview projection; reference acceptance is caller-owned.
local titles = {full = "Sensor information for embodied agents", overview = "Wibral-line PID for physical intelligence"}
local base = "https://github.com/sepahead/pid-rs/blob/main/"
local local_links = {
  ["../../formal/lean-finite-logscore/PUBLICATION.md"] = "audit/formal/lean-finite-logscore/PUBLICATION.md",
  ["../../../audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md"] = "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md",
  ["../../../scripts/check-primegaps-to-pid-transfer-ledger.py"] = "scripts/check-primegaps-to-pid-transfer-ledger.py",
  ["../../../PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md"] = "PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md",
  ["../../../CITATION.cff"] = "CITATION.cff",
  ["../../../ECOSYSTEM_CAPABILITIES.md"] = "ECOSYSTEM_CAPABILITIES.md",
  ["../../../MATHEMATICAL_RESULTS_GUIDE.md"] = "MATHEMATICAL_RESULTS_GUIDE.md",
  ["../../../PID_ALTERNATIVES_AND_INCREMENTAL_VALUE.md"] = "PID_ALTERNATIVES_AND_INCREMENTAL_VALUE.md",
  ["../../../PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md"] = "PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md",
  ["../../../crates/pid-core/benches/estimators.rs"] = "crates/pid-core/benches/estimators.rs",
  ["../../../crates/pid-core/src/lib.rs"] = "crates/pid-core/src/lib.rs",
  ["../../../crates/pid-core/src/sxpid.rs"] = "crates/pid-core/src/sxpid.rs",
  ["../finite-prefix-mgw-gradient/EXPOSITION.md"] = "audit/research/finite-prefix-mgw-gradient/EXPOSITION.md",
  ["../support-change-mi-cusp/EXPOSITION.md"] = "audit/research/support-change-mi-cusp/EXPOSITION.md",
  ["EXPOSITION.md"] = "output/pdf/embodied-sensor-utility.pdf",
  ["EXPOSITION.md#13-rust-implementation-and-computational-cost"] = "audit/research/embodied-sensor-utility/EXPOSITION.md#13-rust-implementation-and-computational-cost",
}
local external_links = {
  ["https://arxiv.org/abs/1510.00831v1"] = true,
  ["https://arxiv.org/abs/2002.03356v5"] = true,
  ["https://arxiv.org/abs/2302.11813"] = true,
  ["https://arxiv.org/abs/2311.06373v3"] = true,
  ["https://doi.org/10.1080/01621459.1963.10500830"] = true,
  ["https://doi.org/10.1103/PhysRevE.103.032149"] = true,
  ["https://doi.org/10.1198/016214506000001437"] = true,
  ["https://proceedings.mlr.press/v270/skand25a.html"] = true,
  ["https://proceedings.mlr.press/v305/almuzairee25a.html"] = true,
}
local figure_map = {
  ["figures/sensor-data-to-evidence.svg"] = "figures/sensor-data-to-evidence.pdf",
  ["figures/signed-atoms-and-sensor-value.svg"] = "figures/signed-atoms-and-sensor-value.pdf",
  ["figures/availability-weighted-gain.svg"] = "figures/availability-weighted-gain.pdf",
}
local kind, h1_count, images
local function metadata(meta)
  if FORMAT ~= "latex" then error("Only the declared LaTeX route is supported") end
  kind = pandoc.utils.stringify(meta["publication-kind"])
  if not titles[kind] or pandoc.utils.stringify(meta.title) ~= titles[kind] then error("Title/kind mismatch") end
  h1_count, images = 0, {}
  return meta
end
local function header(element)
  if element.level == 1 then
    h1_count = h1_count + 1
    if pandoc.utils.stringify(element.content) ~= titles[kind] then error("Source title/kind mismatch") end
    return {}
  end
  element.level = element.level - 1
  return {pandoc.RawBlock('latex','\\par\\Needspace{10\\baselineskip}'), element}
end
local function link(element)
  if external_links[element.target] then return element end
  local relative = local_links[element.target]
  if not relative then error("Unmapped publication link: " .. element.target) end
  element.target = base .. relative
  return element
end
local function image(element)
  local destination = figure_map[element.src]
  if not destination or (kind == "overview" and element.src ~= "figures/signed-atoms-and-sensor-value.svg") then error("Unmapped publication image: " .. element.src) end
  if images[element.src] then error("Repeated publication image") end
  images[element.src] = true
  element.src = destination
  element.attributes.width = "160mm"
  return element
end
function Table(e)
  local n=#e.colspecs
  local widths=({[2]={.35,.65},[3]={.28,.32,.40},[4]={.11,.29,.25,.35},[6]={.26,.10,.12,.12,.10,.30}})[n]
  if widths then for i,c in ipairs(e.colspecs) do e.colspecs[i]={c[1],widths[i]} end end
  -- A table is a fragment. Fresh options avoid inherited standalone state.
  local options=pandoc.WriterOptions{wrap_text='none'}
  local latex=pandoc.write(pandoc.Pandoc({e}),'latex',options)
  if latex:find('\\documentclass',1,true) or latex:find('\\begin{document}',1,true) then error('Table writer returned a complete document') end
  latex=latex:gsub('\\\\\n','\\\\*\n'):gsub('\\endlastfoot','\\endfoot')
  return pandoc.RawBlock('latex',latex)
end

-- Two long definitions are displayed to avoid an unbreakable inline formula.
function Math(e)
  local display={
    ['H(Y\\mid O)=\\sum_{o:P(o)>0}P(o)H(P(\\cdot\\mid o))']=true,
    ['I(Y;V\\mid O)=H(Y\\mid O)-H(Y\\mid O,V)']=true}
  if e.mathtype=='InlineMath' and display[e.text] then return pandoc.Math('DisplayMath',e.text) end
  return e
end

function Para(e)
  for i,x in ipairs(e.content) do
    if x.t=='Math' and x.mathtype=='DisplayMath' and (x.text=='H(Y\\mid O)=\\sum_{o:P(o)>0}P(o)H(P(\\cdot\\mid o))' or x.text=='I(Y;V\\mid O)=H(Y\\mid O)-H(Y\\mid O,V)') then
      local next=e.content[i+1]
      if next and next.t=='Str' and next.text:sub(1,1)=='.' then x.text=x.text..'.';next.text=next.text:sub(2) end
    end
  end
  return e
end
function Code(e)
  local map={['\\']='\\textbackslash{}',['{']='\\{',['}']='\\}',['_']='\\_',['%']='\\%',['$']='\\$',['#']='\\#',['&']='\\&',['~']='\\textasciitilde{}',['^']='\\textasciicircum{}'}
  local out={};local i=1
  while i<=#e.text do
    if e.text:sub(i,i+1)=='::' then table.insert(out,'::\\allowbreak{}');i=i+2
    else local c=e.text:sub(i,i);table.insert(out,map[c] or c);if c=='_' or c=='.' or c=='/' then table.insert(out,'\\allowbreak{}') end;i=i+1 end
  end
  return pandoc.RawInline('latex','\\texttt{'..table.concat(out)..'}')
end

local function complete(document)
  if h1_count ~= 1 then error("Exactly one source title is required") end
  local count = 0
  for _ in pairs(images) do count = count + 1 end
  if count ~= (kind == "full" and 3 or 1) then error("Publication image inventory differs") end
  return document
end
return {
  {Meta = metadata},
  {Header = header, Link = link, Image = image},
  {Table = Table, Math = Math, Code = Code},
  {Para = Para},
  {Pandoc = complete}
}

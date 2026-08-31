-- Deterministic Pandoc projection for the human PDF.
-- Markdown remains the canonical narrative; the PDF drops only the duplicate body title and
-- consumes vector-PDF derivatives of four canonical SVG figure panels.  It also rewrites the
-- declared repository-document links to canonical GitHub main-branch navigation URLs for the
-- standalone PDF while leaving the Markdown targets relative.  The panel split makes the two dense
-- diagrams readable at print size.  Neither projection changes a scientific claim.

local dropped_title = false
local github_navigation_links = {
  ["claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md"] =
    "https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md",
  ["claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md"] =
    "https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md",
  ["claims/SX-CERTIFIED-AVERAGED-PID3-001/revision-index.md"] =
    "https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/revision-index.md",
  ["claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier"] =
    "https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier",
}
local figure_panels = {
  ["semantic-transfer-firewall-source-card.pdf"] = {
    "Semantic transfer firewall, part 1: source meaning and the required transfer card.",
    "Source meaning and transfer-card fields are separated before any PID analogue is considered."
  },
  ["semantic-transfer-firewall-pid-card.pdf"] = {
    "Semantic transfer firewall, part 2: the PID-specific assurance route and nontransfer boundary.",
    "The PID pilot and promotion evidence remain separate from prohibited transfers of prime-gap conclusions."
  },
  ["durable-promotion-state-machine-stages.pdf"] = {
    "Durable promotion state machine, part 1: the seven ordered stages from discovery through retirement.",
    "Numbered stages show that retirement follows verification rather than replacing it."
  },
  ["durable-promotion-state-machine-storage.pdf"] = {
    "Durable promotion state machine, part 2: the storage and promotion paths and retirement gate.",
    "Availability, acceptance, and recoverability are distinct; every retirement condition must hold."
  },
}

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

function Link(element)
  if FORMAT:match("latex") then
    local replacement = github_navigation_links[element.target]
    if replacement ~= nil then
      element.target = replacement
    end
  end
  return element
end

function Para(element)
  if not FORMAT:match("latex") or #element.content ~= 1 then
    return element
  end
  local image = element.content[1]
  if image.t ~= "Image" then
    return element
  end
  local basename = image.src:match("([^/]+)$")
  local panel = figure_panels[basename]
  if panel == nil then
    return element
  end
  return pandoc.RawBlock(
    "latex",
    "\\PidBlueprintFigure{" .. image.src .. "}{" .. panel[2] .. "}{" .. panel[1] .. "}"
  )
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
  elseif count == 3 and first_header == "#" then
    widths = {0.06, 0.22, 0.72}
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

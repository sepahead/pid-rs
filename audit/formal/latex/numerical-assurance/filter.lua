-- PDF-only projection for NUMERICAL_ASSURANCE.md.
-- Markdown and SVG are canonical. This filter changes layout, not claims.

local dropped_title = false
local last_heading = ""
local repository_blob_root = "https://github.com/sepahead/pid-rs/blob/main/"

local function set_widths(element, widths)
  if #element.colspecs ~= #widths then
    return element
  end
  for index, colspec in ipairs(element.colspecs) do
    element.colspecs[index] = {colspec[1], widths[index]}
  end
  return element
end

function Header(element)
  local title = pandoc.utils.stringify(element.content)
  if not dropped_title and element.level == 1
      and title == "Represented-Binary64 Assurance for PID Reconstruction and Quantization" then
    dropped_title = true
    return {}
  end
  if dropped_title and element.level > 1 then
    element.level = element.level - 1
  end
  last_heading = title
  if title == "Object card, provenance, and novelty" then
    return {pandoc.RawBlock("latex", "\\clearpage"), element}
  end
  if element.level == 1 then
    return {pandoc.RawBlock("latex", "\\Needspace{15\\baselineskip}"), element}
  end
  if element.level == 2 then
    return {pandoc.RawBlock("latex", "\\Needspace{11\\baselineskip}"), element}
  end
  return element
end

function Image(element)
  if FORMAT:match("latex") and element.src:match("%.svg$") then
    local figure_dir = os.getenv("PID_NUMERICAL_FIGURE_PDF_DIR")
    if not figure_dir or figure_dir == "" then
      error("PID_NUMERICAL_FIGURE_PDF_DIR is required for PDF projection")
    end
    local basename = element.src:match("([^/]+)%.svg$")
    if not basename then
      error("cannot derive figure basename: " .. element.src)
    end
    element.src = figure_dir .. "/" .. basename .. ".pdf"
  end
  return element
end

function Link(element)
  if FORMAT:match("latex")
      and element.target == "PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md" then
    -- Keep the canonical Markdown link repository-relative, but make its PDF projection usable
    -- after download and through GitHub's viewer. This is live navigation, not an immutable
    -- provenance identity.
    element.target = repository_blob_root .. element.target
  end
  return element
end

function Para(element)
  if FORMAT:match("latex")
      and pandoc.utils.stringify(element.content)
        == "The separate exact-ratio sign certificate uses:" then
    return {
      pandoc.RawBlock("latex", "\\Needspace{7\\baselineskip}"),
      element,
    }
  end
  return element
end

function Table(element)
  if not FORMAT:match("latex") then
    return element
  end
  local widths = nil
  if last_heading == "Object card, provenance, and novelty" then
    widths = {0.24, 0.76}
  elseif last_heading == "4. Reproducible counterexamples" then
    widths = {0.14, 0.30, 0.56}
  elseif last_heading == "8.1 Twelve materially distinct routes considered" then
    widths = {0.22, 0.27, 0.51}
  elseif last_heading == "8.2 Fifty-lens hostile review" then
    widths = {0.05, 0.22, 0.73}
  elseif last_heading == "9. Real-world use" then
    widths = {0.04, 0.20, 0.25, 0.28, 0.23}
  elseif last_heading == "12.2 Reproduction and implementation map" then
    widths = {0.29, 0.71}
  end
  if widths then
    return set_widths(element, widths)
  end
  local count = #element.colspecs
  if count == 2 then
    return set_widths(element, {0.30, 0.70})
  elseif count == 3 then
    return set_widths(element, {0.24, 0.38, 0.38})
  elseif count == 4 then
    return set_widths(element, {0.20, 0.26, 0.27, 0.27})
  end
  return element
end

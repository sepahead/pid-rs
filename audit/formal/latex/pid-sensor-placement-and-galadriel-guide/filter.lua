-- PDF-only projection for PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md.
-- Markdown and SVG are canonical. This filter changes layout, not claims.

local dropped_title = false
local dropped_subtitle = false
local last_heading = ""

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
      and title == "PID in Galadriel and sensor placement" then
    dropped_title = true
    return {}
  end
  if dropped_title and not dropped_subtitle and element.level == 2
      and title == "Current use, proposed research, and evidence gates" then
    dropped_subtitle = true
    return {}
  end
  if dropped_title and element.level > 1 then
    element.level = element.level - 1
  end
  last_heading = title
  if element.level == 1 then
    if title == "10. Formal verification and oracle design"
      or title == "11. Benchmark against established methods"
      or title == "14. Positive results, negative results, and open work"
      or title == "15. Conclusion" then
      return {pandoc.RawBlock("latex", "\\Needspace{15\\baselineskip}"), element}
    end
    return {pandoc.RawBlock("latex", "\\clearpage"), element}
  end
  if element.level == 2 then
    return {pandoc.RawBlock("latex", "\\Needspace{11\\baselineskip}"), element}
  end
  return element
end

function Image(element)
  if FORMAT:match("latex") and element.src:match("%.svg$") then
    local figure_dir = os.getenv("PID_GUIDE_FIGURE_PDF_DIR")
    if not figure_dir or figure_dir == "" then
      error("PID_GUIDE_FIGURE_PDF_DIR is required for PDF projection")
    end
    local basename = element.src:match("([^/]+)%.svg$")
    if not basename then
      error("cannot derive figure basename: " .. element.src)
    end
    element.src = figure_dir .. "/" .. basename .. ".pdf"
  end
  return element
end

function Table(element)
  if not FORMAT:match("latex") then
    return element
  end
  local widths = nil
  if last_heading == "1. Claim map" then
    widths = {0.20, 0.80}
  elseif last_heading == "2.1 Exact source boundary" then
    widths = {0.18, 0.31, 0.18, 0.33}
  elseif last_heading == "2.2 The actual no-thermal fixture" then
    widths = {0.14, 0.14, 0.14, 0.16, 0.16, 0.26}
  elseif last_heading == "2.3 What the calculation returns" then
    widths = {0.32, 0.22, 0.23, 0.23}
  elseif last_heading == "2.4 Exactly which pid-rs work Galadriel consumes" then
    widths = {0.22, 0.22, 0.28, 0.28}
  elseif last_heading == "5.1 One explicit proposed benchmark contract" then
    widths = {0.16, 0.26, 0.28, 0.30}
  elseif last_heading == "5.2 Three defensible grouping choices" then
    widths = {0.18, 0.23, 0.27, 0.32}
  elseif last_heading == "7.1 What is implemented" then
    widths = {0.08, 0.13, 0.16, 0.18, 0.45}
  elseif last_heading == "7.2 Existing timings and their boundary" then
    widths = {0.42, 0.28, 0.30}
  elseif last_heading == "8.2 Comparator matrix" then
    widths = {0.18, 0.25, 0.27, 0.30}
  elseif last_heading == "9. Ten grounded use cases" then
    widths = {0.05, 0.18, 0.25, 0.27, 0.25}
  elseif last_heading == "10.1 What formal tools can and cannot establish" then
    widths = {0.20, 0.40, 0.40}
  elseif last_heading == "10.2 Required claim packet for placement" then
    widths = {0.23, 0.77}
  elseif last_heading == "11.1 Experimental ladder" then
    widths = {0.14, 0.24, 0.31, 0.31}
  elseif last_heading == "12. Ecosystem disposition" then
    widths = {0.12, 0.25, 0.31, 0.32}
  elseif last_heading == "13. One-hundred-forty-lens council review" then
    widths = {0.05, 0.17, 0.35, 0.43}
  elseif last_heading == "A.6 Exact calculation from the current AND fixture" then
    widths = {0.20, 0.29, 0.24, 0.27}
  elseif last_heading == "A.7 Evidence-layer firewall" then
    widths = {0.18, 0.36, 0.46}
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

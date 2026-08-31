-- PDF-only projection for PID2_REPRESENTED_COORDINATE_ASSURANCE.md.
-- The Markdown is canonical. This filter changes layout and navigation, not claims.

local dropped_title = false
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
      and title == "PID2 represented-coordinate assurance, revision 4" then
    dropped_title = true
    return {}
  end
  if dropped_title and element.level > 1 then
    element.level = element.level - 1
  end
  last_heading = title
  if title == "Decision in one page" then
    return {
      pandoc.RawBlock("latex", "\\clearpage\\PidScopeFirewall\\Needspace{12\\baselineskip}"),
      element,
    }
  end
  if title == "5.5 Exact reconstruction versus Neumaier overflow" then
    return {pandoc.RawBlock("latex", "\\Needspace{38\\baselineskip}"), element}
  end
  if element.level == 1 then
    if title == "10. Expected Rust and Python behavior"
        or title == "11. Exact-real Z3 boundary"
        or title == "12. Cost and deployment interpretation"
        or title == "13. Negative results, supersession, and open work" then
      return {pandoc.RawBlock("latex", "\\Needspace{16\\baselineskip}"), element}
    end
    return {pandoc.RawBlock("latex", "\\clearpage"), element}
  end
  if element.level == 2 then
    return {pandoc.RawBlock("latex", "\\Needspace{11\\baselineskip}"), element}
  end
  return element
end

function Table(element)
  if not FORMAT:match("latex") then
    return element
  end
  local widths = nil
  if last_heading == "4. Why exact reduction is selected" then
    widths = {0.23, 0.30, 0.47}
  elseif last_heading == "5.5 Exact reconstruction versus Neumaier overflow" then
    widths = {0.08, 0.14, 0.25, 0.53}
  elseif last_heading == "5.8 Ordinary-scale 32/33 boundaries" then
    widths = {0.07, 0.41, 0.23, 0.14, 0.15}
  elseif last_heading == "8.1 Assumptions before the diagnostic equations" then
    widths = {0.24, 0.22, 0.27, 0.27}
  elseif last_heading == "9. Checker architecture and anti-cheating controls" then
    widths = {0.20, 0.27, 0.27, 0.26}
  elseif last_heading == "14. Thirty-four-lens adversarial review" then
    widths = {0.06, 0.24, 0.70}
  end
  if widths then
    return set_widths(element, widths)
  end
  local count = #element.colspecs
  if count == 2 then
    return set_widths(element, {0.34, 0.66})
  elseif count == 3 then
    return set_widths(element, {0.22, 0.32, 0.46})
  elseif count == 4 then
    return set_widths(element, {0.20, 0.27, 0.23, 0.30})
  elseif count == 5 then
    return set_widths(element, {0.10, 0.30, 0.22, 0.18, 0.20})
  end
  return element
end

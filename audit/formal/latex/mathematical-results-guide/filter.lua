-- Deterministic Pandoc projection for the mathematical-results guide.
-- Markdown and SVG files are canonical. This filter changes only the PDF projection.

local dropped_title = false
local last_heading = ""
local repository_blob_root = "https://github.com/sepahead/pid-rs/blob/main/"

local function figure_block(path, caption, label, width, height)
  local latex = string.format(
    "\\Needspace{%s}\\begin{figure}[H]\\centering" ..
      "\\includegraphics[width=%s,height=%s,keepaspectratio]{%s}" ..
      "\\caption{%s}\\label{%s}\\end{figure}",
    height,
    width,
    height,
    path,
    caption,
    label
  )
  return pandoc.RawBlock("latex", latex)
end

local function landscape_figure_block(path, caption, label)
  local latex = string.format(
    "\\clearpage\\begin{landscape}\\thispagestyle{fancy}" ..
      "\\begin{figure}[H]\\centering" ..
      "\\includegraphics[width=0.97\\linewidth,height=0.82\\textheight,keepaspectratio]{%s}" ..
      "\\caption{%s}\\label{%s}\\end{figure}" ..
      "\\end{landscape}\\clearpage",
    path,
    caption,
    label
  )
  return pandoc.RawBlock("latex", latex)
end

function Header(element)
  local title = pandoc.utils.stringify(element.content)
  if not dropped_title and element.level == 1 and title == "Mathematical results guide" then
    dropped_title = true
    return {}
  end
  last_heading = title
  if dropped_title and element.level > 1 then
    element.level = element.level - 1
  end
  if element.level == 1 then
    -- Section 3 can leave a short read-next tail at the top of a page. Keep
    -- the following Section 4 opening on that page when there is enough room,
    -- but move the complete opening together when there is not.
    if title == "4. Sampling and exact finite-table assurance" then
      return {pandoc.RawBlock("latex", "\\Needspace{22\\baselineskip}"), element}
    end
    return {pandoc.RawBlock("latex", "\\clearpage"), element}
  end
  if element.level == 2 then
    return {pandoc.RawBlock("latex", "\\Needspace{12\\baselineskip}"), element}
  end
  return element
end

function Para(element)
  local text = pandoc.utils.stringify(element.content)
  if text:match("^The 108 audit expressions expand") then
    return {
      pandoc.RawBlock("latex", "\\clearpage\\vspace*{\\fill}"),
      element,
      pandoc.RawBlock("latex", "\\vspace*{\\fill}\\clearpage"),
    }
  end
  if text:match("^Three statuses%.") then
    return {pandoc.RawBlock("latex", "\\Needspace{20\\baselineskip}"), element}
  end
  if text:match("^The full%-lattice atoms") then
    return {pandoc.RawBlock("latex", "\\Needspace{8\\baselineskip}"), element}
  end
  if text:match("^For i%.i%.d%. rows on") then
    return {pandoc.RawBlock("latex", "\\Needspace{12\\baselineskip}"), element}
  end
  if text:match("^For K") and text:match("the monotone upper envelopes") then
    return {pandoc.RawBlock("latex", "\\Needspace{13\\baselineskip}"), element}
  end
  if text:match("^The assurance covers the 24 coordinates") then
    return {pandoc.RawBlock("latex", "\\Needspace{9\\baselineskip}"), element}
  end
  if text:match("^The audit evaluates 2,197,584 products") then
    return {pandoc.RawBlock("latex", "\\Needspace{10\\baselineskip}"), element}
  end
  return element
end

function Image(element)
  if FORMAT:match("latex") and element.src:match("%.svg$") then
    element.src = element.src:gsub("%.svg$", ".pdf")
  end
  return element
end

function Figure(element)
  if not FORMAT:match("latex") then
    return element
  end
  local block = element.content and element.content[1]
  local image = block and block.content and block.content[1]
  local common_radius_svg =
    "audit/formal/latex/figures/mathematical-results-guide/common-radius-small-ball-bridge.svg"
  local common_radius_pdf =
    "audit/formal/latex/figures/mathematical-results-guide/common-radius-small-ball-bridge.pdf"
  if image and image.t == "Image"
      and (image.src == common_radius_svg or image.src == common_radius_pdf) then
    return landscape_figure_block(
      "audit/formal/latex/figures/mathematical-results-guide/common-radius-small-ball-bridge.pdf",
      "Common-radius small-ball cancellation and its first-order-overlap failure boundary. The result is a conditional population lemma, not a finite-sample estimator theorem.",
      "fig:common-radius-small-ball-bridge"
    )
  end
  return element
end

function Link(element)
  if FORMAT:match("latex")
      and not element.target:match("^[A-Za-z][A-Za-z0-9+.-]*:")
      and not element.target:match("^#") then
    -- A relative URI or GoToR action depends on the PDF viewer and on a preserved checkout
    -- layout. The Markdown source keeps repository-relative links so forks and branches remain
    -- navigable. Its committed PDF projection instead uses a live GitHub main URL so the link
    -- works after the PDF is downloaded or opened through GitHub's viewer. These navigation URLs
    -- are not provenance identities; exact evidence continues to use immutable digests/commits.
    if element.target:match("^/")
        or element.target:match("^%./")
        or element.target:match("^%.%./") then
      error("noncanonical repository-relative link in guide source: " .. element.target)
    end
    element.target = repository_blob_root .. element.target
  end
  return element
end

function Table(element)
  if not FORMAT:match("latex") then
    return element
  end
  local count = #element.colspecs
  local widths = {}
  if count == 3 and last_heading == "Evidence labels" then
    widths = {0.14, 0.43, 0.43}
  elseif count == 3 and last_heading == "Five distinct lanes" then
    widths = {0.24, 0.40, 0.36}
  elseif count == 3 and last_heading == "2. Result map" then
    widths = {0.23, 0.38, 0.39}
  elseif count == 3 and last_heading == "6. Estimator choice, global nonclaims, and further reading" then
    widths = {0.22, 0.32, 0.46}
  elseif count == 3 then
    widths = {0.24, 0.38, 0.38}
  elseif count == 2 then
    widths = {0.34, 0.66}
  else
    for index = 1, count do
      widths[index] = 1.0 / count
    end
  end
  for index, colspec in ipairs(element.colspecs) do
    element.colspecs[index] = {colspec[1], widths[index]}
  end

  if last_heading == "Five distinct lanes" then
    return {
      element,
      figure_block(
        "audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.pdf",
        "Semantic firewall for the five non-interchangeable method lanes.",
        "fig:semantic-firewall",
        "0.96\\linewidth",
        "150mm"
      ),
    }
  end
  if last_heading == "2. Result map" then
    return {
      element,
      landscape_figure_block(
        "audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.pdf",
        "Evidence and publication status map for the nine result families.",
        "fig:result-evidence-map"
      ),
    }
  end
  return element
end

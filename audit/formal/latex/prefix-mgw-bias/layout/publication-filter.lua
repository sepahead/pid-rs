-- Publication-source proposal. This file has not been executed in this stage.
-- Markdown keeps repository-relative links and SVG sources. The future LaTeX route
-- maps only this enumerated package's local links and pre-produced vector PDFs.
local base = "https://github.com/sepahead/pid-rs/blob/main/audit/formal/lean-prefix-mgw-bias/"
local local_links = {
  ["EXPOSITION.md"] = true,
  ["SUMMARY.md"] = true,
  ["THEOREM_MAP.md"] = true,
  ["formal/accepted_Contract.lean"] = true,
  ["formal/accepted_Candidate.lean"] = true,
  ["formal/accepted_RawTargets.lean"] = true,
  ["formal/accepted_AliasTargets.lean"] = true
}
local figure_sources = {
  ["figures/signed-tail-envelope.svg"] = "figures/signed-tail-envelope.pdf",
  ["figures/overlapping-query-moment.svg"] = "figures/overlapping-query-moment.pdf",
  ["figures/independence-horizon-one.svg"] = "figures/independence-horizon-one.pdf"
}
function Link(element)
  if not FORMAT:match("latex") then return element end
  local target = element.target
  if target:match("^https://") or target:match("^#") then return element end
  if local_links[target] then
    element.target = base .. target
    return element
  end
  error("Unmapped publication link: " .. target)
end
function Image(element)
  if not FORMAT:match("latex") then return element end
  local replacement = figure_sources[element.src]
  if not replacement then error("Unmapped publication image: " .. element.src) end
  element.src = replacement
  return element
end

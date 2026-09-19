-- Two fixed research-note sources. This source has not been executed in preparation.
local titles = {
  gradient = "Finite-prefix MGW derivatives: a score identity, truncation bound and second moment",
  cusp = "Zero cell tangents with a support-changing mutual-information cusp"
}
local base = "https://github.com/sepahead/pid-rs/blob/main/"
local local_links = {
  ["../../formal/lean-prefix-mgw-gradient/THEOREM_MAP.md"] = "audit/formal/lean-prefix-mgw-gradient/THEOREM_MAP.md",
  ["../../formal/lean-prefix-mgw-mean/EXPOSITION.current.md"] = "audit/formal/lean-prefix-mgw-mean/EXPOSITION.current.md",
  ["../../formal/lean-prefix-mgw-mean/SOURCE_CORRESPONDENCE.md"] = "audit/formal/lean-prefix-mgw-mean/SOURCE_CORRESPONDENCE.md",
  ["../../formal/lean-prefix-mgw-mean/PUBLICATION.md"] = "audit/formal/lean-prefix-mgw-mean/PUBLICATION.md",
  ["../../formal/lean-prefix-mgw-bias/EXPOSITION.md"] = "audit/formal/lean-prefix-mgw-bias/EXPOSITION.md",
  ["../../formal/lean-prefix-mgw-bias/THEOREM_MAP.md"] = "audit/formal/lean-prefix-mgw-bias/THEOREM_MAP.md",
  ["../finite-prefix-mgw-gradient/EXPOSITION.md"] = "audit/research/finite-prefix-mgw-gradient/EXPOSITION.md",
  ["../support-change-mi-cusp/EXPOSITION.md"] = "audit/research/support-change-mi-cusp/EXPOSITION.md",
  ["../../../PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md#9-ten-grounded-use-cases"] = "PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md#9-ten-grounded-use-cases",
  ["../../../PID_ALTERNATIVES_AND_INCREMENTAL_VALUE.md"] = "PID_ALTERNATIVES_AND_INCREMENTAL_VALUE.md",
  ["../../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md"] = "SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md"
}
local external_links = {
  ["https://arxiv.org/abs/2002.03356v5"] = true,
  ["https://doi.org/10.1103/PhysRevE.103.032149"] = true,
  ["https://proceedings.neurips.cc/paper/2015/file/de03beffeed9da5f3639a621bcab5dd4-Paper.pdf"] = true
}
local kind, h1_count, image_count
local function metadata(meta)
  if FORMAT ~= "latex" then error("Only the declared LaTeX route is supported") end
  kind = pandoc.utils.stringify(meta["publication-kind"])
  if not titles[kind] then error("Unknown publication kind") end
  if pandoc.utils.stringify(meta.title) ~= titles[kind] then error("Title/kind mismatch") end
  h1_count, image_count = 0, 0
  if kind == "gradient" then
    meta.subtitle = pandoc.MetaString("Finite categorical laws, complete derivations and explicit proof scope")
    meta.runninghead = pandoc.MetaString("Finite-prefix derivatives")
    meta.subject = pandoc.MetaString("Finite categorical MGW derivative bias and second-moment bounds")
  else
    meta.subtitle = pandoc.MetaString("Handwritten negative example; formal verification remains open")
    meta.runninghead = pandoc.MetaString("Support-change MI cusp")
    meta.subject = pandoc.MetaString("Hand-derived support-changing mutual-information boundary example")
  end
  return meta
end
local function header(element)
  if element.level == 1 then
    h1_count = h1_count + 1
    if pandoc.utils.stringify(element.content) ~= titles[kind] then
      error("Source title/kind mismatch")
    end
    return {}
  end
  element.level = element.level - 1
  return element
end
local function link(element)
  if external_links[element.target] then return element end
  local relative = local_links[element.target]
  if not relative then error("Unmapped publication link: " .. element.target) end
  element.target = base .. relative
  return element
end
local function image(element)
  if kind ~= "gradient" or element.src ~= "figures/prefix-score-experiment.svg" then
    error("Unmapped publication image: " .. element.src)
  end
  image_count = image_count + 1
  element.src = "figures/prefix-score-experiment.pdf"
  return element
end
local function complete(document)
  if h1_count ~= 1 then error("Exactly one source title is required") end
  local expected_images = kind == "gradient" and 1 or 0
  if image_count ~= expected_images then error("Publication image inventory differs") end
  return document
end
-- Separate passes make kind metadata available before visiting headers or images.
return {
  {Meta = metadata},
  {Header = header, Link = link, Image = image},
  {Pandoc = complete}
}

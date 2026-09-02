-- PDF-only navigation projection for the dated custody receipt.
-- Markdown keeps repository-relative links. A standalone PDF uses HTTPS GitHub navigation
-- links instead of relative filespecs, GoToR actions, or file:// targets. These links are
-- navigation aids; exact bytes remain bound by the receipt and TSV hashes.
local github_navigation_links = {
  ["post-publication-custody-2026-09-02.json"] =
    "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/post-publication-custody-2026-09-02.json",
  ["../../output/pdf/post-publication-custody-2026-09-02.pdf"] =
    "https://github.com/sepahead/pid-rs/blob/main/output/pdf/post-publication-custody-2026-09-02.pdf",
  ["../formal/figures/post-publication-custody/state.pdf"] =
    "https://github.com/sepahead/pid-rs/blob/main/audit/formal/figures/post-publication-custody/state.pdf",
  ["post-publication-remote-heads-2026-09-02.tsv"] =
    "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/post-publication-remote-heads-2026-09-02.tsv",
}

function Link(element)
  if FORMAT:match("latex") then
    local replacement = github_navigation_links[element.target]
    if replacement ~= nil then
      element.target = replacement
    end
  end
  return element
end

function Image(element)
  if FORMAT:match("latex")
      and element.src == "../formal/figures/post-publication-custody/state.pdf" then
    local staged = os.getenv("PID_CUSTODY_FIGURE_PDF")
    if staged == nil or staged == "" then
      error("PID_CUSTODY_FIGURE_PDF is required for the isolated PDF build")
    end
    element.src = staged
  end
  return element
end

function Code(element)
  if FORMAT:match("latex")
      and (#element.text == 40 or #element.text == 64)
      and element.text:match("^[0-9a-f]+$") then
    return pandoc.RawInline(
      "latex",
      "\\texttt{\\seqsplit{" .. element.text .. "}}"
    )
  end
  return element
end

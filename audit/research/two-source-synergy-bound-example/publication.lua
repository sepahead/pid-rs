-- Convert only this note's local image and source links for its PDF edition.
local prior = "https://github.com/sepahead/pid-rs/blob/8ff4e244f63d94ff14a9075da212db6a67c108ec/"
local note = "https://github.com/sepahead/pid-rs/blob/70e55aacc5c7fb53270a306db962c259e46482d8/audit/research/two-source-synergy-bound-example/"
local atom = "https://github.com/sepahead/pid-rs/blob/8299214c4198d263f28e7f2a8ab28b78b3133e07/audit/research/two-source-synergy-bound-example/"
function Pandoc(doc)
  if pandoc.utils.stringify(doc.blocks[1]) ~= "How the support count changes a synergy bound"
      or pandoc.utils.stringify(doc.blocks[2]) ~= "Sepehr Mahmoudian · 2026" then
    error("unexpected report title or byline")
  end
  doc.blocks:remove(1)
  doc.blocks:remove(1)
  return doc:walk({
    Header = function(el) el.level = el.level - 1; return el end,
    HorizontalRule = function() return pandoc.RawBlock("latex", "\\newpage") end,
    Figure = function(el)
      local images = {}
      el:walk({Image = function(image) table.insert(images, image.src) end})
      local caption = el.caption.long
      if #images ~= 1 or images[1] ~= "support-bounds.svg" or #caption == 0 then
        error("expected the single count-and-bounds graphic and its visible caption")
      end
      local parts = pandoc.Blocks({pandoc.RawBlock("latex",
        "\\newpage\n\\begin{center}\\includegraphics[width=\\linewidth]{support-bounds.pdf}\\end{center}")})
      for _, block in ipairs(caption) do parts:insert(block) end
      return parts
    end,
    Link = function(el)
      if el.target:match("^https://") then return el end
      local src = el.target:match("^%.%./%.%./%.%./([%w_/%-%.]+)$")
      if src and not src:find("..",1,true) then
        el.target = prior .. src
      elseif el.target == "verify_signed_synergy.py" then
        el.target = atom .. el.target
      elseif el.target:match("^[%w_%-]+%.[%w]+$") then
        el.target = note .. el.target
      else
        error("unexpected publication link " .. el.target)
      end
      return el
    end
  })
end

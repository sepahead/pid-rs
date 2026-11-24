-- Emit one canonical Markdown body. The TeX cover supplies the same title and byline.
function Pandoc(doc)
  if doc.blocks[1].t ~= "Header" or pandoc.utils.stringify(doc.blocks[1]) ~= "Mathematical results guide for November 2026" then
    error("unexpected current guide title")
  end
  if pandoc.utils.stringify(doc.blocks[2]) ~= "Sepehr Mahmoudian · 24 November 2026" then
    error("unexpected current guide byline")
  end
  doc.blocks:remove(1)
  doc.blocks:remove(1)
  return doc:walk({
    Header = function(el) el.level = el.level - 1; return el end,
    HorizontalRule = function() return pandoc.RawBlock("latex", "\\clearpage") end,
    Link = function(link)
      if not link.target:match("^https://") then
        if not link.target:match("^[%w_/%-%.]+$") or link.target:find("..",1,true) then
          error("unexpected relative current-guide link: " .. link.target)
        end
        link.target = "https://github.com/sepahead/pid-rs/blob/main/" .. link.target
      end
      return link
    end
  })
end

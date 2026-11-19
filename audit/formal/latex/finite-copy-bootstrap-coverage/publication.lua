-- One canonical Markdown body. Keep its title and byline once in the reviewed cover treatment.
local title = "Coverage of a bootstrap percentile range on a four-row copy law"
function Pandoc(doc)
  if doc.blocks[1].t ~= "Header" or pandoc.utils.stringify(doc.blocks[1]) ~= title then
    error("unexpected study title")
  end
  if pandoc.utils.stringify(doc.blocks[2]) ~= "Sepehr Mahmoudian · 18 November 2026" then
    error("unexpected study byline")
  end
  doc.blocks:remove(1)
  doc.blocks:remove(1)
  return doc:walk({
    Header = function(el) el.level = el.level - 1; return el end,
    HorizontalRule = function() return pandoc.RawBlock("latex", "\\newpage") end,
    Table = function(el)
      for _, row in ipairs(el.head.rows) do
        for _, cell in ipairs(row.cells) do
          for _, block in ipairs(cell.contents) do
            if block.t == "Plain" or block.t == "Para" then
              block.content = pandoc.List({pandoc.Strong(block.content)})
            end
          end
        end
      end
      return el
    end,
    Link = function(el)
      if not el.target:match("^https://") then
        if not el.target:match("^[%w_/%-%.]+$") or el.target:find("..",1,true) then
          error("unexpected relative publication link: " .. el.target)
        end
        el.target = "https://github.com/sepahead/pid-rs/blob/main/" .. el.target
      end
      return el
    end
  })
end

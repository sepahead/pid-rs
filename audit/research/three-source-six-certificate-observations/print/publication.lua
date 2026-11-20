-- One canonical Markdown body. Keep its title and byline once in the reviewed cover treatment.
local title = "Reading six three-source categorical shared-exclusion certificates"
function Pandoc(doc)
  if doc.blocks[1].t ~= "Header" or pandoc.utils.stringify(doc.blocks[1]) ~= title then
    error("unexpected study title")
  end
  if pandoc.utils.stringify(doc.blocks[2]) ~= "Sepehr Mahmoudian · 20 November 2026" then
    error("unexpected study byline")
  end
  doc.blocks:remove(1)
  doc.blocks:remove(1)
  -- Preserve the reader's section order and keep each mathematical discussion together.
  local pages = {
    ["The defining papers"] = true,
    ["Bounding the logarithm"] = true,
    ["Transformations of the six tables"] = true,
    ["Checks on altered records"] = true,
    ["Evidence and open obligations"] = true
  }
  local paged = pandoc.Blocks({})
  for _, block in ipairs(doc.blocks) do
    if block.t == "Header" and pages[pandoc.utils.stringify(block)] then
      paged:insert(pandoc.RawBlock("latex", "\\newpage"))
    end
    paged:insert(block)
  end
  doc.blocks = paged
  return doc:walk({
    Header = function(el) el.level = el.level - 1; return el end,
    HorizontalRule = function() return pandoc.RawBlock("latex", "\\newpage") end,
    Table = function(el)
      if #el.colspecs == 2 then
        el.colspecs = {{"AlignLeft", 0.25}, {"AlignLeft", 0.75}}
      elseif #el.colspecs == 7 then
        el.colspecs = {{"AlignLeft", 0.23}, {"AlignRight", 0.09}, {"AlignRight", 0.095},
                       {"AlignCenter", 0.20}, {"AlignRight", 0.14}, {"AlignRight", 0.105}, {"AlignRight", 0.14}}
      end
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
        if not el.target:match("^[%w_/%-%.]+$") or el.target:sub(1,1)=="/" then
          error("unexpected relative publication link: " .. el.target)
        end
        local parts = {"audit", "research", "three-source-six-certificate-observations"}
        for piece in el.target:gmatch("[^/]+") do
          if piece == ".." then
            if #parts == 0 then error("link outside the repository") end
            table.remove(parts)
          elseif piece ~= "." then
            table.insert(parts, piece)
          end
        end
        local kind = el.target == "cases" and "tree" or "blob"
        el.target = "https://github.com/sepahead/pid-rs/" .. kind .. "/main/" .. table.concat(parts, "/")
      end
      return el
    end
  })
end

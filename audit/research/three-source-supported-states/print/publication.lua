-- Set print pagination once on the canonical Markdown body.
local title = "When are all 18 local shared-exclusion calculations finite?"
local break_before = {
  ["The exact support condition"] = true,
  ["Two ways to write the joint event"] = true,
  ["From counts to signed information"] = true,
  ["A missing response in eight synthetic trials"] = true,
  ["When the two components increase"] = true,
  ["Checking the evidence"] = true,
  ["Rust implementation and computational cost"] = true
}

local function public_link(el)
  if el.target:match("^https://") then return el end
  if not el.target:match("^[%w_/%-%.]+$") or el.target:sub(1, 1) == "/" then
    error("unexpected relative publication link: " .. el.target)
  end
  local parts = {"audit", "research", "three-source-supported-states"}
  for piece in el.target:gmatch("[^/]+") do
    if piece == ".." then
      if #parts == 0 then error("link outside repository") end
      table.remove(parts)
    elseif piece ~= "." then
      table.insert(parts, piece)
    end
  end
  el.target = "https://github.com/sepahead/pid-rs/blob/main/" .. table.concat(parts, "/")
  return el
end

local function order_figure(el)
  local image = el.content[1] and el.content[1].content[1]
  if not image or image.t ~= "Image" or image.src ~= "signed-order.svg" then
    error("unexpected study figure")
  end
  local print_dir = pandoc.path.directory(PANDOC_SCRIPT_FILE)
  local source = pandoc.path.join({print_dir, "..", image.src})
  pandoc.pipe("rsvg-convert", {"--format=pdf", "--output=signed-order.pdf", source}, "")
  local caption = pandoc.utils.stringify(el.caption.long)
  if caption ~= "Moving up from the two-branch family decreases one signed ratio and increases the other." then
    error("unexpected signed-order caption")
  end
  return pandoc.RawBlock("latex", "\\begin{center}\n" ..
    "\\includegraphics[width=.89\\linewidth]{signed-order.pdf}\n" ..
    "\\captionof{figure}{" .. caption .. "}\n\\end{center}")
end

function Pandoc(doc)
  if doc.blocks[1].t ~= "Header" or pandoc.utils.stringify(doc.blocks[1]) ~= title
      or pandoc.utils.stringify(doc.blocks[2]) ~= "Sepehr Mahmoudian · 22 November 2026" then
    error("unexpected study title or byline")
  end
  doc.blocks:remove(1)
  doc.blocks:remove(1)
  local paged = pandoc.Blocks({})
  for _, block in ipairs(doc.blocks) do
    if block.t == "Header" and break_before[pandoc.utils.stringify(block)] then
      paged:insert(pandoc.RawBlock("latex", "\\newpage"))
    end
    paged:insert(block)
  end
  doc.blocks = paged
  return doc:walk({
    Header = function(el) el.level = el.level - 1; return el end,
    Link = public_link,
    Figure = order_figure,
    Table = function(el)
      local widths = {
        [2] = {{"AlignLeft", .18}, {"AlignLeft", .82}},
        [3] = {{"AlignLeft", .60}, {"AlignCenter", .20}, {"AlignCenter", .20}},
        [4] = {{"AlignLeft", .31}, {"AlignLeft", .29}, {"AlignCenter", .20}, {"AlignRight", .20}},
        [5] = {{"AlignLeft", .31}, {"AlignLeft", .27}, {"AlignRight", .14},
               {"AlignRight", .14}, {"AlignRight", .14}}
      }
      if pandoc.utils.stringify(el.head.rows[1].cells[1].contents):match("^Match required at") then
        el.colspecs = {{"AlignLeft", .50}, {"AlignCenter", .11}, {"AlignCenter", .11}, {"AlignCenter", .28}}
      else
        el.colspecs = assert(widths[#el.colspecs], "unexpected finite-study table")
      end
      return el
    end
  })
end

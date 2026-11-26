-- Emit one canonical Markdown body. The TeX cover supplies the same title and byline.
function Pandoc(doc)
  if doc.blocks[1].t ~= "Header" or pandoc.utils.stringify(doc.blocks[1]) ~= "Mathematical results guide for November 2026" then
    error("unexpected current guide title")
  end
  if pandoc.utils.stringify(doc.blocks[2]) ~= "Sepehr Mahmoudian · 25 November 2026" then
    error("unexpected current guide byline")
  end
  doc.blocks:remove(1)
  doc.blocks:remove(1)
  return doc:walk({
    Header = function(el) el.level = el.level - 1; return el end,
    HorizontalRule = function() return pandoc.RawBlock("latex", "\\clearpage") end,
    Image = function(image)
      local figures = {
        ["audit/research/angular-ray-monotonicity/figures/angular-ray-thresholds.svg"] = "angular-ray-thresholds.pdf",
        ["audit/research/signed-log-certificate-enclosure/figures/intervals.svg"] = "intervals.pdf",
        ["audit/research/nested-categorical-sources/figures/partitions-and-margin.svg"] = "partitions-and-margin.pdf",
        ["audit/research/strict-neighbour-count-geometry/figures/counts-and-distances.svg"] = "counts-and-distances.pdf"
      }
      local target = figures[image.src]
      if not target then error("unregistered current-guide figure: " .. image.src) end
      return pandoc.RawInline("latex", "\\href{https://github.com/sepahead/pid-rs/blob/main/" ..
        image.src .. "}{\\includegraphics[width=0.94\\linewidth,height=0.25\\textheight,keepaspectratio]{" .. target .. "}}")
    end,
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

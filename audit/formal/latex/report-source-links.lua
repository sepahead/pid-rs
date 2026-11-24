-- Rewrite only links that Pandoc identifies in prose. Math and code remain separate nodes.
local web = "https://github.com/sepahead/pid-rs/blob/main/"
local source_dir = os.getenv("PID_RS_REPORT_SOURCE_DIR") or ""

function Link(link)
  local target = link.target
  if target:match("^https://") or target:match("^#") then
    return link
  end
  if not source_dir:match("^audit/research/[%w%-]+$") then
    error("missing or invalid report source directory")
  end
  if target == "" or target:match("^/") or target:match("^[%a][%w+%.%-]*:") then
    error("expected a repository-relative path or HTTPS URL")
  end
  local path, fragment = target:match("^([^#]*)(.*)$")
  if not path:match("^[%w%._/%-]+$") or
      (fragment ~= "" and not fragment:match("^#[%w%._%-]+$")) then
    error("invalid report source link: " .. target)
  end
  local parts = {}
  for component in (source_dir .. "/" .. path):gmatch("[^/]+") do
    if component == ".." then
      if #parts == 0 then
        error("source link leaves the repository: " .. target)
      end
      table.remove(parts)
    elseif component ~= "." then
      table.insert(parts, component)
    end
  end
  if #parts == 0 then
    error("source link has no repository destination")
  end
  link.target = web .. table.concat(parts, "/") .. fragment
  return link
end

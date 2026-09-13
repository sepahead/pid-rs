-- Load one profile-bound, build-private Markdown module under its standard logical name.
-- The source transformer verifies SHA-256 before every compiler pass; this loader rechecks the
-- exact byte length and emits one bounded consumption marker.  The captured entry wrapper and FLS
-- closure bind this loader's exact execution path without enabling LuaTeX's debug library.
local configuration = ...
local namespace_name = "pid_rs_workflow_markdown_gc"

assert(type(configuration) == "table", "PID-RS-MARKDOWN-GC: missing configuration")
for _, field in ipairs({
  "module_path", "module_bytes", "profile_id", "metadata_version"
}) do
  assert(configuration[field] ~= nil, "PID-RS-MARKDOWN-GC: missing field " .. field)
end
assert(type(configuration.module_path) == "string" and #configuration.module_path > 0,
       "PID-RS-MARKDOWN-GC: invalid module path")
assert(type(configuration.module_bytes) == "number"
       and configuration.module_bytes > 0
       and configuration.module_bytes % 1 == 0,
       "PID-RS-MARKDOWN-GC: invalid module length")
assert(type(configuration.profile_id) == "string"
       and configuration.profile_id:match("^[a-z0-9][a-z0-9._-]*$")
       and #configuration.profile_id <= 80,
       "PID-RS-MARKDOWN-GC: invalid profile ID")
assert(type(configuration.metadata_version) == "string"
       and #configuration.metadata_version > 0
       and #configuration.metadata_version <= 80,
       "PID-RS-MARKDOWN-GC: invalid metadata version")
assert(rawget(_G, namespace_name) == nil,
       "PID-RS-MARKDOWN-GC: loader namespace already exists")
assert(package.loaded.markdown == nil and package.preload.markdown == nil,
       "PID-RS-MARKDOWN-GC: Markdown already loaded or preloaded")

local stream = assert(io.open(configuration.module_path, "rb"))
local raw = assert(stream:read("*a"))
assert(stream:close())
assert(#raw == configuration.module_bytes,
       "PID-RS-MARKDOWN-GC: private module length differs")
local chunk = assert(load(raw, "@" .. configuration.module_path, "t", _G))
raw = nil
local loaded = false

rawset(_G, namespace_name, {
  profile_id = configuration.profile_id,
  loaded = false,
})

package.preload.markdown = function(module_name)
  assert(module_name == "markdown", "PID-RS-MARKDOWN-GC: logical module name differs")
  assert(not loaded, "PID-RS-MARKDOWN-GC: private loader called more than once")
  loaded = true
  local module = chunk(module_name)
  chunk = nil
  assert(type(module) == "table" and type(module.metadata) == "table",
         "PID-RS-MARKDOWN-GC: private module result differs")
  assert(module.metadata.version == configuration.metadata_version,
         "PID-RS-MARKDOWN-GC: private module metadata differs")
  local state = assert(rawget(_G, namespace_name))
  state.loaded = true
  texio.write_nl("log", "PID-RS-MARKDOWN-GC=" .. configuration.profile_id)
  texio.write_nl("log", "")
  return module
end

return rawget(_G, namespace_name)

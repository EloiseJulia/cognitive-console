local skipping_abstract = false

local function source_comment(text)
  text = text:gsub("[\r\n]+", " ")
  return pandoc.RawInline("latex", "{}% " .. text .. "\n")
end

local function visible_gap(text)
  text = text:gsub("[\r\n]+", " ")
  text = text:gsub("^MISSING FACT:%s*", "")
  return pandoc.RawInline("latex", "\\Gap{" .. text .. "}")
end

function Header(header)
  local title = pandoc.utils.stringify(header.content)

  if header.level == 1 then
    return {}
  end

  if header.level == 2 and title == "Abstract" then
    skipping_abstract = true
    return {}
  end

  if header.level == 2 and title == "Introduction" then
    skipping_abstract = false
  end

  header.level = header.level - 1
  return header
end

function Para(paragraph)
  if skipping_abstract then
    return {}
  end
  return paragraph
end

function RawInline(inline)
  if inline.format == "html" then
    local comment = inline.text:match("^<!%-%-%s*(.-)%s*%-%->$")
    if comment then
      return source_comment(comment)
    end
  end
  return inline
end

function RawBlock(block)
  if skipping_abstract then
    return {}
  end

  if block.format == "html" then
    local comment = block.text:match("^<!%-%-%s*(.-)%s*%-%->$")
    if comment then
      return pandoc.RawBlock("latex", "% " .. comment)
    end
  end
  return block
end

function Code(code)
  local text = code.text:match("^%[MISSING FACT:%s*(.-)%]$")
  if text then
    return visible_gap(text)
  end
  return code
end

function Inlines(inlines)
  local output = pandoc.Inlines({})
  local index = 1

  while index <= #inlines do
    local current = inlines[index]

    if current.t == "Str" and current.text:match("^%[MISSING") then
      local marker = pandoc.Inlines({})
      local closed = false

      while index <= #inlines do
        local item = inlines[index]
        marker:insert(item)
        index = index + 1
        if item.t == "Str" and item.text:match("%]$") then
          closed = true
          break
        end
      end

      if closed then
        local text = pandoc.utils.stringify(marker)
        text = text:gsub("^%[", ""):gsub("%]$", "")
        output:insert(visible_gap(text))
      else
        for _, item in ipairs(marker) do
          output:insert(item)
        end
      end
    else
      output:insert(current)
      index = index + 1
    end
  end

  return output
end

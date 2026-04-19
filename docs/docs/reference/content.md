# Content

The `content` module provides typed message payload builders. Each class serialises its data into the dict format expected by the Matrix client-server API. You rarely need to instantiate these directly — `Room` methods create them for you — but they are useful when constructing custom message types.

```python
from matrix.content import MarkdownMessage, TextContent

plain = TextContent(body="Hello, world!")
rich  = MarkdownMessage(body="**Hello**, world!")
```

::: matrix.content.BaseMessageContent

::: matrix.content.TextContent

::: matrix.content.MarkdownMessage

::: matrix.content.NoticeContent

::: matrix.content.ReplyContent

::: matrix.content.EditContent

::: matrix.content.FileContent

::: matrix.content.ImageContent

::: matrix.content.AudioContent

::: matrix.content.VideoContent

::: matrix.content.LocationContent

::: matrix.content.ReactionContent

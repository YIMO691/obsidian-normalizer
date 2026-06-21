---
title: Code Block Dashes Test
tags:
  - unity
---

# Code Block Dashes Test

Below is a code block containing `---` which must NOT be treated
as a frontmatter boundary:

```yaml
---
title: fake frontmatter
tags:
  - not-real
---
```

End of document.

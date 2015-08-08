# gittagstats
Generate statistics report from a set of tags for a git repository

```python
Add this as a git submodule to your project.
git submodule add https://github.com/mcharleb/gittagstats.git

Sample usage:

import os
import git
from gittagstats.gittagstats import *

repo = git.Repo("/path/to/linux/kernel")
tags = ["v3.17", "v3.18", "v3.19", "v4.0", "v4.1"]

# Only consider files in ./arch/arm
file_list.append('arch/arm')

# Define the groups to sort using 
me = Group("Personal Group", ["me@gmail.com", "somebody@gmail.com"])
somecompany = Group("Some Company", ["@somecompany.org"])
others = Group("Others", [], me.email + somecompany.email)
 
groups = [ me, somecompany, others ]

report = Report(repo, tags, file_list, groups)
report.generate()
report.show_table()
report.show_commits()
```

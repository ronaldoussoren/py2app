#!/usr/bin/env python

import re

with open("doc/changelog.rst") as stream:
    body = stream.read()

value = re.split("^-+$", body, flags=re.MULTILINE)[1]
print(value.rsplit("\n", 2)[0].strip())

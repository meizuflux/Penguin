"""
The MIT License (MIT)
Copyright (c) 2015-2019 Rapptz
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from discord.ext.menus import ListPageSource
from collections import namedtuple
import itertools

# THIS CODE IS DANNY'S, NOT MINE. I AM SIMPLE MODIFYING IT TO FIT MY PURPOSE.

_GroupByEntry = namedtuple('_GroupByEntry', 'key items')


class HelpGroup(ListPageSource):
    def __init__(self, entries, *, per_page):
        key = lambda c: getattr(c.cog, 'qualified_name', 'Unsorted')
        self.__entries = sorted(entries, key=key)
        nested = []
        self.nested_per_page = per_page
        for k, g in itertools.groupby(self.__entries, key=key):
            g = list(g)
            if not g:
                continue
            size = len(g)

            # Chunk the nested pages
            nested.extend(_GroupByEntry(key=k, items=g[i:i + per_page]) for i in range(0, size, per_page))

        nested.insert(0, _GroupByEntry(key="Walrus Help Command", items="None, this is simply a placeholder"))
        super().__init__(nested, per_page=1)

    async def get_page(self, page_number):
        return self.entries[page_number]

    async def format_page(self, menu, entry):

        raise NotImplementedError

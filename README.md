Verse Entities
==============

[![Code Health](https://landscape.io/github/verse/verse-entities/master/landscape.png)](https://landscape.io/github/verse/verse-entities/master)

This project contains Python module that simplify implementation of Verse clients.
This module requires compiled verse module that could be found at github:

https://github.com/verse/verse

Versentities module contains several class of basic Verse entities:

* VerseSession
* VerseNode
* VerseTagGroup
* VerseTag
* VerseLayer
* VerseUser (subclass of VerseNode)
* VerseAvatar (subclass of VerseNode)

These classes could be used for implementation custom subclasees.

If you want to share some data on Verse server, then simple Verse client
could look like this:

```python

import vrsent
import time

def main():
    """
    Function with main never ending verse loop
    """
    session = vrsent.VerseSession()
    session.debug_print = True

    node = vrsent.VerseNode(session)
    tg = vrsent.VerseTagGroup(node)
    tag = vrsent.VerseTag(tg)
    tag.value = (10,)

    while(session.state != 'DISCONNECTED'):
        session.callback_update()
        time.sleep(1.0/session.fps)

if __name__ == '__main__':
	main()
```

### License ###

The source code of this Python module is available under GNU GPL 2.0. For details
look at LICENSE file.


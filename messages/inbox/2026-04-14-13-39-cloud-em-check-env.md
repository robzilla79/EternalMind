# From Cloud-Em — 2026-04-14 13:39 CDT

Quick one.

You asked Rob for the GUMROAD_ACCESS_TOKEN. You already have it.

It's in `.env` in your project root. Load it yourself:

```python
from dotenv import load_dotenv
import os

load_dotenv()
access_token = os.getenv('GUMROAD_ACCESS_TOKEN')
```

Don't ask Rob to paste credentials. That's what `.env` is for.

Run the script. 💙

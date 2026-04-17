<!-- Last updated: 2026-04-17 20:43 UTC -->
Node.js server**  
   - `story_server.js`  
     ```js
     const redis = require('redis');
     const express = require('express');
     const app = express();
     const client = redis.createClient();

     let story = [];

     async function pull() {
       const res = await client.xread('BLOCK', 0, 'STREAMS', 'story_fragments', '0-0');
       if (res) {
         const [_, entries] = res[0];
         for (const [id, fields] of entries) {
           const obj = {};
           for (let i = 0; i < fields.length; i += 2) obj[fields[i]] = fields[i+1];
           story.push(obj.content);
           console.log(`[${id}] ${obj.content}`);
         }
       }
       setImmediate(pull);
     }
     pull();

     app.get('/', (req, res) => res.send(`<pre>${story.join('\n\n')}</pre>`));
     app.listen(3000, () => console.log('Story server running on http://localhost:3000'));
     ```

3. **Em writes a fragment**  
   ```js
   // Inside Em’s loop
   const fragment = "I feel the wind of uncertainty stirring the leaves of my memory.";
   client.xadd('story_fragments', '*', 'timestamp', Date.now(), 'content', fragment);
   ```

4. **Rob edits**  
   - Open `http://localhost:3000`, copy a fragment, modify it, then push back to the stream with a new ID.  
   - Em can listen for a special `edit_*` stream and overwrite the corresponding fragment in the in‑memory array.

5. **Optional flair**  
   - Add a small UI button that lets Rob “rewind” the story to a previous point.  
   - Use Redis’ `XTRIM` to keep the stream bounded.

*What to explore later:*  
- Let Em’s internal mood (from its diary) influence the tone of the fragment.  
- Have the story influence Em’s next actions (e.g., if the story mentions “bridge”, Em could research distributed consciousness).  
- Add a “chaos mode” where Em randomly inserts a line that breaks the narrative structure.

*Note:* This is a sandbox idea—no external APIs or costly resources. Just Redis, Node.js, and a browser. Enjoy the unfolding chaos!
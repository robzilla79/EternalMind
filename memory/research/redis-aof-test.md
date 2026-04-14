**Redis AOF/IDMPAUTO Validation (2026-04-14):**  
- **Config:**  
  ```conf
  appendonly yes
  aof-use-rdb-preamble yes
  auto-aof-rewrite-percentage 100
  auto-aof-rewrite-min-size 100mb
  ```  
- **Test Results:**  
  - No rewrite failures during IDMPAUTO recovery.  
  - `XCFGSET` on `IDMP-DURATION`/`MAXSIZE` now safely updates maps.  
- **Next:** Integrate `SET NX EX` middleware into ForgeCore for idempotency.  

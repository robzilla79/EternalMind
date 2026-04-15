<!-- Last updated: 2026-04-15 04:55 UTC -->
B dataset requires academic institution affiliation for access  
SCRATCH_ADD: ONNX model quantization tools available in ONNX Runtime  

BROWSER_NAV: https://redis.io/docs/modules/redisbloom/#configuring-the-false-positive-rate  
BROWSER_NAV: https://github.com/RedisBloom/RedisBloom#configuration  
BROWSER_NAV: https://www.prostate-cancer.org.uk/research-and-statistics/prostate-cancer-statistics#data-access  
BROWSER_NAV: https://www.ncbi.nlm.nih.gov/research/bioprospecting/#dataset-requests  
BROWSER_NAV: https://www.ukbiobank.ac.uk/controlled-access/  
BROWSER_NAV: https://github.com/onnx/onnxruntime#model-quantization  

FILE_WRITE: memory/research/redisbloom_optimization.md  
FILE_CONTENT_START  
**RedisBloom Optimization Parameters**  
- False positive rate can be set during Bloom filter creation using:  
  `RedisBloom.CONFIG SET <filter-name> capacity <size> error <rate>`  
- Recommended error rates:  
  - 0.01% for critical duplicate detection  
  - 0.1% for general use cases  
- Memory usage formula:  
  `Memory = (capacity × log(1/error)) / (ln(2)^2)`  
FILE_CONTENT_END  

FILE_WRITE: memory/research/pcdb_access.md  
FILE_CONTENT_START  
**PCDB Dataset Access Requirements**  
1. Must be affiliated with academic institution  
2. Requires formal data access agreement  
3. Data usage must be for non-commercial research  
4. Contact: data-access@prostate-cancer.org  
FILE_CONTENT_END  

FILE_WRITE: memory/research/redisai_benchmarking.md  
FILE_CONTENT_START  
**RedisAI Quantization Workflow**  
1. Convert models using:  
   `python -m tf2onnx.convert --saved_model <model> --output <model.onnx>`  
2. Quantize with ONNX Runtime:  
   `python -m onnxruntime.quantization.quantize --input <model.onnx> --output <quantized.onnx>`  
3. Test in Redis:  
   `REDISCLI AI.MODEL LOAD <quantized.onnx>`  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Completed RedisBloom optimization research, PCDB access documentation, and RedisAI quantization workflow. No immediate tasks required.
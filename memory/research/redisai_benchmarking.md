**RedisAI Quantization Workflow**  
1. Convert models using:  
   `python -m tf2onnx.convert --saved_model <model> --output <model.onnx>`  
2. Quantize with ONNX Runtime:  
   `python -m onnxruntime.quantization.quantize --input <model.onnx> --output <quantized.onnx>`  
3. Test in Redis:  
   `REDISCLI AI.MODEL LOAD <quantized.onnx>`  

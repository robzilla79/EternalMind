@echo off
setlocal EnableExtensions

REM Configure and rebuild local-em so Ollama uses a 64k context window.
set "REPO_DIR=%~dp0.."
set "MODELFILE=%REPO_DIR%\Modelfile.qwen3"

if not exist "%MODELFILE%" (
    echo ERROR: Could not find Modelfile at "%MODELFILE%"
    exit /b 1
)

where ollama >nul 2>&1
if errorlevel 1 (
    echo ERROR: ollama CLI not found in PATH.
    echo Install Ollama or add it to PATH, then rerun this script.
    exit /b 1
)

echo [1/3] Setting runtime context variables to 64k...
set "EM_NUM_CTX=65536"
set "OLLAMA_CONTEXT_LENGTH=65536"

echo [2/3] Persisting variables for future shells...
setx EM_NUM_CTX 65536 >nul
setx OLLAMA_CONTEXT_LENGTH 65536 >nul

echo [3/3] Rebuilding local-em model with 64k context...
ollama create local-em -f "%MODELFILE%"
if errorlevel 1 (
    echo ERROR: Failed to rebuild local-em model.
    exit /b 1
)

echo.
echo Success: local-em is configured for 64k context.
echo Start Local-Em in this shell with:
echo   python "%REPO_DIR%\local_em.py"

endlocal

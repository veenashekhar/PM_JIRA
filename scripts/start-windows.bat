@echo off

if exist .env (
	for /f "usebackq tokens=1* delims==" %%A in (".env") do set %%A=%%B
)

docker rm -f pm-mvp 2>NUL

docker build -t pm-mvp .
docker run --name pm-mvp -p 8000:8000 -e OPENROUTER_API_KEY=%OPENROUTER_API_KEY% -d pm-mvp

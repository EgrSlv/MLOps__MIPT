# Предварительно нужно создать key.txt и положить в него API-ключ
# для xtunnel, иначе работать не будет ничего
XTUNNEL_API_KEY=$(cat key.txt)

!./xtunnel register $XTUNNEL_API_KEY > /dev/null 2>&1

uvicorn app:app --host 127.0.0.1 --port 8002 --loop asyncio & ./xtunnel http 8002 & wait

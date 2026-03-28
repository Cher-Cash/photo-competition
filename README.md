1. создать .env прописать переменные окружения как в файле примере
2. python3 -m venv venv
3. source venv/bin/activate
4. pip install -r requirements.txt
5. Установить docker и minio (устанавливается глобально):
    - sudo apt update
    - sudo apt install apt-transport-https ca-certificates curl software-properties-common
    - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    - sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    - sudo apt update
    - sudo apt install docker-ce
    - # Проверить, что Docker запущен sudo systemctl status docker
    - mkdir -p ~/minio/data
    - добавить своего пользователя в группу docker для запуска без sudo:
      - sudo groupadd docker
      - sudo usermod -aG docker $USER
      - newgrp docker
    - docker run -p 9000:9000 --name minio -v ~/minio/data:/data -e "MINIO_ROOT_USER=admin" -e "MINIO_ROOT_PASSWORD=password123" minio/minio server /data
    - при последующих запусках минио использовать команду docker start minio
6. Применить миграцию с помощью команды flask db upgrade
# API Flask com MongoDB, Elasticsearch e Swagger

Esta é uma API Flask que se integra ao MongoDB para armazenamento de dados de usuários, ao Elasticsearch para indexação de logs e ao Swagger para documentação da API.

## Tecnologias utilizadas

* Flask
* MongoDB
* Elasticsearch
* Swagger
* Docker

## Instalação

1. Certifique-se de ter o Docker instalado.
2. Clone este repositório: `git clone https://github.com/JoaoVitorChaves-05/TargetData.git`
3. Gere a imagem do projeto com o Docker: `docker build -t api .`
4. Inicie os serviços do MongoDB e Elasticsearch: `docker-compose up`
5. Inicie a imagem gerada pelo Docker: `docker run -p 5000:5000 api`

## Uso

* Acesse a documentação da API em http://localhost:5000/docs para visualizar e testar os endpoints.
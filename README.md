# API Flask com MongoDB, Elasticsearch e Swagger

Esta é uma API Flask que se integra ao MongoDB para armazenamento de dados de usuários, ao Elasticsearch para indexação de logs e ao Swagger para documentação da API.

## Tecnologias utilizadas

* Flask
* MongoDB
* Elasticsearch
* Swagger
* Docker

## Instalação

1. Certifique-se de ter o Docker e o Git instalado.
2. Clone este repositório: `git clone https://github.com/JoaoVitorChaves-05/TargetData.git`
3. Entre na pasta: `cd TargetData`
4. Inicie os serviços do MongoDB, Elasticsearch e o Flask: `docker compose up`

## Uso

* Acesse a documentação da API em http://localhost:5000/docs para visualizar e testar os endpoints.

## Exemplos

### Criando usuário

![Criando um usuário na rota "/docs"](/images/post_user_request.png)
![Resultado do request](/images/post_user_result.png)

### Gerando um token de um usuário cadastrado

![Gerando token de um usuário cadastrado na rota "/docs"](/images/token_request.png)
![Resultado do request](/images/token_result.png)

### Consultando um CEP para ver a previsão do tempo

![Consultando um CEP para ver a previsão do tempo na rota "/docs"](/images/cep_request.png)
![Resultado do request](/images/cep_result.png)

### Consultando os logs de um usuário cadastrado

![Consultando os logs de um usuário cadastrado na rota "/docs"](/images/log_request.png)
![Resultado do request](/images/log_result.png)
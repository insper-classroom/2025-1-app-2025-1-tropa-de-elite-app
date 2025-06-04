# Integração com o Backend

Este documento explica como foi estruturada a integração entre o frontend e o backend da aplicação de detecção de fraudes, e o que precisa ser ajustado quando o backend estiver 100% pronto.

## Arquitetura Atual

A aplicação está configurada para funcionar em dois modos:

1. **Modo de Simulação (Desenvolvimento)**: Usando dados simulados para permitir o desenvolvimento do frontend sem dependência do backend.
2. **Modo de Integração**: Configurado para se comunicar com o backend real quando estiver disponível.

## Arquivo Principal de Integração

O arquivo `api-integration-ready.ts` contém todas as funções necessárias para comunicação com o backend, com as seguintes características:

- Controle de simulação via variável de ambiente `NEXT_PUBLIC_USE_SIMULATION`
- Timeouts configuráveis para diferentes tipos de requisições
- Tratamento de erros aprimorado
- Funções para geração de dados simulados durante o desenvolvimento

## Endpoints do Backend

O backend expõe os seguintes endpoints principais:

- `/predict_only_transactions` - Para processamento em lote de transações
- `/health` - Para verificação de saúde do sistema
- `/logs` - Para obtenção de registros históricos (a ser implementado)

## Configuração para Integração com Backend Real

Quando o backend estiver 100% pronto, siga os passos abaixo:

1. **Configurar Variáveis de Ambiente**:
   - Definir `NEXT_PUBLIC_USE_SIMULATION=false` para desativar a simulação
   - Configurar `NEXT_PUBLIC_API_URL` e `NEXT_PUBLIC_FRAUD_API_URL` com os endereços corretos do backend

2. **Verificar Formato das Respostas**:
   - Confirmar se o formato das respostas do backend corresponde ao esperado pelo frontend
   - Adaptar o cliente API conforme necessário para mapear respostas diferentes

3. **Testar Progressivamente**:
   - Testar cada endpoint individualmente
   - Começar com o endpoint de health check
   - Em seguida, testar o processamento em lote
   - Por fim, testar a obtenção de logs

## Ajustes Necessários ao Migrar para o Backend Real

1. **Adaptação de Endpoints**:
   - Verificar se os endpoints do backend correspondem exatamente aos utilizados no frontend
   - Atualizar URLs no arquivo `api-integration-ready.ts` se necessário

2. **Formato de Resposta**:
   - Se o backend retornar dados em formato diferente do esperado, adaptar as funções do cliente API

3. **Tratamento de Erros**:
   - Verificar se os códigos de erro do backend estão sendo tratados corretamente
   - Adaptar mensagens de erro para corresponder às retornadas pelo backend

4. **Autenticação**:
   - Adicionar lógica de autenticação quando implementada no backend
   - Incluir tokens de autenticação nas requisições

## Testando a Integração

Para testar a integração com o backend:

1. Configure as variáveis de ambiente como mencionado acima
2. Verifique se o backend está rodando e acessível
3. Teste cada funcionalidade separadamente:
   - Upload de arquivo para processamento em lote
   - Verificação de status de jobs
   - Visualização de logs históricos

## Depuração

Se encontrar problemas durante a integração:

1. Verifique os logs do console para mensagens de erro detalhadas
2. Use ferramentas como o DevTools do navegador para inspecionar requisições de rede
3. Confirme se o backend está retornando os formatos de resposta esperados
4. Verifique timeouts e certifique-se de que estão configurados adequadamente para sua rede

## Simulação vs. Backend Real

A aplicação usa o modo de simulação por padrão. Para usar o backend real:

1. Defina a variável de ambiente `NEXT_PUBLIC_USE_SIMULATION=false`
2. Verifique se o backend está rodando e acessível
3. Teste cada funcionalidade separadamente

A transição deve ser suave, pois o código foi preparado para funcionar em ambos os modos.

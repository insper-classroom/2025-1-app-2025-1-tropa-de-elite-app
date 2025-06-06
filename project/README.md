# Sistema de Detecção de Fraudes - Frontend

## Configurações para Arquivos Grandes

Este projeto foi configurado para suportar upload de arquivos grandes (até 100MB) para processamento de transações em lote.

### Formatos Suportados

- **CSV** (.csv) - Formato padrão separado por vírgulas
- **Feather** (.feather) - Formato binário otimizado do Apache Arrow
- **Parquet** (.parquet) - Formato colunar comprimido

### Configurações Implementadas

#### Frontend (Next.js)
- `next.config.js`: Configurado para aceitar uploads de até 100MB
- Componente `FileUploader`: Suporte a múltiplos formatos com validação
- Barra de progresso durante upload
- Timeout aumentado para requisições grandes

#### API Service
- Timeout configurado para 5 minutos (300 segundos)
- Progress callback para uploads grandes
- Headers de content-type apropriados

### Como Usar

1. **Inicie o backend** (se ainda não estiver rodando):
   ```bash
   cd back_end
   python start_server.py
   ```

2. **Inicie o frontend**:
   ```bash
   cd project
   npm install
   npm run dev
   ```

3. **Faça upload do arquivo**:
   - Arraste e solte o arquivo na área designada
   - Ou clique para selecionar o arquivo
   - Formatos aceitos: CSV, Feather, Parquet
   - Tamanho máximo: 100MB

4. **Acompanhe o progresso**:
   - Uma barra de progresso será exibida durante o upload
   - O processamento continua após o upload ser concluído

### Limitações

- **Tamanho máximo**: 100MB por arquivo
- **Formatos**: Apenas CSV, Feather e Parquet
- **Timeout**: 5 minutos para processamento completo
- **Colunas obrigatórias**: O arquivo deve conter a coluna `transaction_id`

### Troubleshooting

#### Erro 413 (Request Entity Too Large)
- Verifique se o arquivo não excede 100MB
- Tente comprimir os dados usando formato Feather ou Parquet

#### Timeout durante upload
- Verifique a conexão de internet
- Arquivos muito grandes podem precisar de mais tempo

#### Formato não suportado
- Converta o arquivo para CSV, Feather ou Parquet
- Verifique a extensão do arquivo

### Environment Variables

Crie um arquivo `.env.local` na pasta do projeto com:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Para produção, substitua pela URL do servidor de produção.

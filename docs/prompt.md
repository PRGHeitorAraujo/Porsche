# Prompt e iterações

A dashboard foi gerada pelo caminho do **agente com skill**: um agente (Claude) com acesso à base e a uma skill de visualização de dados (regras de forma de gráfico, cor, rótulos, hover e acessibilidade).

## Prompt final

```
Tenho uma planilha com 100 vendas da Porsche (aba "Sanitized"), com o dado cru e o
sanitizado lado a lado. Use só as colunas sanitizadas.

Antes de desenhar:
- converta preço, ano do modelo e quilometragem em número;
- remova customer_name e salesperson (a base vai embutida no HTML, então nada pessoal);
- crie a família do modelo (911, 718, Cayenne, Macan, Taycan, Panamera);
- agrupe os status de entrega em Entregue / Em andamento / Cancelada;
- para as datas INVALID, olhe a data crua: se dia e mês estiverem trocados (AAAA/DD/MM),
  recupere; se o dia for impossível (30/02, 31/04), guarde só ano e mês.

Gere uma dashboard em HTML, arquivo único, sem framework, que responda:
1. Qual família de modelo traz mais receita — pelo volume ou pelo ticket?
2. Quais estados concentram a receita?
3. Como o cliente paga — e o método de pagamento muda o ticket?

Requisitos:
- KPIs no topo: nº de vendas, receita, ticket médio e % da receita já entregue;
- filtros: família, modelo, estado, cidade, ano da venda, ano do modelo, pagamento e entrega;
- clicar numa barra filtra a dashboard inteira;
- cada pergunta com uma frase de conclusão que se recalcula com o filtro;
- tabela com as vendas do recorte;
- visual: off-white, grafite e um vermelho de destaque, tipografia larga (Archivo),
  modo escuro, funcionando no celular.
```

## O que mudou até a versão final

| Versão | O que estava | O que mudou |
|---|---|---|
| 1 | Pergunta 2 com uma barra “Outros” juntando 25 estados | “Outros” virou a maior barra (43% da receita) e esmagou o top 8. Virou uma linha de texto embaixo do gráfico, e a conclusão passou a dizer que a receita é pulverizada. |
| 1 | “Transferência internacional (wire)” como rótulo | Cortava no gráfico. Encurtei para “Transf. internacional” no script de tratamento. |
| 1 | Pagamento em um gráfico só, com nº de vendas e ticket | Dois eixos diferentes num gráfico só confundem. Separei em duas listas lado a lado, na mesma ordem. |
| 1 | No celular, barra e valores na mesma linha | A barra ficava minúscula. No mobile, o valor vai pra cima e a barra ocupa a largura toda. |
| 1 | Botão de tema com ícone ◐ | Ícone não aparecia sem a fonte carregada. Virou texto (“Tema escuro / Tema claro”). |

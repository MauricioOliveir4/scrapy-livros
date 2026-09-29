# Web Scraping com Scrapy: Monitor de Catálogo de Livraria

**Grupo 01: biblioteca Scrapy**

## 1. Motivação (caso de uso)

Uma livraria pequena quer **acompanhar o catálogo de um concorrente** para decidir preços e compras. Copiar à mão preço, estoque e avaliação de 1000 livros espalhados em 50 páginas levaria horas e ficaria desatualizado logo. Com um robô (*crawler*) a coleta leva menos de um minuto e pode ser repetida todo dia.

Com os dados coletados, a livraria consegue responder:

- Qual é o **preço médio por categoria**? Serve de referência para a própria tabela de preços.
- Livros **mais bem avaliados custam mais**?
- Quais livros têm **5 estrelas e custam menos de £20**? São boas oportunidades de compra.
- Quais livros estão com **estoque crítico** (2 unidades ou menos)?
- Quais **séries** o concorrente trabalha, e quais **temas** aparecem mais nas descrições?

O site usado é o [books.toscrape.com](https://books.toscrape.com), uma livraria fictícia criada para praticar web scraping. Por isso a coleta é legal e não prejudica ninguém.

## 2. Como executar

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt

scrapy crawl livros             # coleta e gera dados/livros.json e dados/livros.csv
python analise.py               # mineração / estatísticas
```

## 3. Como a biblioteca Scrapy funciona

O Scrapy é um **framework** de scraping, e não só uma biblioteca de requisições. Ele cuida do download, do agendamento, da concorrência e da exportação. O programador escreve só as regras de extração.

```
          ┌──────────────┐  Requests   ┌────────────┐   ┌─────────────┐
          │    SPIDER    │ ──────────► │ SCHEDULER  │──►│ DOWNLOADER  │──► Internet
          │ (nosso código│             │  (fila)    │   │ (HTTP async)│
          │   de parse)  │ ◄────────── └────────────┘   └─────────────┘
          └──────┬───────┘  Responses          ▲  ENGINE coordena tudo  │
                 │ Items                       └────────────────────────┘
                 ▼
         ┌────────────────┐     ┌──────────────────┐
         │ ITEM PIPELINES │ ──► │ FEED EXPORTS     │ ──► JSON / CSV
         │ (limpar/validar)│    │ (settings.FEEDS) │
         └────────────────┘     └──────────────────┘
```

| Componente | Função |
|---|---|
| **Engine** | Controla o fluxo de dados entre todos os componentes. |
| **Scheduler** | Fila de URLs a visitar. Descarta URLs repetidas automaticamente. |
| **Downloader** | Faz as requisições HTTP de forma **assíncrona** (baseado no Twisted), baixando várias páginas ao mesmo tempo. |
| **Spider** | Classe escrita por nós. Recebe cada `Response` e devolve (`yield`) novos `Request`s ou `Item`s. |
| **Selectors** | Extraem dados do HTML com **CSS** (`response.css(...)`) ou **XPath** (`response.xpath(...)`), e aceitam **regex** com `.re()` / `.re_first()`. |
| **Item Pipelines** | Processam cada item depois da extração: limpeza, validação, remoção de duplicados, gravação. |
| **Feed Exports** | Salvam os itens em JSON, CSV, XML etc. sem código extra. |

Como os callbacks usam `yield`, o Scrapy não espera uma página terminar para pedir a próxima. É por isso que ele coleta 1000 páginas em poucos segundos.

## 4. Estrutura do projeto

```
scrapy.cfg                     # indica onde estão as configurações
livros/
├── settings.py                # configurações: delay, robots.txt, cache, pipelines, exportação
├── items.py                   # LivroItem: os campos que coletamos
├── pipelines.py               # LimpezaPipeline e DuplicadosPipeline
└── spiders/
    └── livros_spider.py       # o spider (lógica de navegação e extração)
analise.py                     # mineração dos dados coletados
dados/livros.json | livros.csv # resultado
```

## 5. Lógica do código

### 5.1 Spider ([livros/spiders/livros_spider.py](livros/spiders/livros_spider.py))

1. **`start_urls`** começa na página inicial do catálogo.
2. **`parse()`** trata cada página de listagem:
   - seleciona os links de todos os livros (`article.product_pod h3 a::attr(href)`) e cria um `Request` para cada um, com callback `parse_livro`;
   - procura o botão **next** (`li.next a`). Se existir, segue para a próxima página chamando `parse` de novo. Isso percorre as 50 páginas (**paginação recursiva**).
3. **`parse_livro()`** trata a página de detalhe de cada livro e extrai:
   - título (CSS `h1`), categoria (3º item do *breadcrumb*), UPC (XPath: célula ao lado do `<th>UPC</th>`), descrição;
   - **preço, estoque, avaliação e id** usando **expressões regulares** (seção 6).
4. Cada livro vira um `LivroItem` e é enviado com `yield` para os pipelines.

### 5.2 Pipelines ([livros/pipelines.py](livros/pipelines.py))

- **`LimpezaPipeline`**: tira espaços extras, remove o sufixo `...more` das descrições e **descarta** (`DropItem`) itens sem preço ou com UPC inválido.
- **`DuplicadosPipeline`**: guarda os UPCs já vistos num `set` e descarta repetidos.

### 5.3 Configurações ([livros/settings.py](livros/settings.py))

- `ROBOTSTXT_OBEY = True`, `DOWNLOAD_DELAY` e `AUTOTHROTTLE` fazem um scraping "educado", que não sobrecarrega o servidor.
- `HTTPCACHE_ENABLED`: rodar de novo não baixa as páginas outra vez.
- `FEEDS` exporta automaticamente para `dados/livros.json` e `dados/livros.csv`.

### 5.4 Mineração ([analise.py](analise.py))

Lê o JSON e calcula as estatísticas por categoria, a relação entre avaliação e preço, as oportunidades (5 estrelas e barato), o estoque crítico, as palavras mais frequentes nas descrições e as séries de livros.

## 6. Expressões regulares utilizadas

| Onde | Regex | Exemplo de entrada | Resultado | Explicação |
|---|---|---|---|---|
| Spider: preço | `£?\s*(\d+(?:\.\d{1,2})?)` | `£51.77` | `51.77` | `£?` é o símbolo opcional; `\d+` a parte inteira; `(?:\.\d{1,2})?` os centavos opcionais (grupo sem captura). Usada com `.re_first()` do Scrapy. |
| Spider: estoque | `\((\d+)\s+available\)` | `In stock (22 available)` | `22` | `\(` e `\)` são parênteses literais; `(\d+)` captura o número. |
| Spider: avaliação | `star-rating\s+(One\|Two\|Three\|Four\|Five)` | `class="star-rating Three"` | `Three` → 3 | A nota está só no **nome da classe CSS**. A alternância `\|` captura a palavra, que um dicionário converte em número. |
| Spider: id | `_(\d+)/index\.html$` | `.../a-light-in-the-attic_1000/index.html` | `1000` | `\.` é o ponto literal; `$` ancora no fim da URL. |
| Pipeline: espaços | `\s+` | `"Título\n   longo"` | `"Título longo"` | Troca qualquer sequência de espaços/quebras por um espaço só. |
| Pipeline: UPC | `^[0-9a-f]{16}$` | `a897fe39b1053632` | válido | `^...$` exige que a string inteira tenha exatamente 16 caracteres hexadecimais. |
| Pipeline: "...more" | `\s*\.{3}\s*more$` | `"...texto ...more"` | `"...texto"` | `\.{3}` são três pontos literais no fim do texto. |
| Análise: palavras | `\b[a-z]{5,}\b` | descrições | `world`, `story`… | `\b` é a fronteira de palavra; `{5,}` pede 5 letras ou mais (ignora palavras curtas como "the"). |
| Análise: séries | `\(([^#]+?),?\s*#(\d+)(?:-\d+)?\)$` | `Saga, Volume 5 (Saga (Collected Editions) #5)` | `Saga (Collected Editions)`, `5` | `[^#]+?` pega o nome da série (não guloso); `,?` aceita "(Série, #1)" e "(Série #1)"; `(?:-\d+)?` aceita intervalos como `#11-15`. |

## 7. Resultados obtidos

Coleta (`scrapy crawl livros`): **1000 livros** em 50 páginas de listagem mais 1000 páginas de detalhe, sem erros.

Exemplo de item coletado:

```json
{
  "id": 981,
  "titulo": "It's Only the Himalayas",
  "categoria": "Travel",
  "preco": 45.17,
  "avaliacao": 2,
  "estoque": 19,
  "upc": "a22124811bfa8350",
  "url": "https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html"
}
```

Principais descobertas (`python analise.py`):

- O preço médio fica entre £31 e £40 em todas as categorias (Fantasy é a mais cara: £39,59).
- **A avaliação quase não influencia o preço**: a média vai de £34,56 (1 estrela) a £36,09 (4 estrelas).
- **42 livros com 5 estrelas custam menos de £20.** O mais barato é *An Abundance of Katherines*, a £10,00.
- **112 livros** estão com estoque crítico (2 unidades ou menos).
- **307 livros** fazem parte de séries (Fruits Basket, Harry Potter, Saga…).
- Palavras mais comuns nas descrições: *world, story, years, family, author*.

## 8. Considerações éticas

Scraping deve respeitar o `robots.txt` e os termos de uso do site, e não pode sobrecarregar o servidor. Neste projeto isso é garantido por `ROBOTSTXT_OBEY`, `DOWNLOAD_DELAY` e `AUTOTHROTTLE`. O site-alvo foi feito para esse tipo de prática.

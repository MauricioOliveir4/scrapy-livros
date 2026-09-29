"""Mineração dos dados coletados pelo spider (dados/livros.json)."""
import json
import re
from collections import Counter, defaultdict
from statistics import mean

with open("dados/livros.json", encoding="utf-8") as f:
    livros = json.load(f)

print(f"Total de livros coletados: {len(livros)}\n")

# 1) Preço médio e estoque por categoria
por_categoria = defaultdict(list)
for livro in livros:
    por_categoria[livro["categoria"]].append(livro)

print("Top 10 categorias com mais títulos:")
print(f"{'Categoria':<22}{'Qtd':>5}{'Preço médio':>14}{'Estoque':>10}")
for cat, itens in sorted(por_categoria.items(), key=lambda kv: -len(kv[1]))[:10]:
    print(f"{cat:<22}{len(itens):>5}{mean(l['preco'] for l in itens):>13.2f}£"
          f"{sum(l['estoque'] for l in itens):>10}")

# 2) Relação entre avaliação e preço
print("\nPreço médio por avaliação (estrelas):")
for estrelas in range(1, 6):
    precos = [l["preco"] for l in livros if l["avaliacao"] == estrelas]
    print(f"  {'★' * estrelas:<6} {len(precos):>4} livros   média £{mean(precos):.2f}")

# 3) Oportunidades: livros bem avaliados (5★) e baratos (< £20)
baratos = sorted((l for l in livros if l["avaliacao"] == 5 and l["preco"] < 20),
                 key=lambda l: l["preco"])
print(f"\nLivros 5★ abaixo de £20: {len(baratos)}")
for l in baratos[:5]:
    print(f"  £{l['preco']:>6.2f}  {l['titulo'][:60]}")

# 4) Estoque crítico (reposição)
criticos = [l for l in livros if l["estoque"] <= 2]
print(f"\nLivros com estoque crítico (≤ 2 unidades): {len(criticos)}")

# 5) Mineração de texto: palavras mais frequentes nas descrições (regex)
RE_PALAVRA = re.compile(r"\b[a-z]{5,}\b")  # palavras com 5+ letras
STOPWORDS = {"which", "their", "there", "about", "would", "these", "other", "after",
             "where", "while", "being", "every", "through", "still", "first", "never"}
contagem = Counter(
    p for l in livros for p in RE_PALAVRA.findall((l["descricao"] or "").lower())
    if p not in STOPWORDS
)
print("\nPalavras mais frequentes nas descrições:")
print("  " + ", ".join(f"{p} ({n})" for p, n in contagem.most_common(12)))

# 6) Títulos que são parte de séries: "(Nome da Série #3)", "(Série, #1)", "(Série #11-15)"
RE_SERIE = re.compile(r"\(([^#]+?),?\s*#(\d+)(?:-\d+)?\)$")
series = Counter(m.group(1).strip() for l in livros if (m := RE_SERIE.search(l["titulo"])))
print(f"\nLivros que fazem parte de séries: {sum(series.values())}")
for nome, n in series.most_common(5):
    print(f"  {nome}: {n} volume(s)")

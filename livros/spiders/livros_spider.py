import re

import scrapy

from livros.items import LivroItem

# ---------------------------------------------------------------------------
# Expressões regulares usadas na extração
# ---------------------------------------------------------------------------
# Preço: "£51.77" -> 51.77  (símbolo de moeda opcional, parte decimal opcional)
RE_PRECO = r"£?\s*(\d+(?:\.\d{1,2})?)"
# Estoque: "In stock (22 available)" -> 22
RE_ESTOQUE = re.compile(r"\((\d+)\s+available\)")
# Avaliação: class="star-rating Three" -> "Three"
RE_ESTRELAS = re.compile(r"star-rating\s+(One|Two|Three|Four|Five)")
# ID do livro na URL: ".../a-light-in-the-attic_1000/index.html" -> 1000
RE_ID_URL = re.compile(r"_(\d+)/index\.html$")

ESTRELAS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class LivrosSpider(scrapy.Spider):
    name = "livros"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def parse(self, response):
        """Página de listagem: segue cada livro e depois a próxima página."""
        for link in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(link, callback=self.parse_livro)

        proxima = response.css("li.next a::attr(href)").get()
        if proxima:
            yield response.follow(proxima, callback=self.parse)

    def parse_livro(self, response):
        """Página de detalhe: extrai os campos do livro."""
        item = LivroItem()
        item["url"] = response.url

        id_match = RE_ID_URL.search(response.url)
        item["id"] = int(id_match.group(1)) if id_match else None

        item["titulo"] = response.css("div.product_main h1::text").get(default="")
        # 3º link do breadcrumb = categoria (Home > Books > Categoria > Livro)
        item["categoria"] = response.css("ul.breadcrumb li:nth-child(3) a::text").get(default="").strip()

        # .re_first() aplica a regex direto no seletor do Scrapy
        preco = response.css("div.product_main p.price_color::text").re_first(RE_PRECO)
        item["preco"] = float(preco) if preco else None

        classe = response.css("div.product_main p.star-rating::attr(class)").get(default="")
        estrelas = RE_ESTRELAS.search(classe)
        item["avaliacao"] = ESTRELAS[estrelas.group(1)] if estrelas else None

        disponibilidade = " ".join(response.css("div.product_main p.availability::text").getall())
        estoque = RE_ESTOQUE.search(disponibilidade)
        item["estoque"] = int(estoque.group(1)) if estoque else 0

        item["upc"] = response.xpath("//th[text()='UPC']/following-sibling::td/text()").get()
        item["descricao"] = response.css("#product_description + p::text").get()

        yield item

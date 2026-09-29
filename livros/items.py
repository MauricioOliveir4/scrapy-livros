import scrapy


class LivroItem(scrapy.Item):
    """Estrutura de cada livro coletado."""
    id = scrapy.Field()
    titulo = scrapy.Field()
    categoria = scrapy.Field()
    preco = scrapy.Field()        # float, em libras (£)
    avaliacao = scrapy.Field()    # 1 a 5 estrelas
    estoque = scrapy.Field()      # quantidade disponível
    upc = scrapy.Field()
    descricao = scrapy.Field()
    url = scrapy.Field()

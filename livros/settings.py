# Configurações do projeto Scrapy "livros"

BOT_NAME = "livros"
SPIDER_MODULES = ["livros.spiders"]
NEWSPIDER_MODULE = "livros.spiders"

# Scraping "educado": respeita o robots.txt e não sobrecarrega o servidor
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 0.25
AUTOTHROTTLE_ENABLED = True

# Cache HTTP: rodar de novo não baixa as páginas outra vez
HTTPCACHE_ENABLED = True

ITEM_PIPELINES = {
    "livros.pipelines.LimpezaPipeline": 100,
    "livros.pipelines.DuplicadosPipeline": 200,
}

# Exporta automaticamente para JSON e CSV
FEEDS = {
    "dados/livros.json": {"format": "json", "encoding": "utf8", "indent": 2, "overwrite": True},
    "dados/livros.csv": {"format": "csv", "encoding": "utf8", "overwrite": True},
}

LOG_LEVEL = "INFO"
FEED_EXPORT_ENCODING = "utf-8"

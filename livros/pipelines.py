import re

from scrapy.exceptions import DropItem

# Regex usadas na limpeza
RE_ESPACOS = re.compile(r"\s+")                 # qualquer sequência de espaços/quebras de linha
RE_UPC = re.compile(r"^[0-9a-f]{16}$")          # UPC válido: 16 caracteres hexadecimais
RE_SUFIXO_MORE = re.compile(r"\s*\.{3}\s*more$")  # "...more" no fim das descrições


class LimpezaPipeline:
    """Normaliza textos e valida campos obrigatórios."""

    def process_item(self, item, spider):
        item["titulo"] = RE_ESPACOS.sub(" ", item["titulo"]).strip()

        descricao = item.get("descricao") or ""
        descricao = RE_ESPACOS.sub(" ", descricao).strip()
        item["descricao"] = RE_SUFIXO_MORE.sub("", descricao)

        if item.get("preco") is None:
            raise DropItem(f"Livro sem preço: {item['url']}")
        if not RE_UPC.match(item.get("upc") or ""):
            raise DropItem(f"UPC inválido ({item.get('upc')}): {item['url']}")
        return item


class DuplicadosPipeline:
    """Descarta livros repetidos (mesmo UPC)."""

    def __init__(self):
        self.vistos = set()

    def process_item(self, item, spider):
        if item["upc"] in self.vistos:
            raise DropItem(f"Duplicado: {item['titulo']}")
        self.vistos.add(item["upc"])
        return item

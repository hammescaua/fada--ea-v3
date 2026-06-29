"""Base de Conhecimento — carrega os coeficientes agronômicos e o catálogo de insumos.

Externaliza para JSON **auditável e com fonte** (em ``data/knowledge/``) os coeficientes
que antes ficavam embutidos no código, e o catálogo de insumos com preço de referência.
Assim a ferramenta "sabe o quanto cada variável impacta" a partir de uma fonte rastreável
(Embrapa, CQFS-RS/SC, FAO-56, ZARC), e não de números mágicos no código.

Carregamento tolerante a falha: se os arquivos não forem encontrados, retorna vazio e os
módulos do motor caem nos seus defaults — o engine nunca quebra por falta da KB.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


def _find_kb_dir() -> Path | None:
    """Procura ``data/knowledge`` subindo a partir deste arquivo (monorepo)."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "data" / "knowledge"
        if candidate.is_dir():
            return candidate
    return None


@lru_cache(maxsize=1)
def _load(name: str) -> dict:
    kb_dir = _find_kb_dir()
    if not kb_dir:
        return {}
    path = kb_dir / name
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def responses() -> dict:
    return _load("agronomic_responses.json")


def inputs() -> dict:
    return _load("inputs_catalog.json").get("inputs", {})


def get_input(key: str) -> dict | None:
    return inputs().get(key)


def data_sources() -> dict:
    """Ficha de proveniência/acurácia por grupo de variável (de onde vem cada dado)."""
    return _load("data_sources.json").get("groups", {})


def operations() -> dict:
    """Mapa canônico de manejos (janela, fator IPPD alvo, insumo associado)."""
    return _load("operations_catalog.json").get("operations", {})


def manejo_evidence() -> dict:
    """Evidência científica por manejo (mecanismo, coeficiente citado, personalização)."""
    return _load("manejo_evidence.json").get("manejos", {})


def param(path: str, default=None):
    """Lê um coeficiente por caminho pontilhado, ex.: ``'calagem.v_alvo_soja'``.

    Cada folha no JSON é ``{"value": ..., "source": ...}``; retorna ``value``.
    """
    node: object = responses()
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node if node is not None else default


def source(path: str) -> str | None:
    """Fonte citada de um coeficiente (para exibir/auditar)."""
    node: object = responses()
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node.get("source") if isinstance(node, dict) else None

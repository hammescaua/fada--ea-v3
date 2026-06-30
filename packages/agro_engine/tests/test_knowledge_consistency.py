"""Consistência da base de conhecimento — guarda contra divergência entre os JSONs/motores.

Não testa valores agronômicos (isso é literatura); testa que as referências cruzadas
resolvem, que os pesos estão no intervalo e que os motores e os catálogos concordam.
"""

from __future__ import annotations

from agro_engine import kb
from agro_engine.reasoning import _DIRECT_CAUSE


def test_impact_graph_cobre_as_causas_do_reasoning():
    graph = kb.impact_graph()
    need = set(_DIRECT_CAUSE.values()) | {"baixo_fosforo", "baixo_potassio"}
    assert need <= set(graph), f"causas ausentes no impact_graph: {need - set(graph)}"


def test_impact_graph_cadeias_completas_e_pesos_validos():
    for key, node in kb.impact_graph().items():
        for campo in ("cadeia", "fonte", "confirma_se", "acao", "controlabilidade", "confianca_cientifica", "fator"):
            assert campo in node, f"{key} sem '{campo}'"
        assert node["controlabilidade"] in {"sim", "parcial", "nao"}
        for e in node["cadeia"]:
            assert "passo" in e and 0 < e.get("peso", 1) <= 1, f"peso inválido em {key}"


def test_operations_referenciam_insumos_existentes():
    ops, inputs = kb.operations(), kb.inputs()
    for key, op in ops.items():
        insumo = op.get("insumo")
        assert insumo is None or insumo in inputs, f"{key} referencia insumo inexistente: {insumo}"


def test_manejo_evidence_referencia_coeficientes_existentes():
    for key, ev in kb.manejo_evidence().items():
        ref = ev.get("coeficiente", {}).get("ref")
        assert ref is None or kb.param(ref) is not None, f"{key} referencia coeficiente inexistente: {ref}"

"""Seed do banco — catálogo de cultivares e uma fazenda-demo do Noroeste do RS.

Uso: `python seed.py` (requer banco PostGIS no ar e migrations aplicadas).
"""

from __future__ import annotations

from app.db import get_engine
from app.models import Cultivar, Farm, Field
from sqlalchemy.orm import Session

CULTIVARS = [
    {"name": "GMR 5.2 precoce", "maturity_group": 5.2, "base_potential_sc_ha": 92, "cycle_days": 120, "disease_tolerance": 0.5},
    {"name": "GMR 5.5 média", "maturity_group": 5.5, "base_potential_sc_ha": 95, "cycle_days": 130, "disease_tolerance": 0.6},
    {"name": "GMR 6.2 tardia", "maturity_group": 6.2, "base_potential_sc_ha": 98, "cycle_days": 140, "disease_tolerance": 0.4},
]


def main() -> None:
    engine = get_engine()
    with Session(engine) as db:
        if db.query(Cultivar).count() == 0:
            db.add_all(Cultivar(**c) for c in CULTIVARS)
        if db.query(Farm).count() == 0:
            farm = Farm(name="Fazenda Demonstração", municipality="Santo Ângelo")
            db.add(farm)
            db.flush()
            db.add(
                Field(
                    farm_id=farm.id,
                    name="Talhão 07",
                    municipality="Santo Ângelo",
                    area_ha=86.0,
                    centroid_lat=-28.30,
                    centroid_lon=-54.26,
                )
            )
        db.commit()
    print("Seed concluído: cultivares + fazenda-demo.")


if __name__ == "__main__":
    main()

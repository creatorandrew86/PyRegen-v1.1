from .cold_side_models import (
    gnielinski,
    sieder_tate,
    dittus_boelter,
    bishop,
    jackson,
)
from .hot_side_models import (
    bartz,
    bartz_corrected,
)
from .pressure_drop_models import (
    colebrook_petukhov,
    filonenko_petukhov,
    colebrook,
)

from .wall_1d import wall_1d_fin


PRESSURE_DROP = {
    "Colebrook-Petukhov":    colebrook_petukhov,
    "Filonenko-Petukhov":    filonenko_petukhov,
    "Colebrook":             colebrook,
}

COLD_SIDE = {
    "Gnielinski":     gnielinski,
    "Sieder-Tate":    sieder_tate,
    "Dittus-Boelter": dittus_boelter,
    "Bishop et al.":  bishop,
    "Jackson":        jackson,
}

HOT_SIDE = {
    "Bartz":           bartz,
    "Bartz Corrected": bartz_corrected
}

WALL = {
    "1D": wall_1d_fin,
}
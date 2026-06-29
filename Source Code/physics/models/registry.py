from .cold_side_models import (
    cold_side_gnielinski,
    cold_side_sieder_tate,
    cold_side_dittus_boelter,
    cold_side_bishop,
    cold_side_jackson,
)
from .hot_side_models import (
    hot_side_bartz,
    hot_side_bartz_corrected,
)
from .pressure_drop_models import (
    pressure_drop_colebrook_petukhov,
    pressure_drop_filonenko_petukhov,
    pressure_drop_colebrook,
)

from .wall_1d import wall_1d_fin

PRESSURE_DROP = {
    "Colebrook-Petukhov":    pressure_drop_colebrook_petukhov,
    "Filonenko-Petukhov":    pressure_drop_filonenko_petukhov,
    "Colebrook":             pressure_drop_colebrook,
}

COLD_SIDE = {
    "Gnielinski":     cold_side_gnielinski,
    "Sieder-Tate":    cold_side_sieder_tate,
    "Dittus-Boelter": cold_side_dittus_boelter,
    "Bishop et al.":  cold_side_bishop,
    "Jackson":        cold_side_jackson,
}

HOT_SIDE = {
    "Bartz":           hot_side_bartz,
    "Bartz Corrected": hot_side_bartz_corrected
}

WALL = {
    "1D": wall_1d_fin,
}
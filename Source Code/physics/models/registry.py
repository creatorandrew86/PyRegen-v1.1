from .cold_side  import cold_side_gnielinski, cold_side_sieder_tate, cold_side_dittus_boelter
from .hot_side import hot_side_bartz
from .wall import wall_1d_fin
from .pressure_drop import (
    pressure_drop_colebrook_petukhov,
    pressure_drop_filonenko_petukhov,
    pressure_drop_colebrook,
)

PRESSURE_DROP = {
    "Colebrook-Petukhov":    pressure_drop_colebrook_petukhov,
    "Filonenko-Petukhov":    pressure_drop_filonenko_petukhov,
    "Colebrook":             pressure_drop_colebrook,
}

COLD_SIDE = {
    "Gnielinski":     cold_side_gnielinski,
    "Sieder-Tate":    cold_side_sieder_tate,
    "Dittus-Boelter": cold_side_dittus_boelter,
}

HOT_SIDE = {
    "Bartz": hot_side_bartz,
}

WALL = {
    "1D": wall_1d_fin,
}
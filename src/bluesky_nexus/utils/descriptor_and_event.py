"""Example descriptor and event documents for reference.

This file contains example structures of Bluesky 'descriptor' and
'event' documents. It is used for documentation and educational purposes
only. Helps to understand the structure of the descriptor and event
document ## generated in some bluesky run
"""

# -------------- DESCRIPTOR --------------

# # I got a new 'descriptor' document:

# {
#     "configuration": {
#         "test_mono_with_grating_cpt": {
#             "data": {
#                 "test_mono_with_grating_cpt_engry_velocity": 1,
#                 "test_mono_with_grating_cpt_engry_acceleration": 1,
#             },
#             "timestamps": {
#                 "test_mono_with_grating_cpt_engry_velocity": 1734080100.1713617,
#                 "test_mono_with_grating_cpt_engry_acceleration": 1734080100.1714287,
#             },
#             "data_keys": OrderedDict(
#                 {
#                     "test_mono_with_grating_cpt_engry_velocity": {
#                         "source": "SIM:test_mono_with_grating_cpt_engry_velocity",
#                         "dtype": "integer",
#                         "shape": [],
#                     },
#                     "test_mono_with_grating_cpt_engry_acceleration": {
#                         "source": "SIM:test_mono_with_grating_cpt_engry_acceleration",
#                         "dtype": "integer",
#                         "shape": [],
#                     },
#                 }
#             ),
#         },
#         "test_mono": {
#             "data": {"test_mono_en_velocity": 1, "test_mono_en_acceleration": 1},
#             "timestamps": {
#                 "test_mono_en_velocity": 1734080100.169335,
#                 "test_mono_en_acceleration": 1734080100.1694229,
#             },
#             "data_keys": OrderedDict(
#                 {
#                     "test_mono_en_velocity": {
#                         "source": "SIM:test_mono_en_velocity",
#                         "dtype": "integer",
#                         "shape": [],
#                     },
#                     "test_mono_en_acceleration": {
#                         "source": "SIM:test_mono_en_acceleration",
#                         "dtype": "integer",
#                         "shape": [],
#                     },
#                 }
#             ),
#         },
#     },
#     "data_keys": {
#         "test_mono_with_grating_cpt_grating_diffraction_order": {
#             "source": "SIM:test_mono_with_grating_cpt_grating_diffraction_order",
#             "dtype": "number",
#             "shape": [],
#             "object_name": "test_mono_with_grating_cpt",
#         },
#         "test_mono_with_grating_cpt_engry": {
#             "source": "SIM:test_mono_with_grating_cpt_engry",
#             "dtype": "integer",
#             "shape": [],
#             "precision": 3,
#             "object_name": "test_mono_with_grating_cpt",
#         },
#         "test_mono_with_grating_cpt_engry_setpoint": {
#             "source": "SIM:test_mono_with_grating_cpt_engry_setpoint",
#             "dtype": "integer",
#             "shape": [],
#             "precision": 3,
#             "object_name": "test_mono_with_grating_cpt",
#         },
#         "test_mono_with_grating_cpt_slit": {
#             "source": "SIM:test_mono_with_grating_cpt_slit",
#             "dtype": "number",
#             "shape": [],
#             "object_name": "test_mono_with_grating_cpt",
#         },
#         "test_mono_en": {
#             "source": "SIM:test_mono_en",
#             "dtype": "integer",
#             "shape": [],
#             "precision": 3,
#             "object_name": "test_mono",
#         },
#         "test_mono_en_setpoint": {
#             "source": "SIM:test_mono_en_setpoint",
#             "dtype": "integer",
#             "shape": [],
#             "precision": 3,
#             "object_name": "test_mono",
#         },
#         "test_mono_grating": {
#             "source": "SIM:test_mono_grating",
#             "dtype": "number",
#             "shape": [],
#             "object_name": "test_mono",
#         },
#         "test_mono_slit": {
#             "source": "SIM:test_mono_slit",
#             "dtype": "number",
#             "shape": [],
#             "object_name": "test_mono",
#         },
#     },
#     "name": "baseline",
#     "object_keys": {
#         "test_mono_with_grating_cpt": [
#             "test_mono_with_grating_cpt_grating_diffraction_order",
#             "test_mono_with_grating_cpt_engry",
#             "test_mono_with_grating_cpt_engry_setpoint",
#             "test_mono_with_grating_cpt_slit",
#         ],
#         "test_mono": [
#             "test_mono_en",
#             "test_mono_en_setpoint",
#             "test_mono_grating",
#             "test_mono_slit",
#         ],
#     },
#     "run_start": "0c9febad-800b-4cb6-b4ac-ecd08d722c12",
#     "time": 1734080102.7931254,
#     "uid": "14401337-c517-4e9d-829d-9c911c8417b4",
#     "hints": {
#         "test_mono_with_grating_cpt": {"fields": ["test_mono_with_grating_cpt_engry"]
#              },
#         "test_mono": {"fields": ["test_mono_en"]},
#     },
# }


# -------------- EVENT --------------

# # I got a new 'event' document:

# {
#     "uid": "a485cfb3-2151-487f-bf75-5b1584d16ca6",
#     "time": 1734080102.812199,
#     "data": {
#         "test_mono_en": 0,
#         "test_mono_en_setpoint": 0,
#         "test_mono_grating": 0.0,
#         "test_mono_slit": 0.0,
#         "test_mono_with_grating_cpt_grating_diffraction_order": 0.0,
#         "test_mono_with_grating_cpt_engry": 0,
#         "test_mono_with_grating_cpt_engry_setpoint": 0,
#         "test_mono_with_grating_cpt_slit": 0.0,
#     },
#     "timestamps": {
#         "test_mono_en": 1734080100.16885,
#         "test_mono_en_setpoint": 1734080100.1688466,
#         "test_mono_grating": 1734080100.170053,
#         "test_mono_slit": 1734080100.170219,
#         "test_mono_with_grating_cpt_grating_diffraction_order": 1734080100.1709294,
#         "test_mono_with_grating_cpt_engry": 1734080100.1710064,
#         "test_mono_with_grating_cpt_engry_setpoint": 1734080100.1710045,
#         "test_mono_with_grating_cpt_slit": 1734080100.171582,
#     },
#     "seq_num": 1,
#     "filled": {},
#     "descriptor": "14401337-c517-4e9d-829d-9c911c8417b4",
# }

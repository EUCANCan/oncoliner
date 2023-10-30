# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
DEFAULT_INDEL_THRESHOLD = 100
DEFAULT_WINDOW_RADIUS = 100
DEFAULT_SV_BINS = [500]
DEFAULT_CONTIGS = [str(x) for x in range(1, 23)] + ['X', 'Y']
DEFAULT_VARIANT_TYPES = ['SNV', 'INDEL-INS', 'INDEL-DUP', 'INDEL-DEL', 'SV-TRA', 'SV-INV', 'SV-DEL', 'SV-DUP']
UNION_SYMBOL = '_or_'
INTERSECTION_SYMBOL = '_and_'
REMOVE_SYMBOL = '_not_'

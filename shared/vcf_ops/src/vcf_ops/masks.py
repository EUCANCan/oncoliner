# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
from variant_extractor.variants import VariantType


def snv_mask(df):
    return df['type_inferred'] == VariantType.SNV.name


def indel_mask(df, indel_threshold):
    return (df['length'] > 0) & (df['length'] <= indel_threshold) & (df['alt'] != '<INS>') & \
        (df['type_inferred'] != VariantType.SNV.name) & \
        (df['type_inferred'] != VariantType.INV.name) & (df['type_inferred'] != VariantType.TRA.name)

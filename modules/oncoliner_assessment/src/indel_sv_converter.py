import pandas as pd
import pysam

from variant_extractor.variants import VariantType


SV_REGEX = r'[\[\]<>.]'

def _get_chrom_preffix(fasta: pysam.FastaFile):
    # Fix chr1 vs 1
    chrom_preffix = ''
    if fasta.references[0].startswith('chr'):
        chrom_preffix = 'chr'
    return chrom_preffix


def indel_to_sv(variants_df: pd.DataFrame, fasta_ref: str) -> pd.DataFrame:
    if len(variants_df) == 0:
        return variants_df

    fasta = pysam.FastaFile(fasta_ref)

    # Fix chr1 vs 1
    chrom_preffix = _get_chrom_preffix(fasta)

    # Check all chromosomes are in the reference
    for chrom in variants_df['start_chrom'].unique():
        if chrom_preffix + chrom not in fasta.references:
            raise ValueError(f'Chromosome {chrom} not in FASTA references {fasta.references}')

    def convert_row(row):
        # Only convert INS
        # Ignore INS with <INS> in the ALF field
        # Check if the INS is actually a DUP
        # Search if the ALT sequence is repeated in the reference
        if row['alt'] == fasta.fetch(chrom_preffix + row['start_chrom'], row['start'] - 1, row['start'] + row['length']):
            row['type_inferred'] = VariantType.DUP.name
            # Change to bracket notation offsetting 1 from start
            row['start'] += 1
            row['length'] -= 1
            row['end'] = row['start'] + row['length']
            row['ref'] = row['alt'][1]
            row['alt'] = f']{chrom_preffix+row["start_chrom"]}:{row["end"]}]{row["ref"]}'
            row['brackets'] = ']N'
        return row

    variants_mask = (variants_df['type_inferred'] == VariantType.INS.name) & \
        (variants_df['alt'] != '<INS>')
    return pd.concat([variants_df[~variants_mask], variants_df.loc[variants_mask, :].apply(convert_row, axis=1)], ignore_index=True)


def sv_to_indel(variants_df: pd.DataFrame, fasta_ref: str) -> pd.DataFrame:
    if len(variants_df) == 0:
        return

    fasta = pysam.FastaFile(fasta_ref)

    # Fix chr1 vs 1
    chrom_preffix = _get_chrom_preffix(fasta)

    # Check all chromosomes are in the reference
    for chrom in variants_df['start_chrom'].unique():
        if chrom_preffix + chrom not in fasta.references:
            raise ValueError(f'Chromosome {chrom} not in FASTA references {fasta.references}')

    def convert_row(row):
        if row['type_inferred'] == VariantType.DUP.name:
            row['start'] -= 1
            row['length'] += 1
            new_alt = fasta.fetch(chrom_preffix + row['start_chrom'], row['start'] - 1, row['start'] + row['length']).upper()
            row['end'] = row['start']
            row['alt'] = new_alt
            row['ref'] = new_alt[0]
        else:
            raise ValueError('Unknown variant type: ' + row['type_inferred'])
        return row

    variants_mask = (variants_df['type_inferred'] == VariantType.DUP.name) & \
        (variants_df['alt'].str.contains(SV_REGEX))
    # Return the updated dataframe
    return pd.concat([variants_df[~variants_mask], variants_df.loc[variants_mask, :].apply(convert_row, axis=1)], ignore_index=True)

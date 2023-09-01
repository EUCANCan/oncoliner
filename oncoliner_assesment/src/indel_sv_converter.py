import os
import sys
import pysam

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'vcf_ops', 'src'))

from vcf_ops import VariantType  # noqa


SV_REGEX = r'[\[\]<>.]'


def _variant_record_obj(row, chrom_preffix):
    original_obj = row['variant_record_obj']
    new_contig = chrom_preffix + original_obj.contig.replace('chr', '')
    new_obj = original_obj._replace(contig=new_contig, pos=row['start'], end=row['end'], ref=row['ref'], alt=row['alt'])
    return new_obj


def _get_chrom_preffix(fasta):
    # Fix chr1 vs 1
    chrom_preffix = ''
    if fasta.references[0].startswith('chr'):
        chrom_preffix = 'chr'
    return chrom_preffix


def convert_svs(variants_df, fasta_ref):
    if len(variants_df) == 0:
        return variants_df

    fasta = pysam.FastaFile(fasta_ref)

    # Fix chr1 vs 1
    chrom_preffix = _get_chrom_preffix(fasta)

    # Check all chromosomes are in the reference
    for chrom in variants_df['start_chrom'].unique():
        if chrom_preffix+chrom not in fasta.references:
            raise ValueError(f'Chromosome {chrom} not in FASTA references {fasta.references}')

    def convert_row(row):
        # Only convert INS
        # Ignore INS with <INS> in the ALF field
        # Check if the INS is actually a DUP
        # Search if the ALT sequence is repeated in the reference
        if row['alt'] == fasta.fetch(chrom_preffix+row['start_chrom'], row['start']-1, row['start']+row['length']):
            row['type_inferred'] = VariantType.DUP.name
            # Change to bracket notation offsetting 1 from start
            row['start'] += 1
            row['length'] -= 1
            row['end'] = row['start'] + row['length']
            row['ref'] = row['alt'][1]
            row['alt'] = f']{chrom_preffix+row["start_chrom"]}:{row["end"]}]{row["ref"]}'
            row['brackets'] = ']N'
            row['variant_record_obj'] = _variant_record_obj(row, chrom_preffix)
        return row

    variants_df.loc[
        (variants_df['type_inferred'] == VariantType.INS.name) &
        (variants_df['alt'] != '<INS>'), :].apply(convert_row, axis=1)
    return variants_df


def convert_indels(variants_df, fasta_ref):
    if len(variants_df) == 0:
        return variants_df

    fasta = pysam.FastaFile(fasta_ref)

    # Fix chr1 vs 1
    chrom_preffix = _get_chrom_preffix(fasta)

    # Check all chromosomes are in the reference
    for chrom in variants_df['start_chrom'].unique():
        if chrom_preffix+chrom not in fasta.references:
            raise ValueError(f'Chromosome {chrom} not in FASTA references {fasta.references}')

    def convert_row(row):
        if row['type_inferred'] == VariantType.DEL.name:
            new_ref = fasta.fetch(chrom_preffix+row['start_chrom'], row['start']-1, row['end']).upper()
            new_alt = new_ref[0]
            row['alt'] = new_alt
            row['ref'] = new_ref
            row['variant_record_obj'] = _variant_record_obj(row, chrom_preffix)
        elif row['type_inferred'] == VariantType.DUP.name:
            new_ref = fasta.fetch(chrom_preffix+row['start_chrom'], row['end']-1, row['end'])
            new_alt = new_ref + fasta.fetch(chrom_preffix+row['start_chrom'], row['start']-1, row['end']-1).upper()
            row['start'] = row['end']
            row['alt'] = new_alt
            row['ref'] = new_ref
            row['variant_record_obj'] = _variant_record_obj(row, chrom_preffix)
        else:
            raise ValueError('Unknown variant type: ' + row['type_inferred'])
        return row

    variants_df.loc[
        (variants_df['type_inferred'] != VariantType.INS.name) &
        (variants_df['type_inferred'] != VariantType.SNV.name) &
        (variants_df['alt'].str.contains(SV_REGEX)), :].apply(convert_row, axis=1)
    return variants_df

# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
from typing import List, Set, Sequence, Union
import os
import pandas as pd
from variant_extractor import VariantExtractor

from .i_o import extract_variants
from .constants import ONCOLINER_INFO_GENES_NAME

GENE_SPLIT_SYMBOL = ';'
# Lazy load
_PROTEIN_CODING_GENES = None
_CANCER_CENSUS_GENES = None


def combine_gene_annotations(df_tp: pd.DataFrame, df_truth: Union[pd.DataFrame, None] = None) -> Sequence[Sequence[str]]:
    genes = pd.Series([set() for _ in range(len(df_tp))], index=df_tp.index)
    # Check if the variant_record_obj is already gene annotated in the test file
    for vcf_file in df_tp['vcf_file'].unique():
        vcf_df = df_tp[df_tp['vcf_file'] == vcf_file]
        pass_only = df_tp[df_tp['vcf_file'] == vcf_file].iloc[0]['pass_only']
        variants_iterator = extract_variants(vcf_file, df_tp['idx_in_file'], pass_only=pass_only)
        for idx, variant_record in zip(vcf_df.index, variants_iterator):
            affected_genes = extract_protein_affected_genes(variant_record)
            genes[idx] = affected_genes
    if df_truth is None:
        return genes
    # Add gene annotations from the truth files if not present
    df_truth = df_truth.loc[df_tp['idx_truth']]
    # Check if the variant_record_obj is gene annotated in the truth file
    for vcf_file in df_truth['vcf_file'].unique():
        pass_only = df_truth[df_truth['vcf_file'] == vcf_file].iloc[0]['pass_only']
        truth_variant_extractor = VariantExtractor(vcf_file, pass_only=pass_only)
        truth_annotated = False
        for variant_record in truth_variant_extractor:
            # If annotated, use it
            if is_gene_annotated(variant_record):
                truth_annotated = True
                break
        truth_variant_extractor.close()
        if not truth_annotated:
            return genes
    # Add gene annotations to the test file
    truth_to_test_idx = {}
    for i, row in df_tp.iterrows():
        truth_to_test_idx[row['idx_truth']] = i
    for vcf_file in df_truth['vcf_file'].unique():
        truth_vcf_df = df_truth[df_truth['vcf_file'] == vcf_file]
        pass_only = df_truth[df_truth['vcf_file'] == vcf_file].iloc[0]['pass_only']
        variants_iterator = extract_variants(vcf_file, df_truth['idx_in_file'], pass_only=pass_only)
        for idx_truth, variant_record in zip(truth_vcf_df.index, variants_iterator):
            # Extract protein affected genes from the record
            truth_genes = extract_protein_affected_genes(variant_record)
            genes[truth_to_test_idx[idx_truth]] = genes[truth_to_test_idx[idx_truth]].union(truth_genes)
    return genes


def _read_genes_file(genes_tsv_file_path: str):
    df = pd.read_csv(genes_tsv_file_path, sep='\t')
    # Lowercase all columns
    df.columns = [col.lower() for col in df.columns]
    # Get all the genes in the "symbol" column
    return frozenset(df['symbol'].unique())


def _extract_annotations(variant_record_obj, annotation_field_name: str) -> List[str]:
    annotations = variant_record_obj.info[annotation_field_name]
    if annotations is None:
        return []
    elif isinstance(annotations, str):
        annotations = [annotations]
    return annotations


def get_cancer_census_genes():
    # Lazy load CANCER_CENSUS_GENES
    global _CANCER_CENSUS_GENES
    if _CANCER_CENSUS_GENES is None:
        _CANCER_CENSUS_GENES = _read_genes_file(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'genes_cancer.tsv'))
    return _CANCER_CENSUS_GENES


def _extract_protein_affected_genes_from_oncoliner(variant_record_obj) -> Set[str]:
    # Extract protein coding genes from ONCOLINER annotation
    return set(_extract_annotations(variant_record_obj, ONCOLINER_INFO_GENES_NAME))


def _extract_protein_affected_genes_from_funnsv(variant_record_obj) -> Set[str]:
    # Extract protein coding genes from funnSV annotation
    protein_affected_genes = set()
    for annotation in _extract_annotations(variant_record_obj, 'FUNNSV_ANNOTATIONS'):
        for ann in annotation.split('|'):
            if ann in _PROTEIN_CODING_GENES:
                protein_affected_genes.add(ann)
    return protein_affected_genes


def _extract_protein_affected_genes_from_vep(variant_record_obj) -> Set[str]:
    # Extract protein coding genes from VEP annotation
    protein_affected_consequences = set(['stop_gained', 'frameshift_variant', 'stop_lost', 'start_lost', 'inframe_insertion',
                                        'inframe_deletion', 'missense_variant', 'protein_altering_variant', 'coding_sequence_variant', 'coding_transcript_variant'])
    protein_affected_genes = set()
    for vep_annotation in _extract_annotations(variant_record_obj, 'CSQ'):
        # Find an annotation with a protein affecting consequence
        found = False
        for ann in vep_annotation.split('|'):
            if len(set(ann.split('&')).intersection(protein_affected_consequences)) > 0:
                found = True
                break
        if not found:
            continue
        # Extract the gene symbol
        for ann in vep_annotation.split('|'):
            if ann in _PROTEIN_CODING_GENES:
                protein_affected_genes.add(ann)
    return protein_affected_genes


def extract_protein_affected_genes(variant_record_obj) -> Set[str]:
    # Load PROTEIN_CODING_GENES
    global _PROTEIN_CODING_GENES
    if _PROTEIN_CODING_GENES is None:
        _PROTEIN_CODING_GENES = _read_genes_file(os.path.join(os.path.dirname(
            __file__), '..', '..', 'data', 'genes_with_protein_product.tsv'))
    # Check for ONCOLINER annotation
    if _is_gene_annotated_in_oncoliner(variant_record_obj):
        return _extract_protein_affected_genes_from_oncoliner(variant_record_obj)
    # Check for VEP annotation
    if _is_gene_annotated_in_vep(variant_record_obj):
        return _extract_protein_affected_genes_from_vep(variant_record_obj)
    # Check for funnSV annotation
    if _is_gene_annotated_in_funnsv(variant_record_obj):
        return _extract_protein_affected_genes_from_funnsv(variant_record_obj)
    return set()


def combine_genes_symbols(genes_symbols_lists: pd.Series) -> Set[str]:
    genes_symbols = set()
    for genes_symbols_list in genes_symbols_lists:
        genes_symbols = genes_symbols.union(set(genes_symbols_list))
    return genes_symbols


def _is_gene_annotated_in_vep(variant_record_obj) -> bool:
    return 'CSQ' in variant_record_obj.info


def _is_gene_annotated_in_funnsv(variant_record_obj) -> bool:
    return 'FUNNSV_ANNOTATIONS' in variant_record_obj.info


def _is_gene_annotated_in_oncoliner(variant_record_obj) -> bool:
    return ONCOLINER_INFO_GENES_NAME in variant_record_obj.info


def is_gene_annotated(variant_record_obj) -> bool:
    return _is_gene_annotated_in_oncoliner(variant_record_obj) or _is_gene_annotated_in_vep(variant_record_obj) or _is_gene_annotated_in_funnsv(variant_record_obj)

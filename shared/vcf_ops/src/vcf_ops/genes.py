# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
from typing import List, Set
import os
import pandas as pd

GENE_SPLIT_SYMBOL = ';'
ONCOLINER_INFO_FIELD_NAME = 'ONCOLINER_PROT_GENES'
# Lazy load
_PROTEIN_CODING_GENES = None
_CANCER_CENSUS_GENES = None
_ACTIONABLE_GENES = None


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

def get_actionable_genes():
    # Lazy load ACTIONABLE_GENES
    global _ACTIONABLE_GENES
    if _ACTIONABLE_GENES is None:
        _ACTIONABLE_GENES = _read_genes_file(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'genes_actionable.tsv'))
    return _ACTIONABLE_GENES

def _extract_protein_affected_genes_from_oncoliner(variant_record_obj) -> Set[str]:
    # Extract protein coding genes from ONCOLINER annotation
    return set(_extract_annotations(variant_record_obj, ONCOLINER_INFO_FIELD_NAME))

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
    for vep_annotation in  _extract_annotations(variant_record_obj, 'CSQ'):
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


def combine_genes_symbols(genes_symbols_sets: pd.Series) -> Set[str]:
    genes_symbols = set()
    for genes_symbols_set in genes_symbols_sets:
        genes_symbols = genes_symbols.union(genes_symbols_set)
    return genes_symbols


def add_gene_annotation_to_variant_record(variant_record_obj, genes_symbols: Set[str]):
    if len(genes_symbols) == 0:
        return
    variant_record_obj.info[ONCOLINER_INFO_FIELD_NAME] = list(genes_symbols)


def _is_gene_annotated_in_vep(variant_record_obj) -> bool:
    return 'CSQ' in variant_record_obj.info

def _is_gene_annotated_in_funnsv(variant_record_obj) -> bool:
    return 'FUNNSV_ANNOTATIONS' in variant_record_obj.info


def _is_gene_annotated_in_oncoliner(variant_record_obj) -> bool:
    return ONCOLINER_INFO_FIELD_NAME in variant_record_obj.info


def is_gene_annotated(variant_record_obj) -> bool:
    return _is_gene_annotated_in_oncoliner(variant_record_obj) or _is_gene_annotated_in_vep(variant_record_obj) or _is_gene_annotated_in_funnsv(variant_record_obj)

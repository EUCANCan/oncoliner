from typing import List, Tuple
import sys
import os

import pandas as pd
import numpy as np

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', '..', 'shared', 'vcf_ops', 'src'))
from vcf_ops.genes import GENE_SPLIT_SYMBOL  # noqa

def compute_phs(metrics: List[Tuple[float, float]]) -> float:
    # Compute the centroid
    centroid = np.mean(metrics, axis=0)
    # Compute the distance from the centroid to each point
    distances = []
    for point in metrics:
        distances.append(np.linalg.norm(point - centroid))
    # Compute the phs
    phs = np.mean(distances) / (np.sqrt(2) / 2)
    return phs


def compute_gdr(genes_list: List[str]) -> float:
    intersect_genes = None
    union_genes = None
    for genes in genes_list:
        if type(genes) == float:
            continue
        curr_genes = set(genes.split(GENE_SPLIT_SYMBOL))
        if intersect_genes is None:
            intersect_genes = curr_genes
            union_genes = curr_genes
            continue
        intersect_genes = intersect_genes.intersection(curr_genes)
        union_genes = union_genes.union(curr_genes)
    if union_genes is None or len(union_genes) == 0:
        return 0
    return 1 - (len(intersect_genes) / len(union_genes))

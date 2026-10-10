#!/usr/bin/env bash
set -euo pipefail

source ~/miniconda3/etc/profile.d/conda.sh
conda activate phylogeny

for tool in mafft iqtree astral; do
  command -v "$tool" >/dev/null || { echo "Missing $tool"; exit 1; }
done

PILOT_ONLY="${PILOT_ONLY:-1}"

mkdir -p pilot_output/alignments pilot_output/trees
mkdir -p pipeline_output/alignments pipeline_output/trees
mkdir -p reports/stage01

if [ "$PILOT_ONLY" = "1" ]; then
  echo "=== PILOT TEST (5 files) ==="
  files=(input_genes/*.fasta)
  for f in "${files[@]:0:5}"; do
    [ -e "$f" ] || continue
    base=$(basename "$f" .fasta)
    echo "PILOT aligning $base"
    mafft --auto "$f" > "pilot_output/alignments/${base}_aligned.fasta" 2>> reports/stage01/pilot_mafft.log
    iqtree -s "pilot_output/alignments/${base}_aligned.fasta" -m MFP -bb 1000 -nt 2 -mem 3000 -pre "pilot_output/trees/${base}" >> reports/stage01/pilot_iqtree.log 2>&1
  done
  cat pilot_output/trees/*.treefile > pilot_output/all_gene_trees.tre
  astral -i pilot_output/all_gene_trees.tre -o pilot_output/species_tree.newick -t 2 >> reports/stage01/pilot_astral.log 2>&1
  echo "Pilot done: pilot_output/species_tree.newick"
  echo "If OK, run: PILOT_ONLY=0 bash run_pipeline.sh"
  exit 0
fi

echo "=== FULL PIPELINE ==="
for f in input_genes/*.fasta; do
  [ -e "$f" ] || continue
  base=$(basename "$f" .fasta)
  echo "Aligning $base"
  mafft --auto "$f" > "pipeline_output/alignments/${base}_aligned.fasta" 2>> reports/stage01/mafft_align.log
done

for f in pipeline_output/alignments/*_aligned.fasta; do
  [ -e "$f" ] || continue
  base=$(basename "$f" _aligned.fasta)
  echo "Building tree for $base"
  iqtree -s "$f" -m MFP -bb 1000 -nt 2 -mem 3000 -pre "pipeline_output/trees/${base}" >> reports/stage01/iqtree_progress.log 2>&1
done

cat pipeline_output/trees/*.treefile > pipeline_output/all_gene_trees.tre
astral -i pipeline_output/all_gene_trees.tre -o species_tree.newick -t 2 > reports/stage01/astral_run.log 2>&1

[ -s species_tree.newick ] || { echo "species_tree.newick missing or empty"; exit 1; }
echo "First 20 lines:"
head -n 20 species_tree.newick